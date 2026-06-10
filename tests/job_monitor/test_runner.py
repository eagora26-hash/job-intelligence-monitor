"""Tests for the concurrent pipeline runner (no network, fake scrapers + capturing notifier)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Mapping

import pytest

from job_monitor.config.settings import Settings
from job_monitor.database import Database, HealthRepository, JobRepository
from job_monitor.models import JobRecord
from job_monitor.notifications.base import Notifier
from job_monitor.pipeline.runner import PipelineRunner
from job_monitor.scrapers.base import BaseScraper, RawJob
from job_monitor.services.state import StateStore


class _FakeScraper(BaseScraper):
    name = "remoteok"
    label = "RemoteOK (fake)"

    def __init__(self, raw: List[RawJob]) -> None:
        super().__init__()
        self._raw = raw

    def fetch_raw(self) -> List[RawJob]:
        return self._raw


class _FailingScraper(BaseScraper):
    name = "freelancer"

    def fetch_raw(self) -> List[RawJob]:
        raise RuntimeError("boom")


class _CapturingNotifier(Notifier):
    def __init__(self) -> None:
        self.new_jobs: List[JobRecord] = []
        self.errors: List[str] = []
        self.sent: List[str] = []

    def send(self, text: str) -> bool:
        self.sent.append(text)
        return True

    def notify_new_jobs(self, jobs: List[JobRecord]) -> int:
        self.new_jobs.extend(jobs)
        return len(jobs)

    def notify_daily_summary(self, summary: Mapping[str, object]) -> bool:
        return True

    def notify_error(self, message: str) -> bool:
        self.errors.append(message)
        return True


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_PATH=str(tmp_path / "jobs.db"),
        ARCHIVE_DB_PATH=str(tmp_path / "archive.db"),
        DATA_DIR=str(tmp_path / "data"),
        LOG_DIR=str(tmp_path / "logs"),
        BACKUP_DIR=str(tmp_path / "backup"),
        EXPORT_DIR=str(tmp_path / "exports"),
        NOTIFY_MIN_SCORE=1,
        MAX_WORKERS=2,
    )


def _raw(title: str, url: str, desc: str = "python automation web scraping") -> RawJob:
    return RawJob(source="remoteok", title=title, url=url, description=desc, company="Acme")


def _make_runner(settings, scrapers, notifier) -> PipelineRunner:
    db = Database(settings.database_path)
    return PipelineRunner(
        settings=settings,
        database=db,
        scrapers=scrapers,
        notifier=notifier,
        state_store=StateStore(settings.state_file),
    )


def test_first_run_establishes_baseline_without_alerts(test_settings):
    notifier = _CapturingNotifier()
    scraper = _FakeScraper([_raw("Python Dev", "https://x/1"), _raw("Automation Eng", "https://x/2")])
    runner = _make_runner(test_settings, [scraper], notifier)

    report = runner.run_once()

    assert report.baseline is True
    assert report.total_new == 2
    assert report.notified == 0  # baseline never sends per-job alerts
    assert notifier.new_jobs == []
    assert any("Baseline established" in t for t in notifier.sent)
    # Persisted + enriched, and every baseline job is marked notified.
    jobs = JobRepository(runner.database)
    assert jobs.count() == 2
    assert all(j.score > 0 for j in jobs.all_jobs())
    assert all(j.notified for j in jobs.all_jobs())


def test_monitoring_run_notifies_only_new_jobs(test_settings):
    notifier = _CapturingNotifier()
    raw = [_raw("Python Dev", "https://x/1")]
    scraper = _FakeScraper(raw)
    runner = _make_runner(test_settings, [scraper], notifier)

    first = runner.run_once()       # baseline
    second = runner.run_once()      # same data -> nothing new, no alerts
    raw.append(_raw("Scraping Eng", "https://x/2"))
    third = runner.run_once()       # one genuinely new job -> exactly one alert

    assert first.baseline and not second.baseline and not third.baseline
    assert second.total_new == 0 and second.notified == 0
    assert third.total_new == 1 and third.notified == 1
    assert [j.url for j in notifier.new_jobs] == ["https://x/2"]
    assert JobRepository(runner.database).count() == 2


def test_notify_sources_filter(test_settings):
    settings = test_settings.model_copy(update={"notify_sources": ["weworkremotely"]})
    notifier = _CapturingNotifier()
    raw = [_raw("Python Dev", "https://x/1")]
    scraper = _FakeScraper(raw)  # source = remoteok, not in notify_sources
    runner = _make_runner(settings, [scraper], notifier)

    runner.run_once()  # baseline
    raw.append(_raw("Scraping Eng", "https://x/2"))
    report = runner.run_once()

    assert report.total_new == 1        # stored
    assert report.notified == 0         # but silenced by the source filter
    assert notifier.new_jobs == []


def test_failure_isolated_and_alerted(test_settings):
    notifier = _CapturingNotifier()
    good = _FakeScraper([_raw("Python Dev", "https://x/1")])
    runner = _make_runner(test_settings, [good, _FailingScraper()], notifier)

    report = runner.run_once()

    # Good source still stored despite the other failing.
    assert report.total_new == 1
    statuses = {s.source: s.success for s in report.sources}
    assert statuses["remoteok"] is True
    assert statuses["freelancer"] is False
    assert any("freelancer" in e for e in notifier.errors)
    # Health reflects both outcomes.
    health = {h.source: h for h in HealthRepository(runner.database).all()}
    assert health["remoteok"].success_count == 1
    assert health["freelancer"].failure_count == 1


def test_state_and_snapshot_written(test_settings):
    runner = _make_runner(test_settings, [_FakeScraper([_raw("Python Dev", "https://x/1")])],
                          _CapturingNotifier())
    runner.run_once()

    state = StateStore(test_settings.state_file).load()
    assert state.total_runs == 1
    assert state.last_successful_run is not None
    assert state.source_status["remoteok"].last_status == "success"

    from job_monitor.database import SnapshotRepository
    snaps = SnapshotRepository(runner.database).all()
    assert len(snaps) == 1
    assert snaps[0].total_jobs == 1
