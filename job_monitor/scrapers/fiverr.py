"""Fiverr scraper — public listing pages only (best-effort).

Fiverr exposes no public jobs/buyer-requests API and aggressively blocks automated traffic,
so this scraper is intentionally *best-effort and honest*: it parses the ``ld+json``
``ItemList`` that public category pages embed, and returns an empty list (rather than
fabricating data) when the page is unavailable or blocked. The demo-data generator covers
the dashboard when this source yields nothing. An optional Scrapling stealth fallback can be
enabled via ``USE_STEALTH_FALLBACK`` for environments with a browser stack.
"""

from __future__ import annotations

import json
from typing import Any, List

from scrapling import Selector

from job_monitor.scrapers.base import BaseScraper, RawJob

# Public category pages that embed ld+json structured data.
LISTING_URLS = [
    "https://www.fiverr.com/categories/programming-tech/data-processing",
    "https://www.fiverr.com/categories/programming-tech/web-programming",
]


class FiverrScraper(BaseScraper):
    name = "fiverr"
    label = "Fiverr"
    base_url = "https://www.fiverr.com"

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
            self.logger.info("No public Fiverr listings parsed (expected when blocked).")
        return jobs

    @staticmethod
    def parse_html(html: str) -> List[RawJob]:
        """Extract gigs from any ld+json ``ItemList`` embedded in the page."""
        if not html:
            return []
        selector = Selector(content=html)
        jobs: List[RawJob] = []
        for script in selector.css('script[type="application/ld+json"]'):
            payload = _safe_json(str(script.text))
            for entry in _iter_item_list(payload):
                name = entry.get("name") or ""
                url = entry.get("url") or ""
                if not name or not url:
                    continue
                jobs.append(
                    RawJob(
                        source="fiverr",
                        title=name,
                        company=entry.get("seller", "Fiverr Seller"),
                        url=url,
                        description=entry.get("description", ""),
                        posted_at="",
                        location="Remote",
                        tags=["fiverr", "gig"],
                        salary=_extract_price(entry),
                    )
                )
        return jobs


def _safe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _iter_item_list(payload: Any) -> List[dict]:
    """Yield product/gig dicts from an ld+json ItemList (handles common shapes)."""
    if not isinstance(payload, dict):
        return []
    if payload.get("@type") == "ItemList":
        items = payload.get("itemListElement", [])
        out = []
        for item in items:
            node = item.get("item", item) if isinstance(item, dict) else {}
            if isinstance(node, dict):
                out.append(node)
        return out
    return []


def _extract_price(entry: dict) -> str:
    offers = entry.get("offers")
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice")
        currency = offers.get("priceCurrency", "")
        if price:
            return f"{currency} {price}".strip()
    return ""
