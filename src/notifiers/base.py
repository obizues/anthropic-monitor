from __future__ import annotations

from abc import ABC, abstractmethod

from monitor.models import Post


class BaseNotifier(ABC):
    """All notification adapters implement this interface."""

    @abstractmethod
    async def send(self, posts: list[Post]) -> None: ...

    @abstractmethod
    async def send_digest(self, posts: list[Post], label: str = "Weekend Roundup") -> None: ...
