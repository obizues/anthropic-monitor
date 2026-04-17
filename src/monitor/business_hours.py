from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from config.loader import get_config
from config.schema import BusinessHoursConfig


def is_business_hours(now: datetime | None = None) -> bool:
    cfg = get_config().schedule.business_hours
    if not cfg.enabled:
        return True

    tz = ZoneInfo(cfg.timezone)
    local = (now or datetime.now(tz)).astimezone(tz)

    if cfg.weekdays_only and local.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    start_h, start_m = map(int, cfg.start.split(":"))
    end_h, end_m = map(int, cfg.end.split(":"))
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    current_minutes = local.hour * 60 + local.minute

    return start_minutes <= current_minutes < end_minutes
