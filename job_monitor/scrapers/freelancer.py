"""Freelancer scraper — uses the public active-projects JSON API.

Endpoint: ``/api/projects/0.1/projects/active``. We query a handful of relevant terms and
merge the results, de-duplicating by project URL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List

from job_monitor.scrapers.base import BaseScraper, RawJob

API_BASE = "https://www.freelancer.com/api/projects/0.1/projects/active/"
QUERIES = ["python", "web scraping", "automation", "data extraction"]
PROJECT_URL = "https://www.freelancer.com/projects/{seo_url}"


class FreelancerScraper(BaseScraper):
    name = "freelancer"
    label = "Freelancer"
    base_url = "https://www.freelancer.com"

    def fetch_raw(self) -> List[RawJob]:
        jobs: List[RawJob] = []
        seen: set[str] = set()
        for query in QUERIES:
            url = (
                f"{API_BASE}?query={query.replace(' ', '%20')}"
                "&limit=30&job_details=true&full_description=true&compact=true"
            )
            try:
                data = self.http.get_json(url)
            except Exception as exc:  # noqa: BLE001 - per-query isolation
                self.logger.warning("Query failed '%s': %s", query, exc)
                continue
            for job in self.parse_api(data):
                key = job.get("url", "")
                if key and key not in seen:
                    seen.add(key)
                    jobs.append(job)
        return jobs

    @staticmethod
    def parse_api(data: Any) -> List[RawJob]:
        """Parse a Freelancer active-projects API response into raw job dicts."""
        if not isinstance(data, dict):
            return []
        projects = (data.get("result") or {}).get("projects") or []
        jobs: List[RawJob] = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            seo_url = project.get("seo_url", "")
            jobs.append(
                RawJob(
                    source="freelancer",
                    title=project.get("title", ""),
                    company="",  # Freelancer posts are from individual clients, not companies
                    url=PROJECT_URL.format(seo_url=seo_url) if seo_url else "",
                    description=project.get("preview_description")
                    or project.get("description", ""),
                    posted_at=_epoch_to_iso(project.get("time_submitted")),
                    location="Remote",
                    tags=[j.get("name", "") for j in project.get("jobs", []) if j.get("name")],
                    salary=_format_budget(project.get("budget"), project.get("currency")),
                )
            )
        return jobs


def _epoch_to_iso(epoch: Any) -> str:
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return ""


def _format_budget(budget: Any, currency: Any) -> str:
    if not isinstance(budget, dict):
        return ""
    code = (currency or {}).get("code", "") if isinstance(currency, dict) else ""
    lo, hi = budget.get("minimum"), budget.get("maximum")
    if lo and hi:
        return f"{code} {lo}-{hi}".strip()
    if hi:
        return f"{code} up to {hi}".strip()
    if lo:
        return f"{code} from {lo}".strip()
    return ""
