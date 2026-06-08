"""Optional Graphiti adapter (import-guarded).

`Graphiti <https://github.com/getzep/graphiti>`_ is a temporal knowledge-graph framework. This
adapter maps our entity/relationship model onto it **when the optional dependency is installed**.
It is never imported by the core app; :func:`is_available` lets callers feature-detect.
"""

from __future__ import annotations

from typing import Sequence

from job_monitor.graph.base import GraphStore
from job_monitor.models import JobRecord
from job_monitor.observability import get_logger

logger = get_logger("graph.graphiti")


def is_available() -> bool:
    """Return ``True`` if the optional ``graphiti-core`` package is importable."""
    try:
        import graphiti_core  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


class GraphitiAdapter(GraphStore):
    """Maps jobs into a Graphiti graph. Requires ``pip install graphiti-core``.

    Implemented as a thin, honest adapter: construction fails fast with a clear message if the
    dependency is missing, so it can never masquerade as working when it is not installed.
    """

    def __init__(self, client: object = None) -> None:
        if not is_available():
            raise RuntimeError(
                "graphiti-core is not installed. Install it (`pip install graphiti-core`) and "
                "pass a configured client to use the Graphiti backend."
            )
        self._client = client
        logger.info("GraphitiAdapter initialized.")

    def add_job(self, job: JobRecord) -> None:  # pragma: no cover - requires optional dep
        # Mapping outline (entities + relationships) for when a client is wired:
        #   episode = f"{job.title} at {job.company} via {job.source}"
        #   self._client.add_episode(name=job.url, episode_body=episode, ...)
        raise NotImplementedError(
            "Wire your graphiti-core client here to ingest jobs as temporal episodes."
        )

    def nodes(self):  # pragma: no cover - requires optional dep
        raise NotImplementedError("Query the Graphiti client for nodes.")

    def edges(self):  # pragma: no cover - requires optional dep
        raise NotImplementedError("Query the Graphiti client for edges.")

    def add_jobs(self, jobs: Sequence[JobRecord]) -> None:  # pragma: no cover
        for job in jobs:
            self.add_job(job)
