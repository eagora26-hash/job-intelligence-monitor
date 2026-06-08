"""AI enrichment layer.

Defines the :class:`AIEnricher` interface plus a **working** rule-based implementation and a
documented LLM seam. The rule-based enricher runs today with no API keys; the LLM enricher is
an explicit, typed extension point (not a fake) for wiring Claude/OpenAI later.
"""

from job_monitor.ai.enrichment import (
    AIEnricher,
    JobInsight,
    LLMAIEnricher,
    RuleBasedAIEnricher,
    get_ai_enricher,
)

__all__ = [
    "AIEnricher",
    "JobInsight",
    "RuleBasedAIEnricher",
    "LLMAIEnricher",
    "get_ai_enricher",
]
