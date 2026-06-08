"""FastAPI application factory exposing a read API over monitored jobs + analytics.

Endpoints
---------
    GET /health                 liveness + headline counts
    GET /jobs                   filtered job list (query/source/category/min_score/remote)
    GET /jobs/top               highest-relevance jobs
    GET /analytics/overview     headline KPIs
    GET /analytics/sources      jobs-by-source distribution
    GET /analytics/skills       top skills
    GET /sources/health         per-source scraper health

Run with:  uvicorn job_monitor.api.app:app  (or `python -m job_monitor.api.app`)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query

from job_monitor.analytics import AnalyticsService
from job_monitor.config import Settings, get_settings
from job_monitor.database import Database, HealthRepository, JobRepository
from job_monitor.models import JobRecord, SourceHealth


def create_app(settings: Optional[Settings] = None, database: Optional[Database] = None) -> FastAPI:
    """Build the FastAPI app. Inject ``settings``/``database`` for testing."""
    settings = settings or get_settings()
    settings.ensure_directories()
    database = database or Database(settings.database_path)
    database.initialize()

    jobs_repo = JobRepository(database)
    health_repo = HealthRepository(database)
    analytics = AnalyticsService(database)

    app = FastAPI(
        title="Job Intelligence Monitor API",
        version="1.0.0",
        description="Read API over the multi-source job intelligence database.",
    )

    @app.get("/health", tags=["system"])
    def health() -> dict:
        db_path = Path(settings.database_path)
        return {
            "status": "ok",
            "total_jobs": jobs_repo.count(),
            "jobs_today": jobs_repo.count_today(),
            "db_size_kb": round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0,
        }

    @app.get("/jobs", response_model=List[JobRecord], tags=["jobs"])
    def list_jobs(
        query: Optional[str] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_score: int = 0,
        remote_only: bool = False,
        limit: int = Query(default=50, ge=1, le=500),
    ) -> List[JobRecord]:
        return jobs_repo.list_jobs(
            search=query, source=source, category=category,
            min_score=min_score, remote_only=remote_only, limit=limit,
        )

    @app.get("/jobs/top", response_model=List[JobRecord], tags=["jobs"])
    def top_jobs(limit: int = Query(default=10, ge=1, le=100)) -> List[JobRecord]:
        return analytics.top_jobs(limit=limit)

    @app.get("/analytics/overview", tags=["analytics"])
    def overview() -> dict:
        return analytics.overview()

    @app.get("/analytics/sources", tags=["analytics"])
    def by_source() -> dict:
        return analytics.by_source()

    @app.get("/analytics/skills", tags=["analytics"])
    def skills(top: int = Query(default=15, ge=1, le=50)) -> list:
        return analytics.skill_frequency(top=top)

    @app.get("/sources/health", response_model=List[SourceHealth], tags=["system"])
    def sources_health() -> List[SourceHealth]:
        return health_repo.all()

    return app


# Module-level app for `uvicorn job_monitor.api.app:app`.
app = create_app()


def run() -> None:  # pragma: no cover - convenience runner
    import uvicorn

    uvicorn.run("job_monitor.api.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":  # pragma: no cover
    run()
