"""Resume/state persistence (``data/state.json``).

Lets the monitor recover context after a restart: when it last ran, whether the last run
succeeded, and per-source status. Written atomically after every run.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field


class SourceState(BaseModel):
    last_status: str = "unknown"  # "success" | "failure" | "unknown"
    last_run: Optional[datetime] = None
    last_jobs_found: int = 0
    last_error: str = ""


class MonitorState(BaseModel):
    """Serializable monitor state persisted between runs."""

    last_run: Optional[datetime] = None
    last_successful_run: Optional[datetime] = None
    total_runs: int = 0
    source_status: Dict[str, SourceState] = Field(default_factory=dict)


class StateStore:
    """Loads/saves :class:`MonitorState` as JSON, atomically."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> MonitorState:
        if not self.path.exists():
            return MonitorState()
        try:
            return MonitorState.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return MonitorState()

    def save(self, state: MonitorState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = state.model_dump_json(indent=2)
        # Atomic write: temp file in the same dir, then replace.
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(data)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)
