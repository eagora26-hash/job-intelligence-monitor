# Implementation Plan — Multi-Source AI Job Intelligence Monitor

> Status: **Living document**. Updated as phases complete. See [HANDOVER.md](HANDOVER.md)
> for the current real-time state and [TASKS.md](TASKS.md) for the granular task board.

---

## 1. Current State Analysis

### 1.1 What the repository already is

This repository is a fork of **[Scrapling](https://github.com/D4Vinci/Scrapling) v0.4.8** —
a mature, production-grade, undetectable web-scraping library. It is **not** a blank slate;
it is a reusable scraping engine with the following relevant capabilities:

| Component | Location | Reuse value for this project |
| --- | --- | --- |
| `Fetcher` / `AsyncFetcher` | `scrapling/fetchers/requests.py` | HTTP GET/POST over `curl_cffi` with browser-impersonation TLS fingerprints. **Primary HTTP layer.** |
| `StealthyFetcher` / `DynamicFetcher` | `scrapling/fetchers/` | Playwright/Patchright browser fetching for JS-heavy / anti-bot sources. **Optional fallback layer.** |
| `Selector` / `Selectors` | `scrapling/parser.py` | lxml-backed parsing with `css()`, `xpath()`, `find_all()`, `re()`, `get_all_text()`, `.json()`. **Primary parsing layer.** |
| `Response` | `scrapling/engines/toolbelt/custom.py` | `Selector` subclass returned by fetchers; adds `.status`, `.body`, `.json()`. |
| Spider framework | `scrapling/spiders/` | Crawling/scheduling/checkpoint primitives — informative, but heavier than we need. |

### 1.2 Strengths we inherit

- Battle-tested fetching with TLS/browser fingerprint impersonation (low block rate).
- Unified parse API (`css`/`xpath`/`re`/`json`) means **one** extraction style across all sources.
- Strong typing, lazy imports, clean package conventions to mirror.

### 1.3 Gaps for the job-monitor product (everything below is net-new)

- No application layer: no domain model, persistence, scheduling, notifications, analytics, or UI.
- No source-specific scrapers for job boards.
- No configuration/secrets management for an app (the library is config-by-argument).
- No observability/state/resume/health for a long-running monitor.

### 1.4 Environment findings (verified)

- Host Python is **3.14** and **externally managed** (PEP 668). A project virtualenv at
  `.venv/` is used. Core deps (`lxml`, `cssselect`, `orjson`, `tld`, `w3lib`, `curl_cffi`,
  `pydantic`, `python-dotenv`) **install and import cleanly** on 3.14.
- `playwright==1.59.0` (Scrapling's `fetchers` extra) is **not required to run** the monitor;
  all five target sources are reachable via HTTP/JSON/RSS. Browser fetching stays an optional,
  documented capability so the app runs in lightweight/CI/Docker environments without browsers.
- The directory is **not yet a git repository** (the environment snapshot was misleading);
  git is initialized in the final phase.

---

## 2. Missing Components (to be built)

1. **Domain model & normalization** — a single canonical `JobRecord` and a normalization
   layer so no source-specific shape leaks past the scrapers.
2. **Source scrapers** — RemoteOK, We Work Remotely, Freelancer, Fiverr (public), Wellfound,
   each isolated, each emitting raw dicts, fronted by a `BaseScraper` that wraps Scrapling.
3. **Enrichment pipeline** — relevance scoring, keyword/category classification, skill
   extraction, data-quality scoring, dedup + change detection.
4. **Persistence** — SQLite via the repository pattern: `jobs`, `job_history`,
   `source_health`, `daily_snapshots`, plus an archive database.
5. **Notifications** — Telegram (new-job alerts, daily summary, startup, errors) behind a
   `Notifier` interface.
6. **Orchestration** — concurrent `PipelineRunner`, `Scheduler`, state/resume, failure
   isolation, backup.
7. **Analytics & dashboard** — metrics service + multipage Streamlit app (overview, sources,
   analytics, search, health, config, export CSV/Excel).
8. **Extension layers (real interfaces, no fakes)** — AI enrichment, graph (Graphiti),
   MCP registry, internal REST API skeleton.
9. **Product polish** — config UI, demo-data generator, tests, Docker, CI, docs, screenshots.

---

## 3. Proposed Architecture

### 3.1 Key architectural decision — a dedicated `job_monitor/` package

The instructions sketch a flat layout (`scrapers/`, `dashboard/`, … at repo root). I deviate
deliberately (PHASE 3 explicitly permits a better architecture) and place **all application
code in a single installable package `job_monitor/`**, leaving the upstream `scrapling/`
library untouched.

**Rationale:**
- Prevents import/namespace collisions with the library (Scrapling already owns concepts like
  `spiders`, `engines`).
- Keeps "library we reuse" and "product we build" cleanly separated — exactly the story a
  portfolio reviewer wants to see.
- Makes the app `pip install -e .`-able, importable in tests, and Docker-friendly.
- Thin root entrypoints (`main.py`, `generate_demo_data.py`) preserve the familiar UX from the
  instructions while delegating to the package.

### 3.2 Layered design (dependencies point downward only)

```
            ┌─────────────────────────────────────────────────────────┐
 Interfaces │   CLI (main.py)   Streamlit dashboard   REST API (skel)  │
            └───────────────┬─────────────────────────────┬───────────┘
                            │                             │
            ┌───────────────▼─────────────────────────────▼───────────┐
 Orchestr.  │  PipelineRunner (concurrent)   Scheduler   StateStore    │
            └───────────────┬─────────────────────────────────────────┘
                            │
            ┌───────────────▼─────────────────────────────────────────┐
 Services   │  Enrichment   Analytics   Notifications   Backup/Archive │
            └───────────────┬─────────────────────────────────────────┘
                            │
            ┌───────────────▼─────────────────────────────────────────┐
 Domain     │  JobRecord model   Normalizer   Repositories (SQLite)   │
            └───────────────┬─────────────────────────────────────────┘
                            │
            ┌───────────────▼─────────────────────────────────────────┐
 Acquisition│  BaseScraper → {RemoteOK, WWR, Freelancer, Fiverr,      │
            │  Wellfound}  ── wraps ──►  Scrapling Fetcher / Selector  │
            └─────────────────────────────────────────────────────────┘
```

### 3.3 Package layout

```
job_monitor/
  config/        settings.py (pydantic-settings), keywords.py (keywords, weights, taxonomy)
  models/        job.py (JobRecord), health.py, snapshot.py, change.py
  scrapers/      base.py, remoteok.py, weworkremotely.py, freelancer.py,
                 fiverr.py, wellfound.py, registry.py, http.py (Scrapling adapter)
  normalizers/   normalizer.py
  pipeline/      enrichment.py, runner.py, filters.py
  database/      connection.py, schema.sql, repository.py
  notifications/ base.py, telegram.py, formatters.py
  analytics/     metrics.py, exporters.py
  dashboard/     app.py, pages/*, components.py
  services/      state.py, backup.py, archive.py
  ai/            enrichment.py            (interfaces only)
  graph/         base.py, graphiti_adapter.py
  mcp/           registry.py, config.py
  api/           app.py                   (FastAPI skeleton)
  observability/ logging.py (rotating, structured)
  scheduler.py
main.py · generate_demo_data.py · requirements*.txt · .env.example
docker-compose.yml · Dockerfile.app · .github/workflows/
```

### 3.4 Data contract (canonical record)

Every scraper returns the raw shape from the instructions; the normalizer maps it to the
canonical `JobRecord` (pydantic). DB columns extend it with monitor metadata:

`source, title, company, url (unique), description, posted_at, location, salary, tags(JSON),
score, category, skills(JSON), quality_score, remote, first_seen, last_seen, notified,
content_hash`. Companion tables: `job_history`, `source_health`, `daily_snapshots`.

### 3.5 Design patterns applied

- **Repository pattern** for all DB access (no SQL leaks into services/UI).
- **Strategy / registry** for scrapers (sources are pluggable + config-toggled).
- **Service layer** for enrichment, analytics, notifications.
- **Interface/adapter** for notifications, AI, graph, MCP (swap implementations freely).
- **Dependency injection** of `Settings` and repositories into services (testability).
- **Pydantic models + dataclasses** for typed, validated data flow.

---

## 4. Development Phases

| Phase | Theme | Outcome |
| --- | --- | --- |
| **0** | Planning | These four docs (this plan, TASKS, PORTFOLIO_RECOMMENDATIONS, HANDOVER). |
| **A** | Foundations | Package skeleton, `Settings`, keyword taxonomy, `JobRecord`, logging, DB schema + repositories. |
| **B** | Acquisition | `BaseScraper` + Scrapling HTTP adapter, 5 source scrapers, registry, normalizer. |
| **C** | Intelligence | Scoring, classification, skill extraction, quality score, dedup + change detection, filters. |
| **D** | Orchestration | Telegram notifier, concurrent runner, scheduler, state/resume, health, failure isolation, backup/archive. |
| **E** | Product surface | Analytics service, exporters, multipage Streamlit dashboard, demo-data generator. |
| **F** | Extensibility | AI-enrichment / graph / MCP / REST-API interfaces (real abstractions, no fakes). |
| **G** | Production polish | Tests (pytest), Docker + compose, GitHub Actions, README/CHANGELOG/screenshots, git init. |

Each phase follows the cycle from `claude_start.md`: **Plan → Implement → Test → Document →
Update HANDOVER**, with incremental commits.

---

## 5. Estimated Complexity

| Phase | Complexity | Notes / main risk driver |
| --- | --- | --- |
| A | Medium | Schema design must anticipate later features to avoid migrations. |
| B | High | Each site has its own DOM/anti-bot behavior; markup drifts over time. |
| C | Medium | Mostly deterministic text processing; well unit-testable. |
| D | Medium-High | Concurrency + scheduling + graceful shutdown + secret handling. |
| E | Medium-High | Streamlit multipage UX and chart polish are time-consuming. |
| F | Low-Medium | Interfaces only; the discipline is "no fakes." |
| G | Medium | CI must run without network/browsers; Docker layering. |

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Source HTML/endpoints change or block scrapers | Scrapers silently break | Per-source parsers isolated; health tracking; fixture-based tests; Scrapling stealth fallback; failure isolation so one source never halts the run. |
| Anti-bot blocking (Wellfound/Fiverr/Freelancer) | Empty results | Prefer JSON/RSS endpoints; `curl_cffi` impersonation; documented optional `StealthyFetcher` path; demo-data mode for reliable showcasing. |
| Python 3.14 vs Playwright pin | Browser fetch unavailable | Architecture runs fully on the HTTP layer; browser fetch is optional and feature-detected. |
| Secret leakage (Telegram token already committed in `instructions.md`) | Credential exposure | Secrets only via `.env` (gitignored); `.env.example` holds placeholders; **HANDOVER flags the committed token for rotation.** |
| Scope (40+ advanced requirements) vs. quality | Half-built features | Core path fully working end-to-end; advanced/optional items are real, documented interfaces with clear extension points — never stubs that pretend to work. |
| Legal/ToS of scraping | Reputational | Respect robots where applicable, conservative rate limits, public endpoints only, documented disclaimer. |

---

## 7. Dependencies

**Runtime (core, installed & verified):** `lxml`, `cssselect`, `orjson`, `tld`, `w3lib`,
`typing_extensions`, `curl_cffi` (Scrapling stack) · `pydantic`, `pydantic-settings`,
`python-dotenv` (config/models).

**Runtime (app):** `apscheduler` (scheduling) · `httpx` (Telegram API) · `pandas`,
`openpyxl` (export) · `tenacity` (retries).

**Dashboard:** `streamlit`, `plotly`.

**Optional/extension:** `fastapi` + `uvicorn` (API skeleton), `mcp` (Scrapling already
provides), `graphiti-core` (graph, optional import-guarded).

**Dev:** `pytest`, `pytest-cov`, `ruff`/`flake8` (lint, CI).

All pinned in layered requirements files: `requirements.txt` (core+app),
`requirements-dashboard.txt`, `requirements-dev.txt`, plus `[project.optional-dependencies]`
groups in `pyproject` for the monitor.

---

## 8. Priority Matrix

| Priority | Items | Why |
| --- | --- | --- |
| **P0 (must work end-to-end)** | Config, model, normalizer, DB+repository, ≥2 working scrapers (RemoteOK JSON, WWR RSS), enrichment, dedup, runner, Telegram, dashboard overview, demo data, tests, README. | This is the demonstrable product spine. |
| **P1 (high portfolio value)** | Remaining 3 scrapers, scheduler, health monitoring, analytics charts, search, export, change detection, Docker, CI. | Turns the spine into a credible SaaS. |
| **P2 (differentiators / future)** | AI enrichment, graph, MCP, REST API, config UI, archive/backup, snapshots, observability page. | Signals senior architecture and roadmap thinking. |

---

## 9. Definition of Done (per the success criteria)

- `python main.py --once` runs a full scrape→store→notify cycle (or `--demo` with no network).
- `streamlit run job_monitor/dashboard/app.py` shows populated metrics, charts, search, export.
- `docker compose up` brings up scheduler + dashboard with persistent SQLite, zero extra config.
- `pytest` is green; CI runs lint + tests on push/PR without network or browsers.
- Docs (README, this plan, TASKS, HANDOVER, CHANGELOG) are coherent and current.
- No hardcoded secrets; no monolithic scripts; layered, typed, documented code.
