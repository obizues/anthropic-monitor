from __future__ import annotations

import json
from pathlib import Path

import structlog

from monitor.models import Post

log = structlog.get_logger()

_STATE_PATH = Path("state/seen_posts.json")


def find_new_posts(candidates: list[Post]) -> list[Post]:
    seen = _load_seen()
    seen_in_batch: set[str] = set()
    new: list[Post] = []
    for post in candidates:
        if post.url in seen or post.url in seen_in_batch:
            continue
        seen_in_batch.add(post.url)
        new.append(post)
    if new:
        _save_seen(seen | {p.url for p in new})
        log.info("new_posts_detected", count=len(new), urls=[p.url for p in new])
    return new


def _load_seen() -> set[str]:
    if not _STATE_PATH.exists():
        return set()
    try:
        return set(json.loads(_STATE_PATH.read_text()))
    except (json.JSONDecodeError, ValueError):
        log.warning("corrupt_state_file", path=str(_STATE_PATH))
        return set()


def _save_seen(urls: set[str]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(sorted(urls), indent=2))
