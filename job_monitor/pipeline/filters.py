"""Configuration-driven job filtering (include/exclude/source/date/remote/score).

Used by the runner to decide which enriched jobs are worth storing, and by the dashboard for
ad-hoc querying. All criteria are optional and combine with AND semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence

from job_monitor.models import JobRecord


@dataclass
class FilterConfig:
    """Declarative filter criteria. Empty/None fields are ignored."""

    include_keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    sources: Optional[List[str]] = None
    min_score: int = 0
    min_quality: int = 0
    remote_only: bool = False
    since: Optional[datetime] = None

    def normalized(self) -> "FilterConfig":
        """Return a copy with keyword lists lowercased (for case-insensitive matching)."""
        return FilterConfig(
            include_keywords=[k.lower() for k in self.include_keywords],
            exclude_keywords=[k.lower() for k in self.exclude_keywords],
            sources=self.sources,
            min_score=self.min_score,
            min_quality=self.min_quality,
            remote_only=self.remote_only,
            since=self.since,
        )


class JobFilter:
    """Applies a :class:`FilterConfig` to jobs."""

    def __init__(self, config: Optional[FilterConfig] = None) -> None:
        self.config = (config or FilterConfig()).normalized()

    def accepts(self, job: JobRecord) -> bool:
        cfg = self.config
        text = job.searchable_text

        if cfg.exclude_keywords and any(kw in text for kw in cfg.exclude_keywords):
            return False
        if cfg.include_keywords and not any(kw in text for kw in cfg.include_keywords):
            return False
        if cfg.sources is not None and job.source not in cfg.sources:
            return False
        if job.score < cfg.min_score:
            return False
        if job.quality_score < cfg.min_quality:
            return False
        if cfg.remote_only and not job.remote:
            return False
        if cfg.since is not None:
            stamp = job.posted_at or job.first_seen or job.scraped_at
            if stamp is not None and stamp < cfg.since:
                return False
        return True

    def apply(self, jobs: Sequence[JobRecord]) -> List[JobRecord]:
        return [job for job in jobs if self.accepts(job)]
