"""Persistence layer: SQLite connection + repository pattern (no SQL leaks past here)."""

from job_monitor.database.connection import Database
from job_monitor.database.repository import (
    HealthRepository,
    HistoryRepository,
    JobRepository,
    SnapshotRepository,
    UpsertResult,
    UpsertStatus,
)

__all__ = [
    "Database",
    "JobRepository",
    "HealthRepository",
    "SnapshotRepository",
    "HistoryRepository",
    "UpsertResult",
    "UpsertStatus",
]
