from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import structlog

from config.loader import get_config, get_secrets

log = structlog.get_logger()

_HEALTH_PATH = Path("state/health.json")


def record_heartbeat() -> None:
    _HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    _HEALTH_PATH.write_text(
        json.dumps({"last_run": datetime.now(timezone.utc).isoformat()}, indent=2)
    )


def is_healthy() -> bool:
    if not _HEALTH_PATH.exists():
        return False
    try:
        data = json.loads(_HEALTH_PATH.read_text())
        last_run = datetime.fromisoformat(data["last_run"])
        max_silence = timedelta(hours=get_config().health.max_silence_hours)
        return datetime.now(timezone.utc) - last_run < max_silence
    except (KeyError, ValueError):
        return False


def get_last_run() -> datetime | None:
    if not _HEALTH_PATH.exists():
        return None
    try:
        data = json.loads(_HEALTH_PATH.read_text())
        return datetime.fromisoformat(data["last_run"])
    except (KeyError, ValueError):
        return None


async def alert_if_unhealthy() -> None:
    if is_healthy():
        return
    cfg = get_config().health
    if not cfg.admin_alert_on_failure:
        return
    admin_email = get_secrets().admin_email
    if not admin_email:
        log.error("health_check_failed_no_admin_email")
        return
    log.error("health_alert_sent", admin=admin_email)
    # Import here to avoid circular dependency
    from notifiers.email import EmailNotifier
    from monitor.models import Post
    from datetime import timezone
    alert_post = Post(
        url="",
        title="ALERT: Anthropic Monitor has stopped running",
        source_name="Self-Monitor",
        discovered_at=datetime.now(timezone.utc),
        summary=f"No successful run detected within the last {cfg.max_silence_hours} hours. Please check the scheduler.",
    )
    notifier = EmailNotifier()
    # Send directly to admin bypassing subscriber list
    await notifier._send_to(
        admin_email,
        [alert_post],
        template="""<html><body><h2>Monitor Alert</h2><p>{{ posts[0].title }}</p><p>{{ posts[0].summary }}</p></body></html>""",
        subject="ALERT: Anthropic Monitor is down",
    )
