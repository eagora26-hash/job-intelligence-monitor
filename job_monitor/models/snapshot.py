"""Daily aggregate snapshots for historical/trend analytics."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DailySnapshot(BaseModel):
    """A once-per-day rollup of headline metrics, enabling historical trend charts."""

    snapshot_date: date
    total_jobs: int = 0
    new_jobs: int = 0
    source_count: int = 0
    keyword_count: int = 0
    notified_count: int = 0
    avg_score: float = 0.0
