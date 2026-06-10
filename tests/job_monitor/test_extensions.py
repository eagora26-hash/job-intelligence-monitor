"""Tests for the optional extension layers (AI enrichment, graph, MCP, REST API)."""

from __future__ import annotations

from pathlib import Path

import pytest

from job_monitor.ai import RuleBasedAIEnricher, get_ai_enricher
from job_monitor.ai.enrichment import LLMAIEnricher
from job_monitor.database import Database, JobRepository
from job_monitor.graph import build_graph
from job_monitor.graph.base import NODE_COMPANY, NODE_SKILL
from job_monitor.mcp import MCPServerRegistry, load_mcp_config
from job_monitor.models import JobRecord


def _job(**kw) -> JobRecord:
    base = dict(source="remoteok", url="https://x/1", title="Python Automation Engineer",
                company="Acme", description="Build web scraping bots with selenium and docker.",
                skills=["Python", "Selenium", "Docker"], category="Web Scraping", score=30)
    base.update(kw)
    return JobRecord(**base)


# ----------------------------------------------------------------- AI
def test_rule_based_ai_enricher_produces_insight():
    insight = RuleBasedAIEnricher().insight(_job())
    assert insight.relevance > 0
    assert insight.category != ""
    assert insight.summary
    assert "Python" in insight.suggested_tags


def test_ai_daily_digest_ranks_by_score():
    jobs = [_job(url="u1", title="A", score=10), _job(url="u2", title="B", score=40)]
    digest = RuleBasedAIEnricher().daily_digest(jobs)
    assert "Top 2" in digest
    assert digest.index("B") < digest.index("A")  # higher score listed first


def test_get_ai_enricher_defaults_to_rule_based():
    assert isinstance(get_ai_enricher(), RuleBasedAIEnricher)


def test_llm_enricher_is_an_honest_unimplemented_seam():
    with pytest.raises(NotImplementedError):
        LLMAIEnricher().insight(_job())


# ----------------------------------------------------------------- graph
def test_graph_builds_entities_and_relationships():
    jobs = [
        _job(url="u1", company="Acme", skills=["Python", "Docker"]),
        _job(url="u2", company="Globex", skills=["Python", "Selenium"]),
    ]
    graph = build_graph(jobs)
    stats = graph.stats()
    assert stats[NODE_COMPANY] == 2          # Acme, Globex
    assert stats[NODE_SKILL] == 3            # Python, Docker, Selenium (deduped)
    assert stats["edges"] > 0
    payload = graph.to_dict()
    assert "nodes" in payload and "edges" in payload


# ----------------------------------------------------------------- MCP
def test_mcp_config_loads_bundled_default():
    configs = load_mcp_config()  # bundled servers.json
    assert any(c.name == "scrapling" for c in configs)


def test_mcp_registry_register_and_manifest(tmp_path):
    from job_monitor.mcp.plugins import JobSearchPlugin

    db = Database(tmp_path / "jobs.db")
    db.initialize()
    JobRepository(db).upsert(_job())

    registry = MCPServerRegistry()
    registry.load_from_config()
    registry.register_plugin(JobSearchPlugin(db))

    manifest = registry.manifest()
    assert any(p["name"] == "search_jobs" for p in manifest["plugins"])
    # The plugin actually queries the DB.
    results = registry.plugin("search_jobs").invoke(query="python")
    assert results and results[0]["title"]


# ----------------------------------------------------------------- API
def test_rest_api_endpoints(tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from job_monitor.api.app import create_app
    from job_monitor.config.settings import Settings

    settings = Settings(
        _env_file=None,
        DATABASE_PATH=str(tmp_path / "jobs.db"),
        DATA_DIR=str(tmp_path / "data"),
        LOG_DIR=str(tmp_path / "logs"),
        BACKUP_DIR=str(tmp_path / "backup"),
        EXPORT_DIR=str(tmp_path / "exports"),
        ARCHIVE_DB_PATH=str(tmp_path / "archive.db"),
    )
    db = Database(settings.database_path)
    db.initialize()
    JobRepository(db).upsert(_job())

    client = TestClient(create_app(settings=settings, database=db))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["total_jobs"] == 1

    jobs = client.get("/jobs", params={"min_score": 1})
    assert jobs.status_code == 200
    assert len(jobs.json()) == 1
    assert jobs.json()[0]["title"].startswith("Python")

    overview = client.get("/analytics/overview")
    assert overview.status_code == 200
    assert overview.json()["total_jobs"] == 1
