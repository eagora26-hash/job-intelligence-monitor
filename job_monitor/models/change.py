"""Change-detection records: an audit trail of how a posting evolved over time."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobChange(BaseModel):
    """A single detected change to a previously-seen job (one row per changed field)."""

    job_url: str
    field: str
    old_value: str = ""
    new_value: str = ""
    detected_at: datetime = Field(default_factory=_utcnow)
