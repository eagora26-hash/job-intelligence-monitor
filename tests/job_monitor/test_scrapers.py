"""Parser tests for every source scraper, driven by saved fixtures (no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from job_monitor.scrapers.fiverr import FiverrScraper
from job_monitor.scrapers.freelancer import FreelancerScraper
from job_monitor.scrapers.remoteok import RemoteOKScraper
from job_monitor.scrapers.weworkremotely import WeWorkRemotelyScraper
from job_monitor.scrapers.wellfound import WellfoundScraper

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_remoteok_skips_legal_and_parses_jobs():
    data = json.loads(_read("remoteok_api.json"))
    jobs = RemoteOKScraper.parse_api(data)
    assert len(jobs) == 2  # legal notice skipped
    first = jobs[0]
    assert first["title"] == "Python Automation Engineer"
    assert first["url"] == "https://remoteok.com/remote-jobs/1001"
    assert first["salary"] == "$90,000 - $130,000"
    assert "python" in first["tags"]


def test_weworkremotely_rss_splits_company_and_title():
    jobs = WeWorkRemotelyScraper.parse_rss(_read("weworkremotely.rss").encode("utf-8"))
    assert len(jobs) == 2
    assert jobs[0]["company"] == "Globex"
    assert jobs[0]["title"] == "Senior Python Engineer"
    assert jobs[0]["url"].endswith("globex-senior-python-engineer")  # <link> preserved
    assert jobs[1]["company"] == ""  # no colon -> all title
    assert jobs[1]["title"] == "Web Scraping Specialist"


def test_freelancer_api_parsing():
    data = json.loads(_read("freelancer_api.json"))
    jobs = FreelancerScraper.parse_api(data)
    assert len(jobs) == 2
    assert jobs[0]["url"] == "https://www.freelancer.com/projects/build-web-scraping-bot-python"
    assert jobs[0]["salary"] == "USD 250-750"
    assert "Python" in jobs[0]["tags"]


def test_fiverr_perseus_listing_parsing():
    jobs = FiverrScraper.parse_html(_read("fiverr_perseus.html"))
    assert len(jobs) == 2  # gig with empty title is skipped
    first = jobs[0]
    assert first["title"] == "Build a python web scraping bot for any website"
    assert first["company"] == "ScrapeMaster Co"
    assert first["url"] == "https://www.fiverr.com/scrapemaster/build-a-python-web-scraping-bot"
    assert first["salary"] == "USD 120 (starting)"
    assert "pro" in first["tags"]
    assert jobs[1]["company"] == "autodev"  # falls back to seller_name


def test_fiverr_ldjson_itemlist_parsing():
    jobs = FiverrScraper.parse_html(_read("fiverr_listing.html"))
    assert len(jobs) == 2
    assert jobs[0]["title"].startswith("I will build a python web scraping bot")
    assert jobs[0]["url"].startswith("https://www.fiverr.com/")
    assert jobs[0]["salary"] == "USD 120"


def test_fiverr_returns_empty_on_blocked_page():
    assert FiverrScraper.parse_html("") == []
    assert FiverrScraper.parse_html("<html><body>blocked</body></html>") == []


def test_wellfound_next_data_parsing():
    jobs = WellfoundScraper.parse_html(_read("wellfound_next.html"))
    titles = {j["title"] for j in jobs}
    assert "Backend Python Engineer" in titles
    backend = next(j for j in jobs if j["title"] == "Backend Python Engineer")
    assert backend["company"] == "RocketAI"
    assert backend["url"] == "https://wellfound.com/jobs/backend-python-engineer"


def test_wellfound_returns_empty_on_blocked_page():
    assert WellfoundScraper.parse_html("<html><body>cloudflare</body></html>") == []
