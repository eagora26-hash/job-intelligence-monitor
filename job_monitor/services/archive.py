"""Archive service: move stale jobs out of the active DB to keep it lightweight.

Reuses the repository pattern — old jobs are upserted into a separate archive database and
removed from the active one. The archive uses the identical schema, so it remains fully
queryable (e.g. for historical analytics) without special handling.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from job_monitor.config import Settings, get_settings
from job_monitor.database import Database, JobRepository
from job_monitor.observability import get_logger

logger = get_logger("services.archive")


class ArchiveService:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.active = JobRepository(Database(self.settings.database_path))
        archive_db = Database(self.settings.archive_db_path)
        archive_db.initialize()
        self.archive = JobRepository(archive_db)

    def archive_older_than(self, days: int = 90) -> int:
        """Move jobs last seen more than ``days`` ago into the archive DB. Returns count moved."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        moved = 0
        for job in self.active.all_jobs():
            stamp = job.last_seen or job.scraped_at
            if stamp and stamp < cutoff:
                self.archive.upsert(job)
                self.active.delete(job.url)
                moved += 1
        if moved:
            logger.info("Archived %d stale job(s) older than %d days", moved, days)
        return moved

    def archive_count(self) -> int:
        return self.archive.count()
