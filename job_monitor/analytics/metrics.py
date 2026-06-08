"""Analytics service: derives headline metrics, distributions, and trends from the database.

A thin read-only service over the repositories. The dashboard and the Telegram daily summary
both consume it, so the "numbers" are computed in exactly one place.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from job_monitor.database import (
    Database,
    HealthRepository,
    JobRepository,
    SnapshotRepository,
)
from job_monitor.models import DailySnapshot, JobRecord, SourceHealth


class AnalyticsService:
    """Computes metrics for the dashboard and notifications."""

    def __init__(self, database: Database) -> None:
        self.jobs = JobRepository(database)
        self.health_repo = HealthRepository(database)
        self.snapshot_repo = SnapshotRepository(database)

    # ----------------------------------------------------------------- headline
    def overview(self) -> Dict[str, object]:
        """Top-line KPIs for the overview page + daily summary."""
        all_jobs = self.jobs.all_jobs()
        avg_quality = (
            sum(j.quality_score for j in all_jobs) / len(all_jobs) if all_jobs else 0.0
        )
        return {
            "total_jobs": self.jobs.count(),
            "jobs_today": self.jobs.count_today(),
            "source_count": len(self.jobs.distinct_sources()),
            "category_count": len(self.jobs.distinct_categories()),
            "skill_count": len(self.jobs.distinct_skills()),
            "notified_count": self.jobs.notified_count(),
            "avg_score": round(self.jobs.avg_score(), 1),
            "avg_quality": round(avg_quality, 1),
            "remote_count": sum(1 for j in all_jobs if j.remote),
        }

    # ----------------------------------------------------------------- distributions
    def by_source(self) -> Dict[str, int]:
        return self.jobs.count_by_source()

    def by_category(self) -> Dict[str, int]:
        return self.jobs.count_by_category()

    def jobs_per_day(self, days: int = 30) -> Dict[str, int]:
        return self.jobs.count_by_day(days=days)

    def skill_frequency(self, top: int = 15) -> List[Tuple[str, int]]:
        counter: Counter[str] = Counter()
        for job in self.jobs.all_jobs():
            counter.update(job.skills)
        return counter.most_common(top)

    def tag_frequency(self, top: int = 15) -> List[Tuple[str, int]]:
        counter: Counter[str] = Counter()
        for job in self.jobs.all_jobs():
            counter.update(t.lower() for t in job.tags)
        return counter.most_common(top)

    def score_distribution(self, buckets: int = 5) -> Dict[str, int]:
        """Bucket jobs by score band for a histogram."""
        bands = {f"{i*10}-{i*10+9}": 0 for i in range(buckets)}
        bands[f"{buckets*10}+"] = 0
        for job in self.jobs.all_jobs():
            idx = min(job.score // 10, buckets)
            key = f"{buckets*10}+" if idx == buckets else f"{idx*10}-{idx*10+9}"
            bands[key] += 1
        return bands

    # ----------------------------------------------------------------- health/snapshots
    def health(self) -> List[SourceHealth]:
        return self.health_repo.all()

    def snapshots(self) -> List[DailySnapshot]:
        return self.snapshot_repo.all()

    def top_jobs(self, limit: int = 10) -> List[JobRecord]:
        return self.jobs.list_jobs(order_by="score", limit=limit)

    # ----------------------------------------------------------------- notifications
    def daily_summary(self) -> Dict[str, object]:
        """Compact payload for the Telegram daily digest."""
        return {
            "total_jobs": self.jobs.count(),
            "jobs_today": self.jobs.count_today(),
            "by_source": self.by_source(),
            "top_skills": self.skill_frequency(top=8),
        }
