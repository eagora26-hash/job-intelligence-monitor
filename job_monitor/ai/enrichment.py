"""AI enrichment interfaces and implementations.

``AIEnricher`` is the contract: turn a job into a :class:`JobInsight` (relevance, summary,
category, tags) and build a daily opportunity digest. Two implementations are provided:

* :class:`RuleBasedAIEnricher` — deterministic, dependency-free, **works today**. It reuses the
  pipeline :class:`Enricher` and extractive heuristics, so the "AI" surface is real, not a stub.
* :class:`LLMAIEnricher` — a typed extension point for an LLM (e.g. Claude). Its methods raise
  ``NotImplementedError`` with guidance; it exists to show *where* an LLM plugs in, and the
  factory never returns it unless explicitly requested. This keeps the feature honest.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from job_monitor.models import JobRecord
from job_monitor.pipeline.enrichment import Enricher


@dataclass
class JobInsight:
    """Structured AI insight for a single job."""

    relevance: int
    category: str
    summary: str
    suggested_tags: List[str] = field(default_factory=list)
    rationale: str = ""


class AIEnricher(ABC):
    """Interface for AI-style job enrichment (rule-based today, LLM-ready tomorrow)."""

    @abstractmethod
    def insight(self, job: JobRecord) -> JobInsight:
        """Return a :class:`JobInsight` for one job."""

    @abstractmethod
    def daily_digest(self, jobs: Sequence[JobRecord]) -> str:
        """Return a human-readable digest of the most relevant jobs."""

    def insights(self, jobs: Sequence[JobRecord]) -> List[JobInsight]:
        return [self.insight(job) for job in jobs]


class RuleBasedAIEnricher(AIEnricher):
    """Deterministic enricher — real, explainable, and free. The default."""

    def __init__(self, enricher: Optional[Enricher] = None) -> None:
        self._enricher = enricher or Enricher()

    def insight(self, job: JobRecord) -> JobInsight:
        text = job.searchable_text
        score = self._enricher.score(text)
        category = self._enricher.classify(text) or "General"
        skills = self._enricher.extract_skills(text)
        summary = self._summarize(job)
        rationale = (
            f"Matched category '{category}'"
            + (f"; skills: {', '.join(skills[:5])}" if skills else "")
            + f"; relevance {score}."
        )
        return JobInsight(
            relevance=score,
            category=category,
            summary=summary,
            suggested_tags=skills[:8],
            rationale=rationale,
        )

    @staticmethod
    def _summarize(job: JobRecord, max_len: int = 200) -> str:
        """Extractive one-liner: title + the first sentence of the description."""
        first_sentence = job.description.split(". ")[0].strip()
        head = f"{job.title} at {job.company}".strip(" at")
        summary = f"{head}. {first_sentence}".strip()
        return (summary[: max_len - 1] + "…") if len(summary) > max_len else summary

    def daily_digest(self, jobs: Sequence[JobRecord], top: int = 5) -> str:
        ranked = sorted(jobs, key=lambda j: j.score, reverse=True)[:top]
        if not ranked:
            return "No new opportunities today."
        lines = [f"Top {len(ranked)} opportunities today:", ""]
        for i, job in enumerate(ranked, 1):
            lines.append(f"{i}. {job.title} — {job.company or 'n/a'} "
                         f"({job.category or 'General'}, score {job.score})")
        return "\n".join(lines)


class LLMAIEnricher(AIEnricher):
    """LLM-backed enricher — **typed extension point, not yet wired**.

    Intentionally unimplemented: it documents exactly where an LLM (e.g. Claude via the
    Anthropic SDK) would generate richer summaries/classification. The :func:`get_ai_enricher`
    factory returns the rule-based enricher unless an LLM client is explicitly supplied, so no
    code path silently pretends to call an LLM.
    """

    def __init__(self, client: object = None, model: str = "claude-sonnet-4-6") -> None:
        self.client = client
        self.model = model

    def insight(self, job: JobRecord) -> JobInsight:  # pragma: no cover - documented seam
        raise NotImplementedError(
            "LLMAIEnricher is a future integration point. Provide an LLM client and implement "
            "this method to generate summaries/classification via the model."
        )

    def daily_digest(self, jobs: Sequence[JobRecord]) -> str:  # pragma: no cover - seam
        raise NotImplementedError(
            "LLMAIEnricher.daily_digest is not implemented; use RuleBasedAIEnricher by default."
        )


def get_ai_enricher(llm_client: object = None) -> AIEnricher:
    """Return an :class:`AIEnricher`.

    Defaults to the working rule-based enricher. Pass an LLM client only once
    :class:`LLMAIEnricher` is implemented for your provider.
    """
    if llm_client is not None:
        return LLMAIEnricher(client=llm_client)
    return RuleBasedAIEnricher()
