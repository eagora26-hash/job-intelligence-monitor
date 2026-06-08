"""Acquisition layer: per-source scrapers built on the vendored Scrapling engine."""

from job_monitor.scrapers.base import BaseScraper, RawJob, ScrapeResult
from job_monitor.scrapers.http import HttpClient, ScraperHTTPError
from job_monitor.scrapers.registry import (
    SCRAPER_CLASSES,
    build_scrapers,
    get_scraper_class,
)

__all__ = [
    "BaseScraper",
    "RawJob",
    "ScrapeResult",
    "HttpClient",
    "ScraperHTTPError",
    "SCRAPER_CLASSES",
    "build_scrapers",
    "get_scraper_class",
]
