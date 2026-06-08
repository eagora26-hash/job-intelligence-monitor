"""Database + configuration backup service with retention.

Creates a consistent SQLite backup (via the online backup API) plus a non-secret config
snapshot, timestamped under ``backup/``, and prunes backups older than the retention window.
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from job_monitor.config import Settings, get_settings
from job_monitor.observability import get_logger

logger = get_logger("services.backup")

# Settings fields that are safe to snapshot (never back up secrets).
_SAFE_CONFIG_FIELDS = (
    "polling_interval", "max_workers", "request_timeout", "request_retries",
    "http_impersonate", "notify_min_score",
)


class BackupService:
    def __init__(self, settings: Optional[Settings] = None, retention_days: int = 30) -> None:
        self.settings = settings or get_settings()
        self.retention_days = retention_days

    def create_backup(self) -> Optional[Path]:
        """Create a timestamped DB + config backup. Returns the DB backup path (or None)."""
        db_path = self.settings.database_path
        if not db_path.exists():
            logger.info("No database to back up yet at %s", db_path)
            return None

        self.settings.backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target = self.settings.backup_dir / f"jobs_{stamp}.db"

        source = sqlite3.connect(str(db_path))
        try:
            dest = sqlite3.connect(str(target))
            try:
                source.backup(dest)  # consistent online backup
            finally:
                dest.close()
        finally:
            source.close()

        config_snapshot = {
            field: getattr(self.settings, field) for field in _SAFE_CONFIG_FIELDS
        }
        config_snapshot["enabled_sources"] = self.settings.enabled_sources()
        (self.settings.backup_dir / f"config_{stamp}.json").write_text(
            json.dumps(config_snapshot, indent=2, default=str), encoding="utf-8"
        )

        logger.info("Backup created: %s", target.name)
        self.prune()
        return target

    def prune(self) -> int:
        """Delete backups older than the retention window. Returns count removed."""
        if not self.settings.backup_dir.exists():
            return 0
        cutoff = time.time() - self.retention_days * 86400
        removed = 0
        for path in self.settings.backup_dir.iterdir():
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        if removed:
            logger.info("Pruned %d expired backup file(s)", removed)
        return removed

    def list_backups(self) -> List[Path]:
        if not self.settings.backup_dir.exists():
            return []
        return sorted(self.settings.backup_dir.glob("jobs_*.db"))
