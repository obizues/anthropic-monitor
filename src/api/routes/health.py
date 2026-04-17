from __future__ import annotations

from fastapi import APIRouter

from monitor.health import get_last_run, is_healthy

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    last_run = get_last_run()
    return {
        "status": "healthy" if is_healthy() else "degraded",
        "last_run": last_run.isoformat() if last_run else None,
    }
