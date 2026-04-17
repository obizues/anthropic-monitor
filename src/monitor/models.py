from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, HttpUrl


class Post(BaseModel):
    url: str
    title: str
    source_name: str
    discovered_at: datetime
    summary: str | None = None
