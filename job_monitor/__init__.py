"""Multi-Source AI Job Intelligence Monitor.

A production-grade monitoring platform that collects, normalizes, scores, stores, and
surfaces remote/freelance job opportunities from multiple sources. Built on top of the
vendored `scrapling` engine (reused for HTTP fetching and HTML/JSON parsing).

The package is organized in clean layers (see ``IMPLEMENTATION_PLAN.md``)::

    config/        settings + keyword taxonomy
    models/        canonical domain models (JobRecord, SourceHealth, ...)
    scrapers/      per-source acquisition built on the Scrapling Fetcher
    normalizers/   raw payloads -> canonical JobRecord
    pipeline/      enrichment, filtering, and the concurrent runner
    database/      SQLite connection + repository pattern
    notifications/ Notifier interface + Telegram implementation
    analytics/     metrics + exporters
    dashboard/     Streamlit application
    services/      state, backup, archive, demo data
    ai/ graph/ mcp/ api/   real extension interfaces (no fakes)
    observability/ structured logging
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
