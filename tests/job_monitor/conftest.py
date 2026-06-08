"""Shared fixtures for the Job Intelligence Monitor test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from job_monitor.database import Database, HealthRepository, JobRepository
from job_monitor.models import JobRecord


@pytest.fixture()
def database(tmp_path: Path) -> Database:
    """A fresh, initialized SQLite database in a temp dir (one per test)."""
    db = Database(tmp_path / "jobs.db")
    db.initialize()
    return db


@pytest.fixture()
def job_repo(database: Database) -> JobRepository:
    return JobRepository(database)


@pytest.fixture()
def health_repo(database: Database) -> HealthRepository:
    return HealthRepository(database)


@pytest.fixture()
def sample_job() -> JobRecord:
    return JobRecord(
        source="remoteok",
        url="https://remoteok.com/remote-jobs/123",
        title="Senior Python Automation Engineer",
        company="Acme Corp",
        description="Build web scraping and automation pipelines with Python and Playwright.",
        location="Remote",
        salary="$120k",
        tags=["python", "automation"],
        remote=True,
    )
