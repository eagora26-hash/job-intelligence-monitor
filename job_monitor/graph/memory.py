"""A working, dependency-free in-memory graph store.

Demonstrates the entity/relationship model (Job → Company / Skill / Source / Category) without
requiring any external graph database. Useful for analytics ("which skills co-occur?", "which
companies post the most relevant jobs?") and as a reference for the Graphiti adapter.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Sequence

from job_monitor.graph.base import (
    NODE_CATEGORY,
    NODE_COMPANY,
    NODE_JOB,
    NODE_SKILL,
    NODE_SOURCE,
    REL_CLASSIFIED_AS,
    REL_POSTED_BY,
    REL_REQUIRES,
    REL_SOURCED_FROM,
    GraphEdge,
    GraphNode,
    GraphStore,
)
from job_monitor.models import JobRecord


def _node_id(node_type: str, key: str) -> str:
    digest = hashlib.md5(key.lower().encode()).hexdigest()[:10]
    return f"{node_type}:{digest}"


class InMemoryGraphStore(GraphStore):
    """Stores nodes/edges in dicts/sets; safe to rebuild on demand."""

    def __init__(self) -> None:
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: set[GraphEdge] = set()

    def _ensure_node(self, node_type: str, label: str) -> str:
        node_id = _node_id(node_type, label)
        if node_id not in self._nodes:
            self._nodes[node_id] = GraphNode(id=node_id, type=node_type, label=label)
        return node_id

    def add_job(self, job: JobRecord) -> None:
        job_id = self._ensure_node(NODE_JOB, job.url)
        # Re-label the job node with its title (url is the identity key).
        self._nodes[job_id] = GraphNode(id=job_id, type=NODE_JOB, label=job.title or job.url)

        source_id = self._ensure_node(NODE_SOURCE, job.source)
        self._edges.add(GraphEdge(job_id, source_id, REL_SOURCED_FROM))

        if job.company:
            company_id = self._ensure_node(NODE_COMPANY, job.company)
            self._edges.add(GraphEdge(job_id, company_id, REL_POSTED_BY))

        if job.category:
            category_id = self._ensure_node(NODE_CATEGORY, job.category)
            self._edges.add(GraphEdge(job_id, category_id, REL_CLASSIFIED_AS))

        for skill in job.skills:
            skill_id = self._ensure_node(NODE_SKILL, skill)
            self._edges.add(GraphEdge(job_id, skill_id, REL_REQUIRES))

    def nodes(self) -> List[GraphNode]:
        return list(self._nodes.values())

    def edges(self) -> List[GraphEdge]:
        return list(self._edges)

    def neighbors(self, node_id: str) -> List[GraphNode]:
        out_ids = {e.target_id for e in self._edges if e.source_id == node_id}
        in_ids = {e.source_id for e in self._edges if e.target_id == node_id}
        return [self._nodes[n] for n in (out_ids | in_ids) if n in self._nodes]

    def to_dict(self) -> Dict[str, list]:
        """Serialize to a plain dict (for JSON export / visualization tools)."""
        return {
            "nodes": [{"id": n.id, "type": n.type, "label": n.label} for n in self.nodes()],
            "edges": [
                {"source": e.source_id, "target": e.target_id, "relation": e.relation}
                for e in self.edges()
            ],
        }


def build_graph(jobs: Sequence[JobRecord]) -> InMemoryGraphStore:
    """Build an in-memory job knowledge graph from a list of jobs."""
    store = InMemoryGraphStore()
    store.add_jobs(list(jobs))
    return store
