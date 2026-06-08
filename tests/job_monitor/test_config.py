"""Tests for the configuration layer."""

from __future__ import annotations

from job_monitor.config.keywords import (
    CATEGORY_KEYWORDS,
    DEFAULT_KEYWORDS,
    KEYWORD_WEIGHTS,
    keyword_weight,
)
from job_monitor.config.settings import Settings


def test_settings_defaults_and_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("ENABLE_FIVERR", "false")
    monkeypatch.setenv("POLLING_INTERVAL", "120")
    settings = Settings(_env_file=None)  # ignore repo .env for a clean default test

    assert settings.polling_interval == 120
    assert settings.enabled_sources()["fiverr"] is False
    assert settings.enabled_sources()["remoteok"] is True
    # Relative paths resolve against the project root (absolute).
    assert settings.database_path.is_absolute()
    assert settings.state_file.name == "state.json"


def test_settings_csv_filter_parsing(monkeypatch):
    monkeypatch.setenv("EXCLUDE_KEYWORDS", "unpaid, clearance ,  ")
    settings = Settings(_env_file=None)
    assert settings.exclude_keywords == ["unpaid", "clearance"]


def test_keyword_weight_fallback():
    assert keyword_weight("python") == KEYWORD_WEIGHTS["python"]
    assert keyword_weight("PYTHON") == KEYWORD_WEIGHTS["python"]  # case-insensitive
    assert keyword_weight("a-keyword-with-no-explicit-weight") == 5  # DEFAULT_KEYWORD_WEIGHT


def test_taxonomy_is_well_formed():
    assert len(DEFAULT_KEYWORDS) == 20
    assert "Web Scraping" in CATEGORY_KEYWORDS
    # Every category has at least one trigger keyword.
    assert all(triggers for triggers in CATEGORY_KEYWORDS.values())
