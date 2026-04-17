from __future__ import annotations

from datetime import datetime, timezone

import httpx
import structlog
from bs4 import BeautifulSoup

from monitor.models import Post

log = structlog.get_logger()

_HEADERS = {
    "User-Agent": "anthropic-monitor/0.1 (enterprise blog watcher; contact admin@yourcompany.com)"
}


async def fetch_posts(feed_url: str, source_name: str) -> list[Post]:
    async with httpx.AsyncClient(headers=_HEADERS, timeout=30) as client:
        response = await client.get(feed_url)
        response.raise_for_status()

    posts = _parse(response.text, feed_url, source_name)
    log.info("fetched_feed", source=source_name, url=feed_url, count=len(posts))
    return posts


def _parse(html: str, base_url: str, source_name: str) -> list[Post]:
    soup = BeautifulSoup(html, "lxml")
    posts: list[Post] = []

    for anchor in soup.select("a[href]"):
        href: str = anchor["href"]  # type: ignore[assignment]
        title = anchor.get_text(strip=True)

        if not title or not _is_post_link(href, base_url):
            continue

        full_url = href if href.startswith("http") else f"https://www.anthropic.com{href}"
        posts.append(
            Post(
                url=full_url,
                title=title,
                source_name=source_name,
                discovered_at=datetime.now(timezone.utc),
            )
        )

    # Deduplicate by URL while preserving order
    seen: set[str] = set()
    unique: list[Post] = []
    for post in posts:
        if post.url not in seen:
            seen.add(post.url)
            unique.append(post)

    return unique


def _is_post_link(href: str, base_url: str) -> bool:
    """Return True only for links that look like individual post pages."""
    if not href:
        return False
    # Must be a relative path with depth or an absolute URL under anthropic.com
    if href.startswith("/news/") or href.startswith("/research/"):
        return True
    if "anthropic.com/news/" in href or "anthropic.com/research/" in href:
        return True
    return False
