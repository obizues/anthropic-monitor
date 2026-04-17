from __future__ import annotations

import httpx
import structlog

from config.loader import get_secrets
from monitor.models import Post
from notifiers.base import BaseNotifier

log = structlog.get_logger()


class SlackNotifier(BaseNotifier):
    async def send(self, posts: list[Post]) -> None:
        for post in posts:
            await self._post_block(post)

    async def send_digest(self, posts: list[Post], label: str = "Weekend Roundup") -> None:
        blocks: list[dict] = [
            {"type": "header", "text": {"type": "plain_text", "text": f"Anthropic {label}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "Here's what dropped outside business hours:"}},
            {"type": "divider"},
        ]
        for post in posts:
            blocks.extend(_post_blocks(post))
            blocks.append({"type": "divider"})
        await self._send_payload({"blocks": blocks})

    async def _post_block(self, post: Post) -> None:
        blocks: list[dict] = [{"type": "divider"}] + _post_blocks(post)
        await self._send_payload({"blocks": blocks})

    async def _send_payload(self, payload: dict) -> None:
        webhook_url = get_secrets().slack_webhook_url
        if not webhook_url:
            log.warning("slack_webhook_not_configured")
            return
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code != 200:
                log.error("slack_send_failed", status=response.status_code, body=response.text)
            else:
                log.info("slack_sent", post_count=1)


def _post_blocks(post: Post) -> list[dict]:
    text = f"*<{post.url}|{post.title}>*\n_{post.source_name}_"
    if post.summary:
        text += f"\n\n{post.summary}"
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]
