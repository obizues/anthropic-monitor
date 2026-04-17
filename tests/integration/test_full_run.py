from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from monitor.models import Post


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr("monitor.detector._STATE_PATH", tmp_path / "seen.json")
    monkeypatch.setattr("monitor.queue._QUEUE_PATH", tmp_path / "queue.json")
    monkeypatch.setattr("monitor.health._HEALTH_PATH", tmp_path / "health.json")
    return tmp_path


@pytest.mark.asyncio
async def test_new_posts_trigger_notifications(isolated_state, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "a" * 32)
    monkeypatch.setenv("CONFIG_API_KEY", "test")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")

    fake_post = Post(
        url="https://anthropic.com/news/test-post",
        title="Test Post",
        source_name="Anthropic News",
        discovered_at=datetime.now(timezone.utc),
    )

    slack_send = AsyncMock()
    email_send = AsyncMock()

    with (
        patch("monitor.scheduler.fetch_posts", AsyncMock(return_value=[fake_post])),
        patch("monitor.scheduler.enrich_with_summary", AsyncMock(side_effect=lambda p: p)),
        patch("monitor.scheduler.SlackNotifier.send", slack_send),
        patch("monitor.scheduler.EmailNotifier.send", email_send),
        patch("monitor.scheduler.is_business_hours", return_value=True),
    ):
        from monitor.scheduler import run_once
        await run_once()

    slack_send.assert_called_once()
    email_send.assert_called_once()


@pytest.mark.asyncio
async def test_outside_business_hours_queues_email(isolated_state, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "a" * 32)
    monkeypatch.setenv("CONFIG_API_KEY", "test")

    fake_post = Post(
        url="https://anthropic.com/news/weekend-post",
        title="Weekend Post",
        source_name="Anthropic News",
        discovered_at=datetime.now(timezone.utc),
    )

    email_send = AsyncMock()

    with (
        patch("monitor.scheduler.fetch_posts", AsyncMock(return_value=[fake_post])),
        patch("monitor.scheduler.enrich_with_summary", AsyncMock(side_effect=lambda p: p)),
        patch("monitor.scheduler.SlackNotifier.send", AsyncMock()),
        patch("monitor.scheduler.EmailNotifier.send", email_send),
        patch("monitor.scheduler.is_business_hours", return_value=False),
    ):
        from monitor.scheduler import run_once
        await run_once()

    email_send.assert_not_called()
    queued = json.loads((isolated_state / "queue.json").read_text())
    assert len(queued) == 1
