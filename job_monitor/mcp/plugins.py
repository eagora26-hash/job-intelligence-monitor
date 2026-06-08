"""Working MCP plugins that expose the monitor's own data as agent-callable capabilities.

These are real, functional :class:`MCPPlugin` implementations (they query the live database),
demonstrating how the platform's features could be surfaced to an MCP client/agent.
"""

from __future__ import annotations

from typing import List

from job_monitor.analytics import AnalyticsService
from job_monitor.database import Database, JobRepository
from job_monitor.mcp.registry import MCPPlugin


class JobSearchPlugin(MCPPlugin):
    """Search stored jobs by keyword/source/min-score."""

    name = "search_jobs"
    description = "Search monitored jobs by query, source, and minimum relevance score."

    def __init__(self, database: Database) -> None:
        self._repo = JobRepository(database)

    def invoke(self, query: str = "", source: str = "", min_score: int = 0,
               limit: int = 20) -> List[dict]:
        jobs = self._repo.list_jobs(
            search=query or None,
            source=source or None,
            min_score=min_score,
            limit=limit,
        )
        return [
            {
                "title": j.title,
                "company": j.company,
                "source": j.source,
                "score": j.score,
                "category": j.category,
                "url": j.url,
            }
            for j in jobs
        ]


class AnalyticsPlugin(MCPPlugin):
    """Return headline analytics for the monitored job market."""

    name = "get_analytics"
    description = "Return overview metrics, source distribution, and top skills."

    def __init__(self, database: Database) -> None:
        self._analytics = AnalyticsService(database)

    def invoke(self, **_: object) -> dict:
        return {
            "overview": self._analytics.overview(),
            "by_source": self._analytics.by_source(),
            "top_skills": self._analytics.skill_frequency(10),
        }
