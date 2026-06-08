"""Convert loose :class:`RawJob` payloads into validated :class:`JobRecord` objects.

This is the contract boundary: after normalization, the rest of the system never sees a
source-specific shape. Responsibilities: clean HTML out of text, parse heterogeneous date
formats, tidy tags, infer the remote flag, and drop unusable records (no URL/title).
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable, List, Optional

from w3lib.html import remove_tags, replace_entities

from job_monitor.models import JobRecord
from job_monitor.observability import get_logger
from job_monitor.scrapers.base import RawJob

logger = get_logger("normalizers")

# Sources whose postings are remote by definition.
_REMOTE_BY_DEFAULT = {"remoteok", "weworkremotely"}
_REMOTE_HINTS = ("remote", "worldwide", "anywhere", "distributed")
_MAX_DESCRIPTION = 5000


class Normalizer:
    """Stateless normalizer (a class for DI/testability and future per-source hooks)."""

    def normalize_many(self, raw_jobs: Iterable[RawJob]) -> List[JobRecord]:
        records: List[JobRecord] = []
        for raw in raw_jobs:
            record = self.normalize(raw)
            if record is not None:
                records.append(record)
        return records

    def normalize(self, raw: RawJob) -> Optional[JobRecord]:
        """Return a :class:`JobRecord`, or ``None`` if the payload is unusable."""
        url = (raw.get("url") or "").strip()
        title = _clean_text(raw.get("title", ""))
        if not url or not title:
            return None

        source = (raw.get("source") or "unknown").strip()
        description = _clean_html(raw.get("description", ""))
        location = _clean_text(raw.get("location", ""))
        tags = _clean_tags(raw.get("tags", []))

        return JobRecord(
            source=source,
            url=url,
            title=title,
            company=_clean_text(raw.get("company", "")),
            description=description,
            location=location,
            salary=_clean_text(raw.get("salary", "")),
            tags=tags,
            posted_at=_parse_date(raw.get("posted_at", "")),
            remote=_infer_remote(source, location, title, tags),
            scraped_at=datetime.now(timezone.utc),
        )


# --------------------------------------------------------------------------- helpers
def _clean_text(value: str) -> str:
    return " ".join((value or "").split()).strip()


def _clean_html(value: str) -> str:
    if not value:
        return ""
    text = replace_entities(remove_tags(value))
    text = " ".join(text.split()).strip()
    return text[:_MAX_DESCRIPTION]


def _clean_tags(tags: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for tag in tags or []:
        clean = _clean_text(str(tag))
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            out.append(clean)
    return out


def _infer_remote(source: str, location: str, title: str, tags: List[str]) -> bool:
    if source in _REMOTE_BY_DEFAULT:
        return True
    haystack = " ".join([location, title, " ".join(tags)]).lower()
    return any(hint in haystack for hint in _REMOTE_HINTS)


def _parse_date(value: str) -> Optional[datetime]:
    """Best-effort parse of ISO-8601, RFC-822 (RSS), or epoch-seconds date strings."""
    if not value:
        return None
    value = str(value).strip()

    # ISO-8601 (RemoteOK, Freelancer-derived, Wellfound).
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return _aware(dt)
    except ValueError:
        pass

    # RFC-822 (RSS pubDate, e.g. "Mon, 01 Jan 2024 12:00:00 +0000").
    try:
        return _aware(parsedate_to_datetime(value))
    except (TypeError, ValueError, IndexError):
        pass

    # Epoch seconds.
    if value.isdigit():
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        except (ValueError, OSError):
            pass

    return None


def _aware(dt: datetime) -> datetime:
    """Ensure a timezone-aware UTC datetime."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
