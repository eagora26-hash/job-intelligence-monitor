"""Tests for analytics, exporters, and the demo-data generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from job_monitor.analytics import AnalyticsService, JobExporter
from job_monitor.config.settings import Settings
from job_monitor.database import Database, JobRepository
from job_monitor.models import JobRecord
from job_monitor.services.demo import generate_demo_data


@pytest.fixture()
def demo_db(tmp_path: Path) -> Database:
    settings = Settings(
        _env_file=None,
        DATABASE_PATH=str(tmp_path / "jobs.db"),
        DATA_DIR=str(tmp_path / "data"),
        LOG_DIR=str(tmp_path / "logs"),
        BACKUP_DIR=str(tmp_path / "backup"),
        EXPORT_DIR=str(tmp_path / "exports"),
        ARCHIVE_DB_PATH=str(tmp_path / "archive.db"),
    )
    generate_demo_data(count=60, settings=settings, seed=1)
    return Database(settings.database_path)


def test_demo_data_is_enriched_and_spread(demo_db):
    repo = JobRepository(demo_db)
    jobs = repo.all_jobs()
    assert len(jobs) == 60
    assert all(j.score > 0 for j in jobs)          # enriched
    assert any(j.remote for j in jobs)             # remote flag set
    assert len({j.source for j in jobs}) >= 3      # multiple sources
    assert len(repo.count_by_day(40)) > 1          # spread across days


def test_analytics_overview_and_distributions(demo_db):
    svc = AnalyticsService(demo_db)
    overview = svc.overview()
    assert overview["total_jobs"] == 60
    assert overview["source_count"] >= 3
    assert sum(svc.by_source().values()) == 60
    assert len(svc.skill_frequency(5)) <= 5
    assert sum(svc.score_distribution().values()) == 60
    summary = svc.daily_summary()
    assert "by_source" in summary and "top_skills" in summary


def test_exporter_csv_excel_json(demo_db, tmp_path):
    jobs = JobRepository(demo_db).all_jobs()
    exporter = JobExporter(jobs)

    df = exporter.to_dataframe()
    assert len(df) == 60
    assert "title" in df.columns and "url" in df.columns

    csv_path = exporter.to_csv(tmp_path / "out.csv")
    xlsx_path = exporter.to_excel(tmp_path / "out.xlsx")
    json_path = exporter.to_json(tmp_path / "out.json")
    assert csv_path.exists() and xlsx_path.exists() and json_path.exists()
    assert len(exporter.to_csv_bytes()) > 0
    assert exporter.to_excel_bytes()[:2] == b"PK"  # xlsx is a zip
    assert exporter.to_json_bytes().lstrip()[:1] == b"["  # JSON array of records


def test_exporter_handles_empty():
    exporter = JobExporter([])
    assert exporter.to_dataframe().empty
    assert exporter.to_csv_bytes()  # header row still emitted


def test_env_writer_rejects_secrets(tmp_path):
    from job_monitor.config.env_file import update_env_file

    env = tmp_path / ".env"
    update_env_file(env, {"ENABLE_FIVERR": "false", "POLLING_INTERVAL": "900"})
    content = env.read_text()
    assert "ENABLE_FIVERR=false" in content
    assert "POLLING_INTERVAL=900" in content
    with pytest.raises(ValueError):
        update_env_file(env, {"TELEGRAM_BOT_TOKEN": "leak"})
