"""Keyword taxonomy: relevance keywords + weights, job categories, and skill vocabulary.

This module is the single source of truth for the "intelligence" the monitor applies to raw
jobs. It is intentionally data-only (no logic) so it can be edited safely from the dashboard
config page or overridden via settings, and unit-tested in isolation.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Default relevance keywords (from instructions.md). Used for filtering + as scoring seeds.
# ---------------------------------------------------------------------------------------
DEFAULT_KEYWORDS: list[str] = [
    "python",
    "automation",
    "scraping",
    "selenium",
    "playwright",
    "telegram bot",
    "web scraping",
    "data extraction",
    "lead generation",
    "e-commerce",
    "custom e-commerce",
    "shopify",
    "woocommerce",
    "api integration",
    "dashboard",
    "streamlit",
    "data engineering",
    "etl",
    "ai automation",
    "workflow automation",
]

# ---------------------------------------------------------------------------------------
# Relevance scoring weights. Each keyword found in a job's text adds its weight to the
# job's score. Longer/more-specific phrases are checked before shorter ones by the scorer.
# Any DEFAULT_KEYWORD without an explicit weight falls back to DEFAULT_KEYWORD_WEIGHT.
# ---------------------------------------------------------------------------------------
DEFAULT_KEYWORD_WEIGHT: int = 5

KEYWORD_WEIGHTS: dict[str, int] = {
    "python": 10,
    "automation": 10,
    "scraping": 10,
    "web scraping": 10,
    "custom e-commerce": 10,
    "ai automation": 10,
    "workflow automation": 9,
    "data engineering": 9,
    "selenium": 8,
    "playwright": 8,
    "e-commerce": 8,
    "data extraction": 8,
    "etl": 8,
    "telegram bot": 8,
    "api integration": 7,
    "lead generation": 7,
    "shopify": 7,
    "woocommerce": 7,
    "streamlit": 6,
    "dashboard": 6,
}

# ---------------------------------------------------------------------------------------
# Job categories -> trigger keywords. A job is auto-classified into every category whose
# triggers it matches; its primary category is the highest-confidence (most matches) one.
# ---------------------------------------------------------------------------------------
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Automation": ["automation", "workflow", "rpa", "zapier", "make.com", "n8n", "bot"],
    "Web Scraping": [
        "scraping", "web scraping", "scraper", "crawler", "data extraction",
        "selenium", "playwright", "beautifulsoup", "scrapy",
    ],
    "E-commerce": [
        "e-commerce", "ecommerce", "shopify", "woocommerce", "magento", "bigcommerce",
        "dropshipping", "amazon", "product feed",
    ],
    "AI": [
        "ai", "machine learning", "ml", "llm", "gpt", "openai", "nlp",
        "deep learning", "chatbot", "langchain",
    ],
    "Data Engineering": [
        "data engineering", "etl", "elt", "pipeline", "airflow", "data warehouse",
        "spark", "kafka", "dbt",
    ],
    "Python Development": ["python", "django", "fastapi", "flask", "backend"],
    "API Integration": ["api", "api integration", "rest", "graphql", "webhook", "integration"],
    "Dashboard Development": [
        "dashboard", "streamlit", "dash", "power bi", "tableau", "looker", "data visualization",
    ],
}

# ---------------------------------------------------------------------------------------
# Canonical skill vocabulary for skill extraction. Keys are the canonical labels stored on
# the job; values are the surface forms / aliases searched for in the job text.
# ---------------------------------------------------------------------------------------
SKILL_ALIASES: dict[str, list[str]] = {
    "Python": ["python"],
    "Django": ["django"],
    "FastAPI": ["fastapi", "fast api"],
    "Flask": ["flask"],
    "Selenium": ["selenium"],
    "Playwright": ["playwright"],
    "Scrapy": ["scrapy"],
    "BeautifulSoup": ["beautifulsoup", "bs4", "beautiful soup"],
    "Pandas": ["pandas"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "SQL": ["sql"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript"],
    "React": ["react"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "Streamlit": ["streamlit"],
    "Airflow": ["airflow"],
    "Kafka": ["kafka"],
    "Spark": ["spark", "pyspark"],
    "GraphQL": ["graphql"],
    "REST API": ["rest api", "restful"],
    "Telegram Bot": ["telegram bot", "telegram"],
    "LLM": ["llm", "gpt", "openai", "langchain", "claude"],
}

# ---------------------------------------------------------------------------------------
# Default exclude keywords. A job matching any of these is filtered out before storage
# (overridable via EXCLUDE_KEYWORDS env or the dashboard config page).
# ---------------------------------------------------------------------------------------
DEFAULT_EXCLUDE_KEYWORDS: list[str] = [
    "unpaid",
    "security clearance",
    "us citizen only",
    "on-site only",
]


def keyword_weight(keyword: str) -> int:
    """Return the scoring weight for a keyword, falling back to the default weight."""
    return KEYWORD_WEIGHTS.get(keyword.lower(), DEFAULT_KEYWORD_WEIGHT)
