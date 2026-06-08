"""Tests for state/resume, backup, and archive services."""

from __future__ import annotations

from pathlib import Path

import pytest

from job_monitor.config.settings import Settings
from job_monitor.database import Database, JobRepository
from job_monitor.models import JobRecord
from job_monitor.services.archive import ArchiveService
from job_monitor.services.backup import BackupService
from job_monitor.services.state import MonitorState, SourceState, StateStore


@pytest.fixture()
def svc_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_PATH=str(tmp_path / "jobs.db"),
        ARCHIVE_DB_PATH=str(tmp_path / "archive.db"),
        DATA_DIR=str(tmp_path / "data"),
        BACKUP_DIR=str(tmp_path / "backup"),
    )


def test_state_store_roundtrip(tmp_path):
    store = StateStore(tmp_path / "state.json")
    assert store.load().total_runs == 0  # missing file -> defaults
    state = MonitorState(total_runs=3, source_status={"remoteok": SourceState(last_status="success")})
    store.save(state)
    reloaded = store.load()
    assert reloaded.total_runs == 3
    assert reloaded.source_status["remoteok"].last_status == "success"


def test_backup_creates_and_prunes(svc_settings):
    db = Database(svc_settings.database_path)
    db.initialize()
    JobRepository(db).upsert(JobRecord(source="s", url="u1", title="t"))

    service = BackupService(svc_settings, retention_days=30)
    backup = service.create_backup()
    assert backup is not None and backup.exists()
    assert len(service.list_backups()) == 1

    # Retention of 0 days prunes everything on the next call.
    BackupService(svc_settings, retention_days=0).prune()
    assert service.list_backups() == []


def test_backup_noop_without_database(svc_settings):
    assert BackupService(svc_settings).create_backup() is None


def test_archive_moves_only_stale_jobs(svc_settings):
    db = Database(svc_settings.database_path)
    db.initialize()
    repo = JobRepository(db)
    repo.upsert(JobRecord(source="s", url="u1", title="t1"))
    repo.upsert(JobRecord(source="s", url="u2", title="t2"))

    service = ArchiveService(svc_settings)
    # Nothing is old enough yet.
    assert service.archive_older_than(days=9999) == 0
    assert repo.count() == 2
    # Everything is "older than -1 day" (cutoff in the future) -> all archived.
    moved = service.archive_older_than(days=-1)
    assert moved == 2
    assert repo.count() == 0
    assert service.archive_count() == 2
