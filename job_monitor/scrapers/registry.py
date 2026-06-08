"""Scraper registry / factory.

Maps canonical source keys to scraper classes and builds the set of *enabled* scrapers from
configuration. Adding a new source is a one-line change here — nothing else needs editing.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from job_monitor.config import Settings, get_settings
from job_monitor.scrapers.base import BaseScraper
from job_monitor.scrapers.fiverr import FiverrScraper
from job_monitor.scrapers.freelancer import FreelancerScraper
from job_monitor.scrapers.http import HttpClient
from job_monitor.scrapers.remoteok import RemoteOKScraper
from job_monitor.scrapers.weworkremotely import WeWorkRemotelyScraper
from job_monitor.scrapers.wellfound import WellfoundScraper

SCRAPER_CLASSES: Dict[str, Type[BaseScraper]] = {
    RemoteOKScraper.name: RemoteOKScraper,
    WeWorkRemotelyScraper.name: WeWorkRemotelyScraper,
    FreelancerScraper.name: FreelancerScraper,
    FiverrScraper.name: FiverrScraper,
    WellfoundScraper.name: WellfoundScraper,
}


def get_scraper_class(name: str) -> Type[BaseScraper]:
    """Return the scraper class for a source key, or raise ``KeyError``."""
    return SCRAPER_CLASSES[name]


def build_http_client(settings: Settings) -> HttpClient:
    """Construct an :class:`HttpClient` from settings."""
    return HttpClient(
        timeout=settings.request_timeout,
        retries=settings.request_retries,
        impersonate=settings.http_impersonate,
        use_stealth_fallback=settings.use_stealth_fallback,
    )


def build_scrapers(
    settings: Optional[Settings] = None,
    http: Optional[HttpClient] = None,
) -> List[BaseScraper]:
    """Instantiate every *enabled* scraper, sharing one HTTP client."""
    settings = settings or get_settings()
    http = http or build_http_client(settings)
    scrapers: List[BaseScraper] = []
    for name, enabled in settings.enabled_sources().items():
        if enabled and name in SCRAPER_CLASSES:
            scrapers.append(SCRAPER_CLASSES[name](http=http))
    return scrapers
