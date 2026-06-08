# Architecture

A folder-by-folder guide to the `job_monitor/` application package. The design is **layered**:
each layer depends only on the ones below it. The vendored [`scrapling/`](../README_SCRAPLING.md)
library is reused (parsing + fetch backend) but otherwise untouched.

## Layer map

```
Interfaces      main.py (CLI) · dashboard/ (Streamlit) · api/ (FastAPI)
Orchestration   pipeline/runner.py · scheduler.py · services/state.py
Services        pipeline/enrichment.py · analytics/ · notifications/ · services/{backup,archive}
Domain          models/ · normalizers/ · database/ (repositories)
Acquisition     scrapers/ (BaseScraper → 5 sources → http adapter → Scrapling)
Cross-cutting   config/ · observability/
Extensions      ai/ · graph/ · mcp/ · api/   (optional, real interfaces)
```

## Packages

| Package | Responsibility | Key types |
|---|---|---|
| `config/` | Typed settings from env/`.env`; keyword/scoring taxonomy; source labels | `Settings`, `keywords.py`, `sources.py` |
| `models/` | Canonical domain models | `JobRecord`, `SourceHealth`, `DailySnapshot`, `JobChange` |
| `scrapers/` | Per-source acquisition; isolation + timing | `BaseScraper`, `RemoteOKScraper`, …, `HttpClient`, `registry` |
| `normalizers/` | Raw payloads → `JobRecord` (HTML strip, date parsing, remote flag) | `Normalizer` |
| `pipeline/` | Enrichment, filtering, concurrent orchestration | `Enricher`, `JobFilter`, `PipelineRunner` |
| `database/` | SQLite connection + repository pattern (no SQL leaks out) | `Database`, `JobRepository`, … |
| `notifications/` | Notifier interface + Telegram + formatters | `Notifier`, `TelegramNotifier`, `NullNotifier` |
| `analytics/` | Metrics + exporters | `AnalyticsService`, `JobExporter` |
| `dashboard/` | Streamlit UI (nav + views + cached components) | `app.py`, `views/*` |
| `services/` | State/resume, backup, archive, demo data | `StateStore`, `BackupService`, `ArchiveService` |
| `observability/` | Structured rotating logging | `configure_logging`, `get_logger` |
| `ai/` | AI-enrichment interface (rule-based today, LLM-ready) | `AIEnricher`, `RuleBasedAIEnricher` |
| `graph/` | Knowledge-graph layer (in-memory + Graphiti adapter) | `GraphStore`, `InMemoryGraphStore` |
| `mcp/` | MCP config loader + server/plugin registry | `MCPServerRegistry`, `MCPPlugin` |
| `api/` | FastAPI read API | `create_app()` |

## Request → storage flow

1. **Scheduler** triggers **PipelineRunner.run_once()**.
2. Runner scrapes all enabled sources **concurrently** (thread pool); each `BaseScraper.scrape()`
   is fully isolated and returns a `ScrapeResult` (never raises).
3. **Normalizer** maps raw dicts → `JobRecord`.
4. **Enricher** adds score / category / skills / quality.
5. **JobFilter** applies include/exclude + relevance gate.
6. **JobRepository.upsert()** dedupes on URL and records field-level changes to `job_history`.
7. New, relevant jobs are pushed to the **Notifier**; **state** + **daily snapshot** are checkpointed.
8. **Dashboard** / **API** read the same database through repositories + `AnalyticsService`.

## Key design decisions

- **curl_cffi + Scrapling `Selector`** instead of Scrapling's Playwright-coupled `Fetcher`, so the
  app runs with no browser stack in CI/Docker (browser fetch is an optional stealth fallback).
- **Repository pattern** keeps all SQL in one place; services/UI stay persistence-agnostic.
- **Strategy/registry** for sources makes adding a scraper a one-line change.
- **Interface + factory** for notifications/AI/graph keeps optional pieces swappable and honest.

See [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for the full rationale and trade-offs.
