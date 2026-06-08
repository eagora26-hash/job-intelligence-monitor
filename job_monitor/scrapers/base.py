"""Scraper base class and shared data contracts.

Every source scraper subclasses :class:`BaseScraper` and implements :meth:`fetch_raw`,
returning a list of loose :class:`RawJob` dicts (the schema from ``instructions.md``). The
public :meth:`scrape` method wraps that with timing + total error isolation so a single
failing source can never halt a run — it returns a :class:`ScrapeResult` instead of raising.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, TypedDict

from job_monitor.observability import get_logger
from job_monitor.scrapers.http import HttpClient


class RawJob(TypedDict, total=False):
    """Loose, source-agnostic payload emitted by scrapers (pre-normalization)."""

    source: str
    title: str
    company: str
    url: str
    description: str
    posted_at: str
    location: str
    tags: List[str]
    salary: str
    scraped_at: str


@dataclass
class ScrapeResult:
    """Outcome of one source scrape: the raw jobs plus health/timing metadata."""

    source: str
    raw_jobs: List[RawJob] = field(default_factory=list)
    success: bool = True
    error: str = ""
    duration_ms: float = 0.0

    @property
    def count(self) -> int:
        return len(self.raw_jobs)


class BaseScraper(ABC):
    """Abstract source scraper. Subclasses set :attr:`name` and implement :meth:`fetch_raw`."""

    #: Canonical, stable source key (matches Settings.enabled_sources keys).
    name: str = "base"
    #: Human-friendly label for UI/notifications.
    label: str = "Base"
    #: Source homepage (used in docs/UI).
    base_url: str = ""

    def __init__(self, http: Optional[HttpClient] = None) -> None:
        self.http = http or HttpClient()
        self.logger = get_logger(f"scrapers.{self.name}")

    @abstractmethod
    def fetch_raw(self) -> List[RawJob]:
        """Fetch and parse the source, returning raw job dicts. May raise; ``scrape`` guards it."""
        raise NotImplementedError

    def scrape(self) -> ScrapeResult:
        """Run :meth:`fetch_raw` with timing and full error isolation."""
        start = time.perf_counter()
        try:
            raw = self.fetch_raw()
            duration = (time.perf_counter() - start) * 1000
            for job in raw:
                job.setdefault("source", self.name)
            self.logger.info("Scraped %d jobs in %.0f ms", len(raw), duration)
            return ScrapeResult(self.name, raw_jobs=raw, success=True, duration_ms=duration)
        except Exception as exc:  # noqa: BLE001 - isolate per-source failures
            duration = (time.perf_counter() - start) * 1000
            self.logger.error("Scrape failed: %s", exc)
            return ScrapeResult(
                self.name, raw_jobs=[], success=False, error=str(exc), duration_ms=duration
            )
