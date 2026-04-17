from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from monitor.health import get_last_run, is_healthy

router = APIRouter()
_NANO_BANAA_PLUGIN_PATH = (
    Path(__file__).resolve().parents[3] / "cowork-skill" / "anthropic-monitor-skill.zip"
)


@router.get("/health")
async def health() -> dict:
    last_run = get_last_run()
    return {
        "status": "healthy" if is_healthy() else "degraded",
        "last_run": last_run.isoformat() if last_run else None,
        "nano_banaa_plugin": {
            "status": "available" if _NANO_BANAA_PLUGIN_PATH.exists() else "missing"
        },
    }
