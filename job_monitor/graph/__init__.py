"""Optional knowledge-graph layer.

Models jobs as a graph of entities (Job, Company, Skill, Source, Category) and relationships.
Ships a **working** dependency-free :class:`InMemoryGraphStore` and an optional, import-guarded
:class:`GraphitiAdapter`. The application runs fully without any graph database.
"""

from job_monitor.graph.base import GraphEdge, GraphNode, GraphStore
from job_monitor.graph.memory import InMemoryGraphStore, build_graph

__all__ = ["GraphNode", "GraphEdge", "GraphStore", "InMemoryGraphStore", "build_graph"]
