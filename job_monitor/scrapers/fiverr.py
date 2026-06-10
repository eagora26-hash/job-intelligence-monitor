"""Fiverr scraper — public listing pages only (best-effort).

Fiverr exposes no public jobs/buyer-requests API, so this scraper parses the JSON data
island (``<script id="perseus-initial-props">``) that public subcategory/search pages embed
server-side — each page carries ~48 gigs under ``listings[].gigs``. The legacy ``ld+json``
``ItemList`` parse is kept as a fallback for pages that still emit it. The scraper stays
*honest*: it returns an empty list (never fabricated data) when pages are blocked or the
embedded data is absent. The demo-data generator covers the dashboard in that case.
"""

from __future__ import annotations

import json
from typing import Any, List

from scrapling import Selector

from job_monitor.scrapers.base import BaseScraper, RawJob

# Public gig-bearing pages (subcategory + search) aligned with the monitored niche.
# NOTE: category *hub* pages (e.g. /categories/programming-tech/data-processing) embed no
# gigs — only subcategory and /search/gigs pages carry the listings payload.
LISTING_URLS = [
    "https://www.fiverr.com/categories/programming-tech/web-programming-services/web-scraping",
    "https://www.fiverr.com/search/gigs?query=python%20automation",
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

    @classmethod
    def parse_html(cls, html: str) -> List[RawJob]:
        """Extract gigs from the perseus data island, falling back to ld+json ItemList."""
        if not html:
            return []
        selector = Selector(content=html)
        jobs = cls._parse_perseus(selector)
        return jobs if jobs else cls._parse_ld_json(selector)

    # ------------------------------------------------------------- perseus data island
    @staticmethod
    def _parse_perseus(selector: Selector) -> List[RawJob]:
        """Parse gigs from ``<script id="perseus-initial-props">`` (current page format)."""
        jobs: List[RawJob] = []
        for script in selector.css("script#perseus-initial-props"):
            payload = _safe_json(str(script.text))
            if not isinstance(payload, dict):
                continue
            for listing in payload.get("listings") or []:
                if not isinstance(listing, dict):
                    continue
                for gig in listing.get("gigs") or []:
                    job = _gig_to_raw(gig)
                    if job:
                        jobs.append(job)
        return jobs

    # ------------------------------------------------------------- legacy ld+json
    @staticmethod
    def _parse_ld_json(selector: Selector) -> List[RawJob]:
        """Extract gigs from any ld+json ``ItemList`` embedded in the page (legacy)."""
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


def _gig_to_raw(gig: Any) -> RawJob | None:
    """Map one perseus gig dict to the raw-job contract (or ``None`` if unusable)."""
    if not isinstance(gig, dict):
        return None
    title = (gig.get("title") or "").strip()
    path = gig.get("gig_url") or ""
    if not title or not path:
        return None
    seller = gig.get("seller_display_name") or gig.get("seller_name") or "Fiverr Seller"
    price = gig.get("price_i")
    salary = f"USD {price} (starting)" if price else ""
    tags = ["fiverr", "gig"]
    if gig.get("is_pro"):
        tags.append("pro")
    return RawJob(
        source="fiverr",
        # Gig titles are stored lowercase ("develop ai web application …") — capitalize.
        title=title[0].upper() + title[1:],
        company=str(seller),
        url=f"https://www.fiverr.com{path}" if path.startswith("/") else path,
        description=title,
        posted_at="",
        location="Remote",
        tags=tags,
        salary=salary,
    )


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
