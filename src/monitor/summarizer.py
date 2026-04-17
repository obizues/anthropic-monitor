from __future__ import annotations

import anthropic
import httpx
import structlog
from bs4 import BeautifulSoup

from config.loader import get_config, get_secrets
from monitor.models import Post

log = structlog.get_logger()

_HEADERS = {
    "User-Agent": "anthropic-monitor/0.1 (enterprise blog watcher; contact admin@yourcompany.com)"
}

_SYSTEM_PROMPT = (
    "You are a technical intelligence analyst summarizing AI research and product announcements "
    "for an enterprise software team. Be concise, accurate, and highlight what matters for practitioners."
)


async def enrich_with_summary(post: Post) -> Post:
    cfg = get_config().summaries
    if not cfg.enabled:
        return post

    content = await _fetch_post_content(post.url)
    if not content:
        return post

    summary = await _summarize(content, cfg.model, cfg.max_sentences)
    return post.model_copy(update={"summary": summary})


async def _fetch_post_content(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        # Strip nav, footer, scripts — keep main article text
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:8000]  # Token budget
    except Exception:
        log.warning("failed_to_fetch_post_content", url=url)
        return None


async def _summarize(content: str, model: str, max_sentences: int) -> str | None:
    try:
        client = anthropic.Anthropic(api_key=get_secrets().anthropic_api_key)
        message = client.messages.create(
            model=model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Summarize the following article in exactly {max_sentences} sentences. "
                        f"Focus on: what was announced, why it matters, and any key technical details.\n\n"
                        f"{content}"
                    ),
                }
            ],
        )
        return message.content[0].text.strip()
    except Exception:
        log.warning("summarization_failed", model=model)
        return None
