"""SQLite connection management and schema initialization.

A :class:`Database` is a thin, thread-safe handle around a SQLite file. It hands out
short-lived connections (one per unit of work) which is the simplest correct model for the
concurrent runner — SQLite connections are not shareable across threads, and WAL mode keeps
concurrent readers/writers fast.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


class Database:
    """Owns a SQLite file path and produces configured connections."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        """Open a configured connection (row factory + WAL + foreign keys)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path), timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context-managed connection that commits on success and always closes."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Create all tables/indexes from ``schema.sql`` (idempotent)."""
        schema = _SCHEMA_PATH.read_text(encoding="utf-8")
        with self.connection() as conn:
            conn.executescript(schema)

    def size_bytes(self) -> int:
        """Return the database file size in bytes (0 if it does not exist yet)."""
        return self.path.stat().st_size if self.path.exists() else 0
