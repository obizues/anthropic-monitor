from __future__ import annotations

import httpx
import structlog

from monitor.models import Post
from notifiers.base import BaseNotifier

log = structlog.get_logger()


class WebhookNotifier(BaseNotifier):
    """Generic HTTP POST notifier. Configure target_url to integrate any destination."""

    def __init__(self, target_url: str) -> None:
        self._target_url = target_url

    async def send(self, posts: list[Post]) -> None:
        payload = {"event": "new_posts", "posts": [p.model_dump(mode="json") for p in posts]}
        await self._post(payload)

    async def send_digest(self, posts: list[Post], label: str = "Weekend Roundup") -> None:
        payload = {
            "event": "digest",
            "label": label,
            "posts": [p.model_dump(mode="json") for p in posts],
        }
        await self._post(payload)

    async def _post(self, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self._target_url, json=payload)
            if response.status_code not in range(200, 300):
                log.error("webhook_failed", url=self._target_url, status=response.status_code)
            else:
                log.info("webhook_sent", url=self._target_url)
