"""Repository pattern over SQLite.

Every database read/write goes through these repositories; no raw SQL or row dict leaks into
services, the runner, or the UI. Repositories translate between :mod:`job_monitor.models`
objects and table rows, and own deduplication + change detection.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Iterable, Optional, Sequence

from job_monitor.database.connection import Database
from job_monitor.models import DailySnapshot, JobChange, JobRecord, SourceHealth

# Fields whose change is meaningful enough to record in job_history.
_TRACKED_FIELDS = ("title", "company", "description", "salary", "location")


# --------------------------------------------------------------------------- (de)serialize
def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _job_to_params(job: JobRecord) -> dict[str, Any]:
    return {
        "source": job.source,
        "title": job.title,
        "company": job.company,
        "url": job.url,
        "description": job.description,
        "posted_at": _iso(job.posted_at),
        "location": job.location,
        "salary": job.salary,
        "tags": json.dumps(job.tags),
        "score": job.score,
        "category": job.category,
        "skills": json.dumps(job.skills),
        "quality_score": job.quality_score,
        "remote": int(job.remote),
        "content_hash": job.content_hash or job.compute_content_hash(),
        "first_seen": _iso(job.first_seen or _utcnow()),
        "last_seen": _iso(job.last_seen or _utcnow()),
        "notified": int(job.notified),
    }


def _row_to_job(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        source=row["source"],
        title=row["title"],
        company=row["company"],
        url=row["url"],
        description=row["description"],
        posted_at=_parse_dt(row["posted_at"]),
        location=row["location"],
        salary=row["salary"],
        tags=json.loads(row["tags"] or "[]"),
        score=row["score"],
        category=row["category"],
        skills=json.loads(row["skills"] or "[]"),
        quality_score=row["quality_score"],
        remote=bool(row["remote"]),
        content_hash=row["content_hash"],
        first_seen=_parse_dt(row["first_seen"]),
        last_seen=_parse_dt(row["last_seen"]),
        notified=bool(row["notified"]),
    )


# --------------------------------------------------------------------------- upsert result
class UpsertStatus(str, Enum):
    NEW = "new"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass
class UpsertResult:
    """Outcome of persisting one job, including any detected field changes."""

    status: UpsertStatus
    job: JobRecord
    changes: list[JobChange] = field(default_factory=list)

    @property
    def is_new(self) -> bool:
        return self.status is UpsertStatus.NEW


# --------------------------------------------------------------------------- jobs
class JobRepository:
    """CRUD + querying for jobs, with deduplication and change detection."""

    _COLUMNS = (
        "source, title, company, url, description, posted_at, location, salary, tags, "
        "score, category, skills, quality_score, remote, content_hash, first_seen, "
        "last_seen, notified"
    )

    def __init__(self, db: Database) -> None:
        self.db = db

    # -- writes --
    def upsert(self, job: JobRecord) -> UpsertResult:
        """Insert a new job or update an existing one (keyed on ``url``).

        Returns an :class:`UpsertResult` describing whether the job was new, updated
        (content changed — field changes recorded in ``job_history``), or unchanged.
        """
        job = job.with_content_hash()
        now = _utcnow()
        with self.db.connection() as conn:
            existing = conn.execute(
                "SELECT * FROM jobs WHERE url = ?", (job.url,)
            ).fetchone()

            if existing is None:
                job.first_seen = now
                job.last_seen = now
                params = _job_to_params(job)
                placeholders = ", ".join(f":{c.strip()}" for c in self._COLUMNS.split(","))
                conn.execute(
                    f"INSERT INTO jobs ({self._COLUMNS}) VALUES ({placeholders})", params
                )
                return UpsertResult(UpsertStatus.NEW, job)

            existing_job = _row_to_job(existing)
            changes = self._detect_changes(existing_job, job)
            # Always refresh enrichment + last_seen; preserve original first_seen & notified.
            job.first_seen = existing_job.first_seen or now
            job.last_seen = now
            job.notified = existing_job.notified
            params = _job_to_params(job)
            set_clause = ", ".join(
                f"{c.strip()} = :{c.strip()}"
                for c in self._COLUMNS.split(",")
                if c.strip() not in ("url", "first_seen", "notified")
            )
            conn.execute(f"UPDATE jobs SET {set_clause} WHERE url = :url", params)

            if changes:
                conn.executemany(
                    "INSERT INTO job_history (job_url, field, old_value, new_value, detected_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    [(c.job_url, c.field, c.old_value, c.new_value, _iso(c.detected_at))
                     for c in changes],
                )
                return UpsertResult(UpsertStatus.UPDATED, job, changes)
            return UpsertResult(UpsertStatus.UNCHANGED, job)

    @staticmethod
    def _detect_changes(old: JobRecord, new: JobRecord) -> list[JobChange]:
        if old.content_hash == new.compute_content_hash():
            return []
        changes: list[JobChange] = []
        for fld in _TRACKED_FIELDS:
            old_val = str(getattr(old, fld) or "")
            new_val = str(getattr(new, fld) or "")
            if old_val != new_val:
                changes.append(
                    JobChange(job_url=new.url, field=fld, old_value=old_val, new_value=new_val)
                )
        return changes

    def delete(self, url: str) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM jobs WHERE url = ?", (url,))

    def seed(self, job: JobRecord) -> None:
        """Insert a job honoring its provided ``first_seen``/``last_seen``/``notified``.

        Used only by the demo-data generator to create historically-spread records (the normal
        :meth:`upsert` always stamps ``now``). Ignored if the URL already exists.
        """
        job = job.with_content_hash()
        params = _job_to_params(job)
        placeholders = ", ".join(f":{c.strip()}" for c in self._COLUMNS.split(","))
        with self.db.connection() as conn:
            conn.execute(
                f"INSERT OR IGNORE INTO jobs ({self._COLUMNS}) VALUES ({placeholders})", params
            )

    def mark_notified(self, urls: Iterable[str]) -> None:
        urls = list(urls)
        if not urls:
            return
        with self.db.connection() as conn:
            conn.executemany("UPDATE jobs SET notified = 1 WHERE url = ?", [(u,) for u in urls])

    # -- reads --
    def get(self, url: str) -> Optional[JobRecord]:
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE url = ?", (url,)).fetchone()
        return _row_to_job(row) if row else None

    def unnotified(self, min_score: int = 0) -> list[JobRecord]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE notified = 0 AND score >= ? ORDER BY score DESC",
                (min_score,),
            ).fetchall()
        return [_row_to_job(r) for r in rows]

    def list_jobs(
        self,
        *,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_score: int = 0,
        remote_only: bool = False,
        search: Optional[str] = None,
        since: Optional[datetime] = None,
        order_by: str = "score",
        limit: Optional[int] = None,
    ) -> list[JobRecord]:
        """Flexible, parameterized query backing the dashboard search/filter UI."""
        clauses: list[str] = ["1=1"]
        params: list[Any] = []
        if source:
            clauses.append("source = ?")
            params.append(source)
        if category:
            clauses.append("category = ?")
            params.append(category)
        if min_score:
            clauses.append("score >= ?")
            params.append(min_score)
        if remote_only:
            clauses.append("remote = 1")
        if since:
            clauses.append("first_seen >= ?")
            params.append(_iso(since))
        if search:
            clauses.append(
                "(LOWER(title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(description) LIKE ?"
                " OR LOWER(skills) LIKE ?)"
            )
            like = f"%{search.lower()}%"
            params.extend([like, like, like, like])

        order_column = {
            "score": "score DESC",
            "recent": "first_seen DESC",
            "quality": "quality_score DESC",
        }.get(order_by, "score DESC")

        sql = f"SELECT * FROM jobs WHERE {' AND '.join(clauses)} ORDER BY {order_column}"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        with self.db.connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_job(r) for r in rows]

    def all_jobs(self) -> list[JobRecord]:
        return self.list_jobs(order_by="recent")

    # -- aggregates --
    def count(self) -> int:
        with self.db.connection() as conn:
            return int(conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()["n"])

    def count_today(self) -> int:
        start = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self.db.connection() as conn:
            return int(
                conn.execute(
                    "SELECT COUNT(*) AS n FROM jobs WHERE substr(first_seen, 1, 10) = ?",
                    (start,),
                ).fetchone()["n"]
            )

    def count_by_source(self) -> dict[str, int]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT source, COUNT(*) AS n FROM jobs GROUP BY source ORDER BY n DESC"
            ).fetchall()
        return {r["source"]: r["n"] for r in rows}

    def count_by_category(self) -> dict[str, int]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT category, COUNT(*) AS n FROM jobs WHERE category != '' "
                "GROUP BY category ORDER BY n DESC"
            ).fetchall()
        return {r["category"]: r["n"] for r in rows}

    def count_by_day(self, days: int = 30) -> dict[str, int]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT substr(first_seen, 1, 10) AS day, COUNT(*) AS n FROM jobs "
                "GROUP BY day ORDER BY day DESC LIMIT ?",
                (days,),
            ).fetchall()
        return {r["day"]: r["n"] for r in reversed(rows)}

    def avg_score(self) -> float:
        with self.db.connection() as conn:
            row = conn.execute("SELECT AVG(score) AS a FROM jobs").fetchone()
        return float(row["a"]) if row and row["a"] is not None else 0.0

    def notified_count(self) -> int:
        with self.db.connection() as conn:
            return int(
                conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE notified = 1").fetchone()["n"]
            )

    def distinct_skills(self) -> set[str]:
        """Union of skills across all jobs (skills are stored as a JSON array per row)."""
        skills: set[str] = set()
        with self.db.connection() as conn:
            rows = conn.execute("SELECT skills FROM jobs WHERE skills != '[]'").fetchall()
        for row in rows:
            try:
                skills.update(json.loads(row["skills"]))
            except (json.JSONDecodeError, TypeError):
                continue
        return skills

    def distinct_sources(self) -> list[str]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT DISTINCT source FROM jobs ORDER BY source").fetchall()
        return [r["source"] for r in rows]

    def distinct_categories(self) -> list[str]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM jobs WHERE category != '' ORDER BY category"
            ).fetchall()
        return [r["category"] for r in rows]


# --------------------------------------------------------------------------- health
class HealthRepository:
    """Upsert/read rolling per-source health."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def get(self, source: str) -> SourceHealth:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM source_health WHERE source = ?", (source,)
            ).fetchone()
        if row is None:
            return SourceHealth(source=source)
        return SourceHealth(
            source=row["source"],
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            last_success=_parse_dt(row["last_success"]),
            last_failure=_parse_dt(row["last_failure"]),
            last_error=row["last_error"],
            avg_response_ms=row["avg_response_ms"],
            last_jobs_found=row["last_jobs_found"],
        )

    def save(self, health: SourceHealth) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO source_health (source, success_count, failure_count, last_success,"
                " last_failure, last_error, avg_response_ms, last_jobs_found) "
                "VALUES (:source, :success_count, :failure_count, :last_success, :last_failure,"
                " :last_error, :avg_response_ms, :last_jobs_found) "
                "ON CONFLICT(source) DO UPDATE SET success_count=excluded.success_count, "
                "failure_count=excluded.failure_count, last_success=excluded.last_success, "
                "last_failure=excluded.last_failure, last_error=excluded.last_error, "
                "avg_response_ms=excluded.avg_response_ms, last_jobs_found=excluded.last_jobs_found",
                {
                    "source": health.source,
                    "success_count": health.success_count,
                    "failure_count": health.failure_count,
                    "last_success": _iso(health.last_success),
                    "last_failure": _iso(health.last_failure),
                    "last_error": health.last_error,
                    "avg_response_ms": health.avg_response_ms,
                    "last_jobs_found": health.last_jobs_found,
                },
            )

    def all(self) -> list[SourceHealth]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT source FROM source_health ORDER BY source").fetchall()
        return [self.get(r["source"]) for r in rows]


