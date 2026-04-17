from __future__ import annotations

from pathlib import Path

import aiosqlite
import structlog

log = structlog.get_logger()

_DB_PATH = Path("state/subscribers.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS subscribers (
    email    TEXT PRIMARY KEY,
    name     TEXT,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


async def _ensure_table(db: aiosqlite.Connection) -> None:
    await db.execute(_CREATE_TABLE)
    await db.commit()


async def add_subscriber(email: str, name: str = "") -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await _ensure_table(db)
        await db.execute(
            "INSERT OR IGNORE INTO subscribers (email, name) VALUES (?, ?)",
            (email.lower().strip(), name.strip()),
        )
        await db.commit()
    log.info("subscriber_added", email=email)


async def remove_subscriber(email: str) -> bool:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await _ensure_table(db)
        cursor = await db.execute(
            "DELETE FROM subscribers WHERE email = ?", (email.lower().strip(),)
        )
        await db.commit()
        removed = cursor.rowcount > 0
    log.info("subscriber_removed", email=email, found=removed)
    return removed


async def list_subscribers() -> list[dict[str, str]]:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await _ensure_table(db)
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT email, name, added_at FROM subscribers ORDER BY added_at"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def subscriber_exists(email: str) -> bool:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await _ensure_table(db)
        cursor = await db.execute(
            "SELECT 1 FROM subscribers WHERE email = ?", (email.lower().strip(),)
        )
        return await cursor.fetchone() is not None
