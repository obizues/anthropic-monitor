from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter

from monitor.health import get_last_run, is_healthy

router = APIRouter()
_DEFAULT_ANTHROPIC_MONITOR_SKILL_PATH = Path("cowork-skill/anthropic-monitor-skill.zip")


def _nano_banaa_plugin_status() -> str:
    plugin_path = Path(
        os.getenv("NANO_BANAA_PLUGIN_PATH", str(_DEFAULT_ANTHROPIC_MONITOR_SKILL_PATH))
    )
    return "available" if plugin_path.exists() else "missing"


@router.get("/health")
async def health() -> dict:
    last_run = get_last_run()
    return {
        "status": "healthy" if is_healthy() else "degraded",
        "last_run": last_run.isoformat() if last_run else None,
        "nano_banaa_plugin": {"status": _nano_banaa_plugin_status()},
    }
