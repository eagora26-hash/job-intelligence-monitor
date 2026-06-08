"""Tests for the enrichment + filtering pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from job_monitor.models import JobRecord
from job_monitor.pipeline import Enricher, FilterConfig, JobFilter


def _job(**kw) -> JobRecord:
    base = dict(source="remoteok", url="https://x/" + kw.get("title", "t"), title="t")
    base.update(kw)
    return JobRecord(**base)


def test_score_sums_keyword_weights():
    enricher = Enricher()
    # "python" (10) + "automation" (10) + "web scraping" (10) + "scraping" (10)
    text = "python automation and web scraping role"
    assert enricher.score(text) == 40


def test_score_zero_for_irrelevant_text():
    assert Enricher().score("barista wanted for coffee shop") == 0


def test_classify_picks_dominant_category():
    enricher = Enricher()
    assert enricher.classify("python web scraping with scrapy and selenium") == "Web Scraping"
    assert enricher.classify("shopify woocommerce ecommerce store") == "E-commerce"
    assert enricher.classify("nothing relevant here") == ""


def test_extract_skills_canonicalizes():
    skills = Enricher().extract_skills("we use python, fastapi, docker and postgres")
    assert "Python" in skills and "FastAPI" in skills and "Docker" in skills
    assert "PostgreSQL" in skills


def test_quality_score_rewards_completeness():
    full = _job(company="Acme", description="x" * 100, salary="$100k", location="Remote",
                tags=["python"])
    sparse = _job(company="", description="", salary="", location="", tags=[])
    assert Enricher.quality(full) == 100
    assert Enricher.quality(sparse) == 0


def test_enrich_populates_all_fields():
    enriched = Enricher().enrich(
        _job(title="Python Automation Engineer",
             description="Build web scraping bots with selenium. " * 5,
             company="Acme", salary="$120k", location="Remote", tags=["python"])
    )
    assert enriched.score > 0
    assert enriched.category != ""
    assert "Python" in enriched.skills
    assert enriched.quality_score > 0


def test_filter_include_exclude():
    jobs = [
        _job(title="Python dev", description="python automation"),
        _job(title="PHP dev", description="wordpress php"),
        _job(title="Unpaid intern", description="unpaid python role"),
    ]
    f = JobFilter(FilterConfig(include_keywords=["python"], exclude_keywords=["unpaid"]))
    kept = f.apply(jobs)
    assert len(kept) == 1
    assert kept[0].title == "Python dev"


def test_filter_score_source_remote_date():
    now = datetime.now(timezone.utc)
    jobs = [
        _job(title="a", score=20, source="remoteok", remote=True, posted_at=now),
        _job(title="b", score=5, source="remoteok", remote=True, posted_at=now),
        _job(title="c", score=30, source="fiverr", remote=False,
             posted_at=now - timedelta(days=10)),
    ]
    assert len(JobFilter(FilterConfig(min_score=10)).apply(jobs)) == 2
    assert len(JobFilter(FilterConfig(sources=["remoteok"])).apply(jobs)) == 2
    assert len(JobFilter(FilterConfig(remote_only=True)).apply(jobs)) == 2
    assert len(JobFilter(FilterConfig(since=now - timedelta(days=1))).apply(jobs)) == 2
