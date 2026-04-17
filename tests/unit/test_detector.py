from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from monitor.detector import find_new_posts
from monitor.models import Post


def _make_post(url: str) -> Post:
    return Post(url=url, title="Test", source_name="Test", discovered_at=datetime.now(timezone.utc))


def test_all_new_when_state_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("monitor.detector._STATE_PATH", tmp_path / "seen.json")
    posts = [_make_post("https://anthropic.com/news/a"), _make_post("https://anthropic.com/news/b")]
    result = find_new_posts(posts)
    assert len(result) == 2


def test_known_posts_filtered(tmp_path, monkeypatch):
    state_path = tmp_path / "seen.json"
    state_path.write_text(json.dumps(["https://anthropic.com/news/a"]))
    monkeypatch.setattr("monitor.detector._STATE_PATH", state_path)
    posts = [_make_post("https://anthropic.com/news/a"), _make_post("https://anthropic.com/news/b")]
    result = find_new_posts(posts)
    assert len(result) == 1
    assert result[0].url == "https://anthropic.com/news/b"


def test_state_persisted_after_detection(tmp_path, monkeypatch):
    state_path = tmp_path / "seen.json"
    monkeypatch.setattr("monitor.detector._STATE_PATH", state_path)
    find_new_posts([_make_post("https://anthropic.com/news/a")])
    saved = json.loads(state_path.read_text())
    assert "https://anthropic.com/news/a" in saved


def test_idempotent_double_run(tmp_path, monkeypatch):
    state_path = tmp_path / "seen.json"
    monkeypatch.setattr("monitor.detector._STATE_PATH", state_path)
    posts = [_make_post("https://anthropic.com/news/a")]
    first = find_new_posts(posts)
    second = find_new_posts(posts)
    assert len(first) == 1
    assert len(second) == 0
