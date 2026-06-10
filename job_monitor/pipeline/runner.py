"""The concurrent pipeline runner: scrape → normalize → enrich → filter → store → notify.

This is the orchestration core. Scrapers run **concurrently** (network-bound) in a thread
pool; results are then processed sequentially (SQLite writes are serialized). Every source is
isolated — a failure is recorded to health + state and optionally alerted, but never stops the
run. After processing, new relevant jobs are notified, state is checkpointed, and a daily
snapshot is written.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple

from job_monitor.config import Settings, get_settings
from job_monitor.config.keywords import DEFAULT_EXCLUDE_KEYWORDS
from job_monitor.database import (
    Database,
    HealthRepository,
    JobRepository,
    SnapshotRepository,
    UpsertStatus,
)
from job_monitor.models import DailySnapshot, JobRecord
from job_monitor.normalizers import Normalizer
from job_monitor.notifications import Notifier, build_notifier
from job_monitor.observability import get_logger
from job_monitor.pipeline.enrichment import Enricher
from job_monitor.pipeline.filters import FilterConfig, JobFilter
from job_monitor.scrapers import BaseScraper, ScrapeResult, build_scrapers
from job_monitor.services.state import StateStore

logger = get_logger("pipeline.runner")


@dataclass
class SourceRunInfo:
    """Per-source outcome within a single run."""

    source: str
    success: bool = True
    error: str = ""
    duration_ms: float = 0.0
    scraped: int = 0
    stored: int = 0
    new: int = 0
    updated: int = 0
    unchanged: int = 0


@dataclass
class RunReport:
    """Summary of one full pipeline run (returned to CLI/scheduler/tests)."""

    started_at: datetime
    finished_at: datetime
    sources: List[SourceRunInfo] = field(default_factory=list)
    new_jobs: List[JobRecord] = field(default_factory=list)
    notified: int = 0
    baseline: bool = False

    @property
    def duration_ms(self) -> float:
        return (self.finished_at - self.started_at).total_seconds() * 1000

    @property
    def total_scraped(self) -> int:
        return sum(s.scraped for s in self.sources)

    @property
    def total_new(self) -> int:
        return sum(s.new for s in self.sources)

    @property
    def total_updated(self) -> int:
        return sum(s.updated for s in self.sources)

    def summary_line(self) -> str:
        ok = sum(1 for s in self.sources if s.success)
        mode = "BASELINE | " if self.baseline else ""
        return (
            f"Run finished in {self.duration_ms:.0f} ms | {mode}"
            f"sources ok {ok}/{len(self.sources)} | "
            f"scraped {self.total_scraped} | new {self.total_new} | updated {self.total_updated} | "
            f"notified {self.notified}"
        )


class PipelineRunner:
    """Wires the acquisition + intelligence + persistence + notification layers together."""

    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        database: Optional[Database] = None,
        scrapers: Optional[List[BaseScraper]] = None,
        normalizer: Optional[Normalizer] = None,
        enricher: Optional[Enricher] = None,
        job_filter: Optional[JobFilter] = None,
        notifier: Optional[Notifier] = None,
        state_store: Optional[StateStore] = None,
        store_min_score: int = 1,
    ) -> None:
        self.settings = settings or get_settings()
        self.settings.ensure_directories()
        self.database = database or Database(self.settings.database_path)
        self.database.initialize()

        self.jobs = JobRepository(self.database)
        self.health = HealthRepository(self.database)
        self.snapshots = SnapshotRepository(self.database)

        self.scrapers = scrapers if scrapers is not None else build_scrapers(self.settings)
        self.normalizer = normalizer or Normalizer()
        self.enricher = enricher or Enricher()
        self.notifier = notifier or build_notifier(self.settings)
        self.state_store = state_store or StateStore(self.settings.state_file)
        self.job_filter = job_filter or JobFilter(self._default_filter_config())
        self.store_min_score = store_min_score

    def _default_filter_config(self) -> FilterConfig:
        return FilterConfig(
            include_keywords=self.settings.include_keywords,
            exclude_keywords=self.settings.exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS,
        )

    # ----------------------------------------------------------------- run
    def run_once(self) -> RunReport:
        started = datetime.now(timezone.utc)
        # An empty jobs table means this is the FIRST run: it establishes the baseline.
        # Baseline runs ingest everything but send no per-job alerts (only a summary),
        # so a fresh deployment never floods the Telegram chat.
        baseline = self.jobs.count() == 0
        logger.info(
            "Starting %s run with %d source(s)",
            "BASELINE" if baseline else "monitoring",
            len(self.scrapers),
        )

        results = self._scrape_concurrently()

        sources_info: List[SourceRunInfo] = []
        new_jobs: List[JobRecord] = []
        for result in results:
            info, fresh = self._process_result(result)
            sources_info.append(info)
            new_jobs.extend(fresh)

        if baseline:
            notified = 0
            self._finish_baseline(new_jobs)
        else:
            notified = self._notify(new_jobs)
        self._checkpoint_state(sources_info)
        self._write_snapshot(new_today=len(new_jobs))

        report = RunReport(
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            sources=sources_info,
            new_jobs=new_jobs,
            notified=notified,
            baseline=baseline,
        )
        logger.info(report.summary_line())
        return report

    # ----------------------------------------------------------------- steps
    def _scrape_concurrently(self) -> List[ScrapeResult]:
        if not self.scrapers:
            return []
        workers = max(1, min(self.settings.max_workers, len(self.scrapers)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(lambda s: s.scrape(), self.scrapers))

    def _process_result(self, result: ScrapeResult) -> Tuple[SourceRunInfo, List[JobRecord]]:
        info = SourceRunInfo(source=result.source, duration_ms=result.duration_ms)
        health = self.health.get(result.source)

        if not result.success:
            info.success = False
            info.error = result.error
            health.record_failure(error=result.error)
            self.health.save(health)
            self.notifier.notify_error(f"Source '{result.source}' failed: {result.error}")
            return info, []

        records = self.normalizer.normalize_many(result.raw_jobs)
        enriched = self.enricher.enrich_many(records)
        kept = [
            job for job in self.job_filter.apply(enriched) if job.score >= self.store_min_score
        ]
        info.scraped = result.count
        info.stored = len(kept)

        fresh: List[JobRecord] = []
        for job in kept:
            outcome = self.jobs.upsert(job)
            if outcome.status is UpsertStatus.NEW:
                info.new += 1
                fresh.append(outcome.job)
            elif outcome.status is UpsertStatus.UPDATED:
                info.updated += 1
            else:
                info.unchanged += 1

        health.record_success(jobs_found=len(kept), response_ms=result.duration_ms)
        self.health.save(health)
        return info, fresh

    def _finish_baseline(self, new_jobs: List[JobRecord]) -> None:
        """Close out a baseline run: mark everything notified, send one summary message."""
        self.jobs.mark_notified(j.url for j in new_jobs)
        per_source = {}
        for j in new_jobs:
            per_source[j.source] = per_source.get(j.source, 0) + 1
        breakdown = " · ".join(f"{s}: {n}" for s, n in sorted(per_source.items())) or "no jobs"
        self.notifier.send(
            f"📊 <b>Baseline established</b> — {len(new_jobs)} jobs ingested ({breakdown}).\n"
            "From now on you will only be alerted about <b>new</b> jobs."
        )

    def _notify(self, new_jobs: List[JobRecord]) -> int:
        allowed = self.settings.notify_sources
        worthy = [
            j for j in new_jobs
            if j.score >= self.settings.notify_min_score
            and (not allowed or j.source in allowed)
        ]
        if not worthy:
            return 0
        sent = self.notifier.notify_new_jobs(worthy)
        self.jobs.mark_notified(j.url for j in worthy)
        return sent

    def _checkpoint_state(self, sources_info: List[SourceRunInfo]) -> None:
        state = self.state_store.load()
        now = StateStore.now()
        state.last_run = now
        state.total_runs += 1
        any_success = any(s.success for s in sources_info)
        if any_success:
            state.last_successful_run = now
        for info in sources_info:
            from job_monitor.services.state import SourceState

            state.source_status[info.source] = SourceState(
                last_status="success" if info.success else "failure",
                last_run=now,
                last_jobs_found=info.stored,
                last_error=info.error,
            )
        self.state_store.save(state)

    def _write_snapshot(self, *, new_today: int) -> None:
        snapshot = DailySnapshot(
            snapshot_date=date.today(),
            total_jobs=self.jobs.count(),
            new_jobs=new_today,
            source_count=len(self.jobs.distinct_sources()),
            keyword_count=len(self.jobs.distinct_skills()),
            notified_count=self.jobs.notified_count(),
            avg_score=round(self.jobs.avg_score(), 2),
        )
        self.snapshots.upsert(snapshot)
