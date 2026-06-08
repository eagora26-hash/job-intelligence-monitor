"""Wellfound (formerly AngelList Talent) scraper — public job pages (best-effort).

Wellfound is a JavaScript-rendered, Cloudflare-protected site. This scraper extracts the
``__NEXT_DATA__`` JSON island that the public pages embed and walks it for job nodes. When
the page is blocked or the shape changes it returns an empty list rather than fabricating
data; enable ``USE_STEALTH_FALLBACK`` (Scrapling Playwright) for JS rendering where a browser
stack is available. Demo mode covers the dashboard when this source is empty.
"""

from __future__ import annotations

import json
from typing import Any, Iterator, List

from scrapling import Selector

from job_monitor.scrapers.base import BaseScraper, RawJob

LISTING_URLS = [
    "https://wellfound.com/role/r/software-engineer",
    "https://wellfound.com/role/r/python-developer",
]


class WellfoundScraper(BaseScraper):
    name = "wellfound"
    label = "Wellfound"
    base_url = "https://wellfound.com"

    def fetch_raw(self) -> List[RawJob]:
        jobs: List[RawJob] = []
        seen: set[str] = set()
        for url in LISTING_URLS:
            try:
                html = self.http.get_text(url)
            except Exception as exc:  # noqa: BLE001 - best-effort source
                self.logger.warning("Listing unavailable %s: %s", url, exc)
                continue
            for job in self.parse_html(html):
                key = job.get("url", "")
                if key and key not in seen:
                    seen.add(key)
                    jobs.append(job)
        if not jobs:
            self.logger.info("No public Wellfound listings parsed (expected when blocked).")
        return jobs

    @staticmethod
    def parse_html(html: str) -> List[RawJob]:
        """Extract jobs from the ``__NEXT_DATA__`` JSON island (best-effort traversal)."""
        if not html:
            return []
        selector = Selector(content=html)
        scripts = selector.css("script#__NEXT_DATA__")
        if not scripts:
            return []
        payload = _safe_json(str(scripts[0].text))
        if payload is None:
            return []

        jobs: List[RawJob] = []
        seen: set[str] = set()
        for node in _walk_job_nodes(payload):
            slug = node.get("slug") or node.get("id")
            title = node.get("title") or ""
            if not title:
                continue
            url = f"https://wellfound.com/jobs/{slug}" if slug else ""
            if url in seen:
                continue
            seen.add(url)
            company = ""
            startup = node.get("startup")
            if isinstance(startup, dict):
                company = startup.get("name", "")
            jobs.append(
                RawJob(
                    source="wellfound",
                    title=title,
                    company=company,
                    url=url,
                    description=node.get("description", ""),
                    posted_at=node.get("liveStartAt", "") or node.get("createdAt", ""),
                    location=_first_location(node),
                    tags=["wellfound"],
                    salary=node.get("salary", ""),
                )
            )
        return jobs


def _safe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _walk_job_nodes(payload: Any) -> Iterator[dict]:
    """Recursively yield dicts that look like job postings (have title + slug/id)."""
    if isinstance(payload, dict):
        looks_like_job = "title" in payload and ("slug" in payload or "id" in payload)
        if looks_like_job and ("startup" in payload or "jobType" in payload or "remote" in payload):
            yield payload
        for value in payload.values():
            yield from _walk_job_nodes(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _walk_job_nodes(item)


def _first_location(node: dict) -> str:
    locations = node.get("locationNames") or node.get("locations")
    if isinstance(locations, list) and locations:
        first = locations[0]
        if isinstance(first, dict):
            return first.get("name", "Remote")
        return str(first)
    return "Remote"
