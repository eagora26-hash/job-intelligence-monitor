"""We Work Remotely scraper — uses the public per-category RSS feeds.

RSS is parsed with the stdlib XML parser rather than the HTML ``Selector`` because HTML
parsing treats ``<link>`` as a void element and would drop the job URL. Item titles follow
the ``"Company: Position"`` convention, which we split apart.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

from job_monitor.scrapers.base import BaseScraper, RawJob

# A focused set of category feeds relevant to the monitored keywords.
FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
]


class WeWorkRemotelyScraper(BaseScraper):
    name = "weworkremotely"
    label = "We Work Remotely"
    base_url = "https://weworkremotely.com"

    def fetch_raw(self) -> List[RawJob]:
        jobs: List[RawJob] = []
        seen: set[str] = set()
        for feed in FEEDS:
            try:
                raw_bytes = self.http.get_bytes(feed)
            except Exception as exc:  # noqa: BLE001 - one feed failing shouldn't kill the source
                self.logger.warning("Feed failed %s: %s", feed, exc)
                continue
            for job in self.parse_rss(raw_bytes):
                url = job.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    jobs.append(job)
        return jobs

    @staticmethod
    def parse_rss(xml_bytes: bytes) -> List[RawJob]:
        """Parse a WWR RSS feed body into raw job dicts."""
        jobs: List[RawJob] = []
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            return []
        for item in root.iter("item"):
            raw_title = (item.findtext("title") or "").strip()
            company, _, title = raw_title.partition(": ")
            if not title:  # no colon -> treat whole string as the title
                company, title = "", raw_title
            region = item.findtext("region") or ""
            jobs.append(
                RawJob(
                    source="weworkremotely",
                    title=title.strip(),
                    company=company.strip(),
                    url=(item.findtext("link") or "").strip(),
                    description=(item.findtext("description") or "").strip(),
                    posted_at=(item.findtext("pubDate") or "").strip(),
                    location=region.strip() or "Remote",
                    tags=[c.text.strip() for c in item.findall("category") if c.text],
                    salary="",
                )
            )
        return jobs
