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

    def send(self, text: str) -> bool:
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


def test_run_once_stores_and_notifies(test_settings):
    notifier = _CapturingNotifier()
    scraper = _FakeScraper([_raw("Python Dev", "https://x/1"), _raw("Automation Eng", "https://x/2")])
    runner = _make_runner(test_settings, [scraper], notifier)

    report = runner.run_once()

    assert report.total_new == 2
    assert report.notified == 2
    assert len(notifier.new_jobs) == 2
    # Persisted + enriched.
    jobs = JobRepository(runner.database)
    assert jobs.count() == 2
    assert all(j.score > 0 for j in jobs.all_jobs())


def test_second_run_is_idempotent(test_settings):
    notifier = _CapturingNotifier()
    raw = [_raw("Python Dev", "https://x/1")]
    runner = _make_runner(test_settings, [_FakeScraper(raw)], notifier)

    first = runner.run_once()
    second = runner.run_once()

    assert first.total_new == 1
    assert second.total_new == 0  # deduped
    assert JobRepository(runner.database).count() == 1


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
