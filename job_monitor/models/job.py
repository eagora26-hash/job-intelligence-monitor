"""The canonical :class:`JobRecord` — the single shape every layer agrees on.

Scrapers emit loose ``dict`` payloads; the normalizer converts those into ``JobRecord``
instances, and from that point on no source-specific structure exists anywhere in the
system. Enrichment fields (score/category/skills/quality) and monitor metadata
(first_seen/last_seen/notified) live on the same model but default to "unenriched" so a
freshly-normalized record is always valid.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobRecord(BaseModel):
    """A normalized job posting plus its enrichment and monitoring metadata."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    # --- identity / provenance ---
    source: str = Field(..., description="Canonical source key, e.g. 'remoteok'.")
    url: str = Field(..., description="Canonical job URL. Unique key for deduplication.")

    # --- core posting data ---
    title: str = ""
    company: str = ""
    description: str = ""
    location: str = ""
    salary: str = ""
    tags: List[str] = Field(default_factory=list)
    posted_at: Optional[datetime] = None

    # --- enrichment (populated by the pipeline; safe defaults) ---
    score: int = 0
    category: str = ""
    skills: List[str] = Field(default_factory=list)
    quality_score: int = 0
    remote: bool = False

    # --- monitor metadata (managed by the repository) ---
    scraped_at: datetime = Field(default_factory=_utcnow)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    notified: bool = False
    content_hash: str = ""

    @field_validator("tags", "skills", mode="before")
    @classmethod
    def _coerce_list(cls, value: object) -> object:
        """Accept ``None`` or a comma/pipe-separated string for list fields."""
        if value is None:
            return []
        if isinstance(value, str):
            raw = value.replace("|", ",")
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value

    @property
    def searchable_text(self) -> str:
        """Lowercased blob of the human-readable fields, used by enrichment/search."""
        parts = [self.title, self.company, self.description, self.location, " ".join(self.tags)]
        return " ".join(p for p in parts if p).lower()

    def compute_content_hash(self) -> str:
        """Stable hash of the volatile fields used for change detection.

        Excludes timestamps and enrichment so the hash changes only when the *posting*
        meaningfully changes (title, company, description, salary, location).
        """
        basis = "||".join([
            self.title.strip(),
            self.company.strip(),
            self.description.strip(),
            self.salary.strip(),
            self.location.strip(),
        ])
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    def with_content_hash(self) -> "JobRecord":
        """Return a copy with ``content_hash`` populated (chainable in the pipeline)."""
        return self.model_copy(update={"content_hash": self.compute_content_hash()})