# --------------------------------------------------------------------------- snapshots
class SnapshotRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def upsert(self, snapshot: DailySnapshot) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO daily_snapshots (snapshot_date, total_jobs, new_jobs, source_count,"
                " keyword_count, notified_count, avg_score) VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(snapshot_date) DO UPDATE SET total_jobs=excluded.total_jobs, "
                "new_jobs=excluded.new_jobs, source_count=excluded.source_count, "
                "keyword_count=excluded.keyword_count, notified_count=excluded.notified_count, "
                "avg_score=excluded.avg_score",
                (
                    snapshot.snapshot_date.isoformat(),
                    snapshot.total_jobs,
                    snapshot.new_jobs,
                    snapshot.source_count,
                    snapshot.keyword_count,
                    snapshot.notified_count,
                    snapshot.avg_score,
                ),
            )

    def all(self) -> list[DailySnapshot]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM daily_snapshots ORDER BY snapshot_date"
            ).fetchall()
        return [
            DailySnapshot(
                snapshot_date=date.fromisoformat(r["snapshot_date"]),
                total_jobs=r["total_jobs"],
                new_jobs=r["new_jobs"],
                source_count=r["source_count"],
                keyword_count=r["keyword_count"],
                notified_count=r["notified_count"],
                avg_score=r["avg_score"],
            )
            for r in rows
        ]


# --------------------------------------------------------------------------- history
class HistoryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def for_url(self, url: str) -> list[JobChange]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM job_history WHERE job_url = ? ORDER BY detected_at DESC", (url,)
            ).fetchall()
        return [
            JobChange(
                job_url=r["job_url"],
                field=r["field"],
                old_value=r["old_value"],
                new_value=r["new_value"],
                detected_at=_parse_dt(r["detected_at"]) or _utcnow(),
            )
            for r in rows
        ]

    def recent(self, limit: int = 50) -> list[JobChange]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM job_history ORDER BY detected_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            JobChange(
                job_url=r["job_url"],
                field=r["field"],
                old_value=r["old_value"],
                new_value=r["new_value"],
                detected_at=_parse_dt(r["detected_at"]) or _utcnow(),
            )
            for r in rows
        ]
