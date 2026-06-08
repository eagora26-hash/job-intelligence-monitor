"""Tests for the repository layer: dedup, change detection, queries, health."""

from __future__ import annotations

from job_monitor.database import UpsertStatus
from job_monitor.models import JobRecord


def test_insert_then_dedupe(job_repo, sample_job):
    assert job_repo.upsert(sample_job).status is UpsertStatus.NEW
    assert job_repo.upsert(sample_job).status is UpsertStatus.UNCHANGED
    assert job_repo.count() == 1  # unique-on-url dedup


def test_change_detection_records_history(job_repo, sample_job):
    job_repo.upsert(sample_job)
    changed = sample_job.model_copy(update={"salary": "$200k", "title": "Lead Engineer"})
    result = job_repo.upsert(changed)
    assert result.status is UpsertStatus.UPDATED
    fields = {c.field for c in result.changes}
    assert fields == {"salary", "title"}
    assert job_repo.count() == 1  # still the same job, just updated


def test_first_seen_preserved_notified_sticky(job_repo, sample_job):
    job_repo.upsert(sample_job)
    job_repo.mark_notified([sample_job.url])
    # Re-scrape with a content change.
    job_repo.upsert(sample_job.model_copy(update={"description": "new text"}))
    stored = job_repo.get(sample_job.url)
    assert stored is not None
    assert stored.notified is True  # notification status is sticky across updates
    assert stored.first_seen is not None


def test_query_filters_and_aggregates(job_repo):
    jobs = [
        JobRecord(source="remoteok", url="u1", title="Python dev", score=20, category="Python Development", remote=True),
        JobRecord(source="weworkremotely", url="u2", title="Scraper", score=5, category="Web Scraping", remote=False),
        JobRecord(source="remoteok", url="u3", title="Automation", score=15, category="Automation", remote=True),
    ]
    for j in jobs:
        job_repo.upsert(j)

    assert job_repo.count() == 3
    assert job_repo.count_by_source() == {"remoteok": 2, "weworkremotely": 1}
    assert len(job_repo.list_jobs(min_score=10)) == 2
    assert len(job_repo.list_jobs(source="remoteok")) == 2
    assert len(job_repo.list_jobs(remote_only=True)) == 2
    assert len(job_repo.list_jobs(search="scraper")) == 1
    # Default order is score DESC.
    ordered = job_repo.list_jobs()
    assert [j.score for j in ordered] == [20, 15, 5]


def test_unnotified_threshold(job_repo):
    job_repo.upsert(JobRecord(source="s", url="a", score=20))
    job_repo.upsert(JobRecord(source="s", url="b", score=3))
    assert {j.url for j in job_repo.unnotified(min_score=10)} == {"a"}


def test_health_repository_roundtrip(health_repo):
    h = health_repo.get("remoteok")
    h.record_success(jobs_found=12, response_ms=150)
    health_repo.save(h)
    reloaded = health_repo.get("remoteok")
    assert reloaded.success_count == 1
    assert reloaded.last_jobs_found == 12
    assert reloaded.status == "healthy"
