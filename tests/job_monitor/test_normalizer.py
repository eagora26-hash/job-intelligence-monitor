"""Tests for the normalization layer."""

from __future__ import annotations

from datetime import datetime

from job_monitor.normalizers import Normalizer
from job_monitor.scrapers.base import RawJob


def test_normalize_strips_html_and_entities():
    norm = Normalizer()
    record = norm.normalize(
        RawJob(
            source="remoteok",
            url="https://x.com/1",
            title="  Python   Dev ",
            description="<p>Build <b>scrapers</b> &amp; bots.</p>",
            tags=["Python", "python", "  Automation "],
        )
    )
    assert record is not None
    assert record.title == "Python Dev"  # whitespace collapsed
    assert record.description == "Build scrapers & bots."  # tags stripped, entity decoded
    assert record.tags == ["Python", "Automation"]  # de-duped case-insensitively


def test_normalize_drops_records_without_url_or_title():
    norm = Normalizer()
    assert norm.normalize(RawJob(source="s", url="", title="x")) is None
    assert norm.normalize(RawJob(source="s", url="u", title="")) is None


def test_remote_inference():
    norm = Normalizer()
    # remoteok is remote-by-default
    r1 = norm.normalize(RawJob(source="remoteok", url="u1", title="Dev", location=""))
    assert r1.remote is True
    # freelancer depends on text hints
    r2 = norm.normalize(RawJob(source="freelancer", url="u2", title="Dev", location="London"))
    assert r2.remote is False
    r3 = norm.normalize(RawJob(source="freelancer", url="u3", title="Remote Dev", location="Anywhere"))
    assert r3.remote is True


def test_date_parsing_variants():
    norm = Normalizer()
    iso = norm.normalize(RawJob(source="s", url="u1", title="t", posted_at="2026-06-01T09:30:00+00:00"))
    rfc = norm.normalize(RawJob(source="s", url="u2", title="t", posted_at="Mon, 02 Jun 2026 10:00:00 +0000"))
    epoch = norm.normalize(RawJob(source="s", url="u3", title="t", posted_at="1780000000"))
    bad = norm.normalize(RawJob(source="s", url="u4", title="t", posted_at="not a date"))
    assert isinstance(iso.posted_at, datetime) and iso.posted_at.year == 2026
    assert isinstance(rfc.posted_at, datetime) and rfc.posted_at.day == 2
    assert isinstance(epoch.posted_at, datetime)
    assert bad.posted_at is None


def test_normalize_many_filters_invalid():
    norm = Normalizer()
    out = norm.normalize_many([
        RawJob(source="s", url="u1", title="Good"),
        RawJob(source="s", url="", title="Bad"),
    ])
    assert len(out) == 1
