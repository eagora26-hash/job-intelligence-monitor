"""Export jobs to CSV / Excel (and a future-ready interface for JSON / Google Sheets).

``JobExporter`` wraps a list of :class:`JobRecord` and renders it to a pandas DataFrame, then
to files or in-memory bytes (the latter powering the dashboard's download buttons).
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import List, Sequence

import pandas as pd

from job_monitor.models import JobRecord

# Stable, human-friendly column order for exports.
EXPORT_COLUMNS = [
    "source", "title", "company", "category", "score", "quality_score", "remote",
    "location", "salary", "skills", "tags", "posted_at", "first_seen", "url",
]


class JobExporter:
    """Renders jobs to tabular exports."""

    def __init__(self, jobs: Sequence[JobRecord]) -> None:
        self.jobs = list(jobs)

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for job in self.jobs:
            rows.append(
                {
                    "source": job.source,
                    "title": job.title,
                    "company": job.company,
                    "category": job.category,
                    "score": job.score,
                    "quality_score": job.quality_score,
                    "remote": job.remote,
                    "location": job.location,
                    "salary": job.salary,
                    "skills": ", ".join(job.skills),
                    "tags": ", ".join(job.tags),
                    "posted_at": job.posted_at.isoformat() if job.posted_at else "",
                    "first_seen": job.first_seen.isoformat() if job.first_seen else "",
                    "url": job.url,
                }
            )
        frame = pd.DataFrame(rows, columns=EXPORT_COLUMNS)
        return frame

    # --- file outputs ---
    def to_csv(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(path, index=False)
        return path

    def to_excel(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_excel(path, index=False, sheet_name="Jobs", engine="openpyxl")
        return path

    def to_json(self, path: Path | str) -> Path:
        """JSON export (future-ready; mirrors CSV/Excel surface)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_dataframe().to_json(orient="records", indent=2), encoding="utf-8")
        return path

    # --- in-memory outputs (dashboard download buttons) ---
    def to_csv_bytes(self) -> bytes:
        return self.to_dataframe().to_csv(index=False).encode("utf-8")

    def to_excel_bytes(self) -> bytes:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            self.to_dataframe().to_excel(writer, index=False, sheet_name="Jobs")
        return buffer.getvalue()

    def to_json_bytes(self) -> bytes:
        return self.to_dataframe().to_json(orient="records", indent=2).encode("utf-8")
