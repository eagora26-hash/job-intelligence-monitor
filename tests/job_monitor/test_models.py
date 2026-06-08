"""Tests for the canonical domain models."""

from __future__ import annotations

from datetime import datetime, timezone

from job_monitor.models import JobRecord, SourceHealth


def test_job_list_coercion_from_string():
    job = JobRecord(source="x", url="u", tags="python, automation | scraping")
    assert job.tags == ["python", "automation", "scraping"]


def test_searchable_text_is_lowercased_blob(sample_job):
    text = sample_job.searchable_text
    assert "python" in text and "acme corp" in text
    assert text == text.lower()


def test_content_hash_is_stable_and_change_sensitive(sample_job):
    h1 = sample_job.compute_content_hash()
    assert h1 == sample_job.compute_content_hash()  # deterministic
    changed = sample_job.model_copy(update={"salary": "$200k"})
    assert changed.compute_content_hash() != h1
    # Enrichment/timestamps must NOT affect the content hash.
    enriched = sample_job.model_copy(update={"score": 99, "scraped_at": datetime.now(timezone.utc)})
    assert enriched.compute_content_hash() == h1


def test_with_content_hash_populates_field(sample_job):
    assert sample_job.with_content_hash().content_hash != ""


def test_source_health_status_transitions():
    h = SourceHealth(source="remoteok")
    assert h.status == "unknown"
    h.record_success(jobs_found=10, response_ms=200)
    assert h.status == "healthy"
    assert h.avg_response_ms == 200
    h.record_success(jobs_found=5, response_ms=400)
    assert h.avg_response_ms == 300  # incremental mean
    for _ in range(5):
        h.record_failure(error="boom")
    assert h.status == "failing"
    assert 0 <= h.success_rate <= 1
