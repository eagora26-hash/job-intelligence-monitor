"""Per-source health metrics used by the observability/health dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceHealth(BaseModel):
    """Rolling health for a single scraper source.

    Updated on every scrape attempt by the runner so the dashboard can show which sources
    are healthy, failing, or slow.
    """

    source: str
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_error: str = ""
    avg_response_ms: float = 0.0
    last_jobs_found: int = 0

    @property
    def total_runs(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """Success ratio in ``[0, 1]``; ``1.0`` when there are no runs yet."""
        return 1.0 if self.total_runs == 0 else self.success_count / self.total_runs

    @property
    def status(self) -> str:
        """Human-friendly status label for the dashboard."""
        if self.total_runs == 0:
            return "unknown"
        if self.success_rate >= 0.8:
            return "healthy"
        if self.success_rate >= 0.4:
            return "degraded"
        return "failing"

    def record_success(self, *, jobs_found: int, response_ms: float) -> None:
        """Fold a successful run into the rolling metrics (incremental mean for latency)."""
        from datetime import datetime as _dt, timezone as _tz

        self.success_count += 1
        self.last_success = _dt.now(_tz.utc)
        self.last_jobs_found = jobs_found
        self.last_error = ""
        # Incremental average over successful runs only.
        n = self.success_count
        self.avg_response_ms = ((self.avg_response_ms * (n - 1)) + response_ms) / n

    def record_failure(self, *, error: str) -> None:
        from datetime import datetime as _dt, timezone as _tz

        self.failure_count += 1
        self.last_failure = _dt.now(_tz.utc)
        self.last_error = error[:500]
