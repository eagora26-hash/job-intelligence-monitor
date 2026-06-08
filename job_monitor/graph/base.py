"""Graph abstractions: nodes, edges, and the :class:`GraphStore` interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List

from job_monitor.models import JobRecord

# Node types and relationship labels (kept as constants for consistency across backends).
NODE_JOB = "job"
NODE_COMPANY = "company"
NODE_SKILL = "skill"
NODE_SOURCE = "source"
NODE_CATEGORY = "category"

REL_POSTED_BY = "POSTED_BY"      # Job -> Company
REL_REQUIRES = "REQUIRES"        # Job -> Skill
REL_SOURCED_FROM = "SOURCED_FROM"  # Job -> Source
REL_CLASSIFIED_AS = "CLASSIFIED_AS"  # Job -> Category


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str
    label: str
    props: tuple = field(default_factory=tuple)  # frozen-friendly; usually empty


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relation: str


class GraphStore(ABC):
    """Interface for a backend that ingests jobs and exposes the resulting graph."""

    @abstractmethod
    def add_job(self, job: JobRecord) -> None:
        """Ingest one job, creating its entities and relationships."""

    @abstractmethod
    def nodes(self) -> List[GraphNode]:
        ...

    @abstractmethod
    def edges(self) -> List[GraphEdge]:
        ...

    def add_jobs(self, jobs: List[JobRecord]) -> None:
        for job in jobs:
            self.add_job(job)

    def stats(self) -> Dict[str, int]:
        node_types: Dict[str, int] = {}
        for node in self.nodes():
            node_types[node.type] = node_types.get(node.type, 0) + 1
        return {"nodes": len(self.nodes()), "edges": len(self.edges()), **node_types}
