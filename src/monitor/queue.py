from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import structlog

from monitor.models import Post

log = structlog.get_logger()

_QUEUE_PATH = Path("queue/pending.json")


def enqueue(posts: list[Post]) -> None:
    existing = _load()
    existing.extend(posts)
    _save(existing)
    log.info("posts_queued", count=len(posts))


def drain() -> list[Post]:
    posts = _load()
    if posts:
        _save([])
        log.info("queue_drained", count=len(posts))
    return posts


def _load() -> list[Post]:
    if not _QUEUE_PATH.exists():
        return []
    try:
        raw = json.loads(_QUEUE_PATH.read_text())
        return [Post.model_validate(item) for item in raw]
    except (json.JSONDecodeError, ValueError):
        log.warning("corrupt_queue_file", path=str(_QUEUE_PATH))
        return []


def _save(posts: list[Post]) -> None:
    _QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _QUEUE_PATH.write_text(json.dumps([p.model_dump(mode="json") for p in posts], indent=2))
