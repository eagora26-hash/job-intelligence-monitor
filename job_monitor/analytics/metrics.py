"""Analytics service: derives headline metrics, distributions, and trends from the database.

A thin read-only service over the repositories. The dashboard and the Telegram daily summary
both consume it, so the "numbers" are computed in exactly one place.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
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

    # ----------------------------------------------------------------- intelligence
    def new_last_24h(self) -> int:
        """Jobs first seen within the last 24 hours (rolling, not calendar-day)."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        return sum(
            1 for j in self.jobs.all_jobs() if j.first_seen and j.first_seen >= cutoff
        )

    def most_active_source(self) -> Tuple[str, int]:
        """The source contributing the most jobs (name, count); ('—', 0) when empty."""
        by_source = self.by_source()
        if not by_source:
            return ("—", 0)
        return max(by_source.items(), key=lambda kv: kv[1])

    def weekly_trend(self, weeks: int = 8) -> Dict[str, int]:
        """New jobs per ISO week (label 'YYYY-Www'), oldest → newest."""
        counter: Counter[str] = Counter()
        cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks)
        for j in self.jobs.all_jobs():
            ts = j.first_seen
            if ts and ts >= cutoff:
                iso = ts.isocalendar()
                counter[f"{iso.year}-W{iso.week:02d}"] += 1
        return dict(sorted(counter.items()))

    def skill_source_matrix(self, top: int = 12) -> Dict[str, Dict[str, int]]:
        """Skill × source job counts for the demand heatmap: {skill: {source: n}}."""
        totals: Counter[str] = Counter()
        matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for j in self.jobs.all_jobs():
            for skill in j.skills:
                totals[skill] += 1
                matrix[skill][j.source] += 1
        return {s: dict(matrix[s]) for s, _ in totals.most_common(top)}

    def source_stats(self) -> List[Dict[str, object]]:
        """Per-source comparison: volume, avg relevance/quality, remote share."""
        groups: Dict[str, List[JobRecord]] = defaultdict(list)
        for j in self.jobs.all_jobs():
            groups[j.source].append(j)
        stats = []
        for source, jobs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            n = len(jobs)
            stats.append({
                "source": source,
                "jobs": n,
                "avg_score": round(sum(j.score for j in jobs) / n, 1),
                "avg_quality": round(sum(j.quality_score for j in jobs) / n, 1),
                "remote_pct": round(100 * sum(1 for j in jobs if j.remote) / n),
            })
        return stats

    def health_score(self) -> int:
        """Overall source-fleet health, 0–100: run-weighted success rate."""
        records = self.health_repo.all()
        total = sum(h.total_runs for h in records)
        if not total:
            return 100
        return round(100 * sum(h.success_count for h in records) / total)

    def reliability_leaderboard(self) -> List[Dict[str, object]]:
        """Sources ranked by success rate (then volume) for the reliability leaderboard."""
        rows = []
        for h in self.health_repo.all():
            rate = round(100 * h.success_count / h.total_runs) if h.total_runs else 0
            rows.append({
                "source": h.source,
                "success_rate": rate,
                "runs": h.total_runs,
                "avg_response_ms": round(h.avg_response_ms),
                "last_jobs_found": h.last_jobs_found,
                "last_error": h.last_error or "—",
            })
        return sorted(rows, key=lambda r: (-r["success_rate"], -r["runs"]))

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
