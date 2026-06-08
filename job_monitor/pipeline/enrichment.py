"""Job enrichment: relevance scoring, classification, skill extraction, quality scoring.

The :class:`Enricher` turns a normalized :class:`JobRecord` into an *intelligent* one — this
is what makes the product a "Job Intelligence Monitor" rather than a list of links. It is
pure/deterministic (no I/O), driven entirely by the taxonomy in
:mod:`job_monitor.config.keywords`, which makes it trivially unit-testable and configurable.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from job_monitor.config.keywords import (
    CATEGORY_KEYWORDS,
    DEFAULT_KEYWORDS,
    KEYWORD_WEIGHTS,
    SKILL_ALIASES,
    keyword_weight,
)
from job_monitor.models import JobRecord


class Enricher:
    """Applies the relevance/category/skill/quality model to jobs."""

    def __init__(
        self,
        *,
        keywords: Sequence[str] | None = None,
        weights: Dict[str, int] | None = None,
        categories: Dict[str, List[str]] | None = None,
        skill_aliases: Dict[str, List[str]] | None = None,
    ) -> None:
        # Union of default keywords and any explicitly weighted keywords.
        base = list(keywords or DEFAULT_KEYWORDS)
        self._weights = weights or KEYWORD_WEIGHTS
        self._scoring_keywords = sorted(
            set(base) | set(self._weights.keys()), key=len, reverse=True
        )
        self._categories = categories or CATEGORY_KEYWORDS
        self._skill_aliases = skill_aliases or SKILL_ALIASES

    # ----------------------------------------------------------------- public
    def enrich(self, job: JobRecord) -> JobRecord:
        """Return a copy of ``job`` with score/category/skills/quality populated."""
        text = job.searchable_text
        return job.model_copy(
            update={
                "score": self.score(text),
                "category": self.classify(text),
                "skills": self.extract_skills(text),
                "quality_score": self.quality(job),
            }
        )

    def enrich_many(self, jobs: Sequence[JobRecord]) -> List[JobRecord]:
        return [self.enrich(job) for job in jobs]

    # ----------------------------------------------------------------- components
    def score(self, text: str) -> int:
        """Relevance score: sum of weights for every matched keyword."""
        return sum(
            keyword_weight(kw) if kw not in self._weights else self._weights[kw]
            for kw in self._scoring_keywords
            if kw in text
        )

    def classify(self, text: str) -> str:
        """Primary category = the one with the most trigger-keyword matches (or '')."""
        best_category = ""
        best_hits = 0
        for category, triggers in self._categories.items():
            hits = sum(1 for trigger in triggers if trigger in text)
            if hits > best_hits:
                best_category, best_hits = category, hits
        return best_category

    def categories(self, text: str) -> List[str]:
        """All categories the text matches (useful for tagging/graph relationships)."""
        return [
            category
            for category, triggers in self._categories.items()
            if any(trigger in text for trigger in triggers)
        ]

    def extract_skills(self, text: str) -> List[str]:
        """Canonical skills detected via their aliases, in taxonomy order."""
        found: List[str] = []
        for canonical, aliases in self._skill_aliases.items():
            if any(alias in text for alias in aliases):
                found.append(canonical)
        return found

    @staticmethod
    def quality(job: JobRecord) -> int:
        """Data-quality score in ``[0, 100]`` based on field completeness."""
        score = 0
        if job.company.strip():
            score += 25
        if len(job.description.strip()) >= 80:
            score += 30
        elif job.description.strip():
            score += 10
        if job.salary.strip():
            score += 25
        if job.location.strip():
            score += 10
        if job.tags:
            score += 10
        return min(score, 100)
