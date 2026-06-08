"""Demo-data generator.

Populates the database with realistic, enriched, historically-spread jobs so the dashboard can
be demoed (and screenshotted) even when live sources are unavailable or blocked. Data is
*synthetic but plausible* — clearly a demo, never passed off as real scraped data. Jobs are run
through the real :class:`Enricher`, so scores/categories/skills are consistent with production.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from job_monitor.config import Settings, get_settings
from job_monitor.database import Database, JobRepository, SnapshotRepository
from job_monitor.models import DailySnapshot, JobRecord
from job_monitor.observability import get_logger
from job_monitor.pipeline.enrichment import Enricher

logger = get_logger("services.demo")

_SOURCES = ["remoteok", "weworkremotely", "freelancer", "fiverr", "wellfound"]

_TITLES = [
    "Python Automation Engineer", "Senior Web Scraping Developer", "Data Engineer (ETL)",
    "Shopify Integration Specialist", "Telegram Bot Developer", "Backend Python Developer",
    "Selenium/Playwright Automation Expert", "E-commerce Automation Consultant",
    "AI Workflow Automation Engineer", "Streamlit Dashboard Developer",
    "WooCommerce API Developer", "Lead Generation Scraper", "FastAPI Backend Engineer",
    "Data Extraction Specialist", "RPA Developer", "Django Full-Stack Developer",
]

_COMPANIES = [
    "Acme Remote", "Globex", "DataLabs", "RocketAI", "NimbusSoft", "ScrapeWorks",
    "AutomateHQ", "ShopFlow", "InsightPipe", "BotForge", "CloudHarvest", "PixelTrade",
]

_DESCRIPTIONS = [
    "Build and maintain {kw} pipelines using Python, Playwright and Selenium. "
    "Experience with Docker, PostgreSQL and REST API integration required.",
    "We need a developer to automate {kw} workflows. Strong Python, pandas and "
    "data extraction skills. Bonus: Shopify / WooCommerce and AWS.",
    "Looking for an expert in {kw} and web scraping. FastAPI, Django, Redis and "
    "ETL experience are a big plus. Remote, contract.",
    "Help us scale our {kw} platform. You will work with Kafka, Airflow and "
    "Streamlit dashboards. Python + SQL essential.",
]

_KEYWORDS = [
    "automation", "web scraping", "data engineering", "e-commerce", "ai automation",
    "lead generation", "api integration", "workflow automation", "etl",
]

_LOCATIONS = ["Remote", "Worldwide", "Anywhere", "Europe Only", "US Only", "Remote (EU)"]
_SALARIES = ["$80k - $120k", "$100k - $150k", "$60/hr", "$500 - $1500 project", "", "$90k+"]


def _demo_url(source: str, index: int) -> str:
    digest = hashlib.md5(f"{source}-{index}".encode()).hexdigest()[:10]
    return f"https://example.com/demo/{source}/{digest}"


def generate_demo_data(
    count: int = 120,
    *,
    settings: Optional[Settings] = None,
    seed: int = 42,
) -> int:
    """Seed ``count`` demo jobs spread over the last ~30 days. Returns the number created."""
    settings = settings or get_settings()
    settings.ensure_directories()
    database = Database(settings.database_path)
    database.initialize()
    jobs_repo = JobRepository(database)
    snap_repo = SnapshotRepository(database)
    enricher = Enricher()

    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    created = 0
    per_day: dict[str, int] = {}

    for i in range(count):
        source = rng.choice(_SOURCES)
        keyword = rng.choice(_KEYWORDS)
        title = rng.choice(_TITLES)
        description = rng.choice(_DESCRIPTIONS).format(kw=keyword)
        days_ago = rng.randint(0, 29)
        first_seen = now - timedelta(days=days_ago, hours=rng.randint(0, 23))
        location = rng.choice(_LOCATIONS)

        record = JobRecord(
            source=source,
            url=_demo_url(source, i),
            title=title,
            company=rng.choice(_COMPANIES),
            description=description,
            location=location,
            salary=rng.choice(_SALARIES),
            tags=rng.sample(["python", "remote", "contract", "selenium", "shopify", "api"], k=3),
            remote=any(h in location.lower() for h in ("remote", "worldwide", "anywhere")),
            posted_at=first_seen,
            first_seen=first_seen,
            last_seen=now - timedelta(days=rng.randint(0, days_ago)),
            notified=rng.random() < 0.5,
        )
        enriched = enricher.enrich(record)
        jobs_repo.seed(enriched)
        created += 1
        day_key = first_seen.strftime("%Y-%m-%d")
        per_day[day_key] = per_day.get(day_key, 0) + 1

    _write_demo_snapshots(snap_repo, jobs_repo, per_day)
    logger.info("Generated %d demo jobs across %d sources", created, len(_SOURCES))
    return created


def _write_demo_snapshots(snap_repo, jobs_repo: JobRepository, per_day: dict[str, int]) -> None:
    """Create per-day snapshots so historical trend charts are populated."""
    from datetime import date as _date

    total_sources = len(jobs_repo.distinct_sources())
    skill_count = len(jobs_repo.distinct_skills())
    avg = round(jobs_repo.avg_score(), 2)
    for day_str, new_count in per_day.items():
        snap_repo.upsert(
            DailySnapshot(
                snapshot_date=_date.fromisoformat(day_str),
                total_jobs=jobs_repo.count(),
                new_jobs=new_count,
                source_count=total_sources,
                keyword_count=skill_count,
                notified_count=jobs_repo.notified_count(),
                avg_score=avg,
            )
        )
