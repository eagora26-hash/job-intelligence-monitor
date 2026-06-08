"""RemoteOK scraper — uses the public JSON API (https://remoteok.com/api).

The API returns a JSON array whose first element is a legal/metadata notice; the rest are
job objects. This is the most reliable of the five sources, so it doubles as the reference
implementation for the scraper contract.
"""

from __future__ import annotations

from typing import Any, List

from job_monitor.scrapers.base import BaseScraper, RawJob

API_URL = "https://remoteok.com/api"


class RemoteOKScraper(BaseScraper):
    name = "remoteok"
    label = "RemoteOK"
    base_url = "https://remoteok.com"

    def fetch_raw(self) -> List[RawJob]:
        data = self.http.get_json(API_URL)
        return self.parse_api(data)

    @staticmethod
    def parse_api(data: Any) -> List[RawJob]:
        """Convert the RemoteOK API payload into raw job dicts."""
        if not isinstance(data, list):
            return []
        jobs: List[RawJob] = []
        for item in data:
            if not isinstance(item, dict) or item.get("legal") or not item.get("position"):
                continue  # skip the leading legal notice / malformed entries
            jobs.append(
                RawJob(
                    source="remoteok",
                    title=item.get("position", ""),
                    company=item.get("company", ""),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    posted_at=item.get("date", ""),
                    location=item.get("location") or "Worldwide",
                    tags=[str(t) for t in item.get("tags", []) if t],
                    salary=_format_salary(item.get("salary_min"), item.get("salary_max")),
                )
            )
        return jobs


def _format_salary(minimum: Any, maximum: Any) -> str:
    try:
        lo = int(minimum) if minimum else 0
        hi = int(maximum) if maximum else 0
    except (TypeError, ValueError):
        return ""
    if lo and hi:
        return f"${lo:,} - ${hi:,}"
    if hi:
        return f"Up to ${hi:,}"
    if lo:
        return f"From ${lo:,}"
    return ""
