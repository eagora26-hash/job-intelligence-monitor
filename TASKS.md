# Task Board — Multi-Source AI Job Intelligence Monitor

> Granular, resumable task list. Each task: **objective · files · dependencies · expected
> output · priority**. Status legend: `[ ]` todo · `[~]` in progress · `[x]` done.
> Keep in sync with [HANDOVER.md](HANDOVER.md). Priorities: **HIGH / MEDIUM / LOW**.

---

## Phase 0 — Planning  ✅
- [x] **0.1** Repository + Scrapling engine analysis · *files:* — · *out:* findings in plan · **HIGH**
- [x] **0.2** IMPLEMENTATION_PLAN.md · **HIGH**
- [x] **0.3** TASKS.md (this file) · **HIGH**
- [x] **0.4** PORTFOLIO_RECOMMENDATIONS.md · **HIGH**
- [x] **0.5** HANDOVER.md (initial) · **HIGH**

---

## Phase A — Foundations  ✅
- [x] **A.1** Package skeleton + layered requirements files (`requirements*.txt`) · **HIGH**
- [x] **A.2** `Settings` via pydantic-settings, `.env` loading, source toggles, intervals · **HIGH**
- [x] **A.3** Keyword taxonomy: default keywords, scoring weights, categories, skills, exclude list · **HIGH**
- [x] **A.4** Domain models: `JobRecord`, `SourceHealth`, `DailySnapshot`, `JobChange` · **HIGH**
- [x] **A.5** Structured rotating logging · **MEDIUM**
- [x] **A.6** DB connection + schema + repositories (jobs, history, health, snapshots) · **HIGH**
- [x] **A.7** Unit tests: settings, models, repository (dedup + change detection) — **15 tests green** · **HIGH**
  · *config:* `pytest_job_monitor.ini` (separate from Scrapling's pytest.ini)
  · *note:* `pyproject` app metadata deferred to Phase G alongside packaging/Docker.

## Phase B — Acquisition (scrapers)  ✅
- [x] **B.1** HTTP adapter — **curl_cffi (Scrapling's impersonation backend) + tenacity retries**,
  lazy Playwright `StealthyFetcher` fallback. *Decision:* avoid importing Scrapling's
  Playwright-coupled `Fetcher` so the app runs without browsers. · **HIGH**
- [x] **B.2** `BaseScraper` (abstract; timing + full error isolation via `ScrapeResult`) · **HIGH**
- [x] **B.3** RemoteOK scraper (JSON API) — **live-verified: 99 jobs** · **HIGH**
- [x] **B.4** We Work Remotely scraper (RSS via stdlib XML; `<link>` preserved) · **HIGH**
- [x] **B.5** Freelancer scraper (active-projects JSON API) · **MEDIUM**
- [x] **B.6** Fiverr scraper (public ld+json ItemList; honest empty-on-block) · **MEDIUM**
- [x] **B.7** Wellfound scraper (`__NEXT_DATA__` JSON island; honest empty-on-block) · **MEDIUM**
- [x] **B.8** Source registry/factory honoring config toggles · **HIGH**
- [x] **B.9** Normalizer raw→`JobRecord` (HTML strip, multi-format dates, tags, remote flag) · **HIGH**
- [x] **B.10** Scraper + normalizer tests vs saved fixtures — **27 tests green total** · **HIGH**

## Phase C — Intelligence (enrichment)
- [ ] **C.1** Relevance scoring from keyword weights
  · *files:* `job_monitor/pipeline/enrichment.py` · *deps:* A.3, B.9 · **HIGH**
- [ ] **C.2** Category classification (Automation, Web Scraping, E-commerce, AI, …)
  · *files:* `job_monitor/pipeline/enrichment.py` · *deps:* A.3 · **HIGH**
- [ ] **C.3** Skill extraction (Python, Django, Selenium, Docker, …)
  · *files:* `job_monitor/pipeline/enrichment.py` · *deps:* A.3 · **MEDIUM**
- [ ] **C.4** Data-quality scoring (field completeness)
  · *files:* `job_monitor/pipeline/enrichment.py` · *deps:* B.9 · **MEDIUM**
- [ ] **C.5** Include/exclude/source/date/remote filters (config-driven)
  · *files:* `job_monitor/pipeline/filters.py` · *deps:* A.2,A.3 · **MEDIUM**
- [ ] **C.6** Dedup (unique url) + change detection (content hash → `job_history`)
  · *files:* `job_monitor/database/repository.py`, `job_monitor/pipeline/enrichment.py` · *deps:* A.6 · **HIGH**
- [ ] **C.7** Enrichment/filter/dedup tests
  · *files:* `tests/job_monitor/test_enrichment.py` · *deps:* C.1-C.6 · **HIGH**

## Phase D — Orchestration  ✅
- [x] **D.1** `Notifier` interface + Telegram impl + `NullNotifier` + HTML formatters · **HIGH**
- [x] **D.2** Concurrent `PipelineRunner` (ThreadPool scrape; serialized store; per-source isolation) · **HIGH**
- [x] **D.3** State/resume store (`data/state.json`, atomic writes) · **MEDIUM**
- [x] **D.4** Source health recording (success/failure/latency) wired into runner · **MEDIUM**
- [x] **D.5** Scheduler (interval, graceful shutdown) + `main.py` CLI (`--once/--loop/--demo/--status`)
  — **live-verified `--once`: 99 scraped → 13 relevant stored; `--status` OK** · **HIGH**
- [x] **D.6** Backup (retention) + archive (reuses repository pattern) services · **LOW**
- [x] **D.7** Runner + services tests (fake scrapers, capturing notifier) — **43 tests green** · **MEDIUM**

## Phase E — Product surface  ✅
- [x] **E.1** Analytics service (totals, by-source/category, skill freq, daily trend, score dist, health) · **HIGH**
- [x] **E.2** Exporters (CSV, Excel, JSON; in-memory bytes for dashboard downloads) · **MEDIUM**
- [x] **E.3** Streamlit app shell + nav + cached components + Overview page · **HIGH**
- [x] **E.4** Pages: Analytics (Plotly), Job Explorer (search/filter/export), Source Health/Observability · **HIGH**
- [x] **E.5** Configuration page (toggle sources, edit keywords, notifications; safe `.env` writer) · **MEDIUM**
- [x] **E.6** Demo-data generator (`generate_demo_data.py` + `services/demo.py`) — **150 jobs seeded** · **HIGH**
  · *verified:* all 5 pages render with **0 errors** via Streamlit `AppTest`; **48 tests green**.

## Phase F — Extensibility (interfaces only, no fakes)  ✅
- [x] **F.1** AI enrichment — `AIEnricher` interface + **working** `RuleBasedAIEnricher`
  (insight/summary/digest) + honest `LLMAIEnricher` seam · **MEDIUM**
- [x] **F.2** Graph — `GraphStore` + **working** `InMemoryGraphStore` (Job→Company/Skill/Source/
  Category) + import-guarded `GraphitiAdapter` · **LOW**
- [x] **F.3** MCP — config loader (`servers.json`) + `MCPServerRegistry` + **working** plugins
  (`search_jobs`, `get_analytics`) · **LOW**
- [x] **F.4** REST API — **working** FastAPI app (`/health`, `/jobs`, `/jobs/top`,
  `/analytics/*`, `/sources/health`); TestClient-tested · **LOW**
  · *verified:* **56 tests green** (incl. live API + graph + MCP + AI).

## Phase G — Production polish
- [ ] **G.1** Test suite green + coverage config; `pytest.ini`/`conftest`
  · *files:* `tests/job_monitor/*`, `conftest.py` · *deps:* all tests · **HIGH**
- [ ] **G.2** Dockerfile.app + docker-compose (scheduler + dashboard, SQLite volume, env)
  · *files:* `Dockerfile.app`, `docker-compose.yml`, `.dockerignore` · *deps:* D.5,E.3 · **HIGH**
- [ ] **G.3** GitHub Actions: lint + test on push/PR
  · *files:* `.github/workflows/{lint,test}.yml` · *deps:* G.1 · **HIGH**
- [ ] **G.4** README (SaaS-grade), Mermaid architecture + DB diagrams, screenshots placeholders
  · *files:* `README.md` (or `README_JOB_MONITOR.md`), `screenshots/README.md`, `docs/` · *deps:* most · **HIGH**
- [ ] **G.5** CHANGELOG + ROADMAP + demo-video script
  · *files:* `CHANGELOG.md`, `docs/DEMO_VIDEO.md` · *deps:* — · **MEDIUM**
- [ ] **G.6** git init, `.gitignore`, secret-safe `.env`, incremental commits, final HANDOVER
  · *files:* `.gitignore`, repo · *deps:* all · **HIGH**

---

### Discovered tasks (added as work progresses)
- _(none yet — append here with date as new work is uncovered)_
