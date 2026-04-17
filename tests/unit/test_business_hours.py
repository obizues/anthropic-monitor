from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from monitor.business_hours import is_business_hours

_ET = ZoneInfo("America/New_York")


def _dt(weekday: int, hour: int, minute: int = 0) -> datetime:
    """weekday: 0=Mon, 5=Sat, 6=Sun"""
    from datetime import date, timedelta
    base = date(2025, 1, 6)  # Known Monday
    day = base + timedelta(days=weekday)
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=_ET)


def test_within_business_hours():
    assert is_business_hours(_dt(0, 10)) is True  # Monday 10am


def test_before_start():
    assert is_business_hours(_dt(0, 8, 59)) is False  # Monday 8:59am


def test_at_end():
    assert is_business_hours(_dt(0, 17, 0)) is False  # Monday 5:00pm exactly


def test_saturday():
    assert is_business_hours(_dt(5, 10)) is False


def test_sunday():
    assert is_business_hours(_dt(6, 14)) is False


def test_friday_afternoon():
    assert is_business_hours(_dt(4, 16, 30)) is True  # Friday 4:30pm
