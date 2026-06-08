# HANDOVER — Multi-Source AI Job Intelligence Monitor

> **Single source of truth for project state.** Any engineer (human or AI) can resume from:
> `instructions.md` → `claude_start.md` → `IMPLEMENTATION_PLAN.md` → `TASKS.md` → this file.
> Last updated: **2026-06-09** (Phases 0–G complete — v1.0).

---

## Current Project Status

✅ **COMPLETE (v1.0).** All planned phases (0–G) are done. The product runs end-to-end and is
verified: **63 tests pass** (`pytest -c pytest_job_monitor.ini`, 71% coverage), **lint is clean**
(ruff), a **live `--once` scrape** stored real jobs, the **dashboard renders all 5 pages**
headlessly, the **REST API** is TestClient-verified, and the repo is a **git repo on `main` with
8 layered commits** (no secrets committed). Docker + CI are in place.

---

## Current Architecture

Installable-style package **`job_monitor/`** reusing Scrapling's **`Selector`** parser + the
**curl_cffi** impersonation backend (not Scrapling's Playwright-coupled `Fetcher`). Layered:

- **Interfaces:** `main.py` CLI (`--once/--loop/--demo/--status`); Streamlit dashboard
  (`job_monitor/dashboard/app.py`); FastAPI (`job_monitor/api/app.py`).
- **Orchestration:** `pipeline/runner.py` (concurrent), `scheduler.py`, `services/state.py`.
- **Services:** `pipeline/enrichment.py`, `analytics/`, `notifications/`, `services/{backup,archive,demo}`.
- **Domain:** `models/`, `normalizers/`, `database/` (repository pattern).
- **Acquisition:** `scrapers/` (BaseScraper + 5 sources + registry + curl_cffi http).
- **Extensions:** `ai/`, `graph/`, `mcp/`, `api/` (real interfaces, no fakes).

Flow: scrape (concurrent) → normalize → enrich → filter → upsert (dedup + change detection) →
notify → checkpoint state → daily snapshot. Diagrams in [README.md](README.md) +
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Completed Tasks

All of Phases 0–G (see [TASKS.md](TASKS.md) for the checked board):
- **0** Governance docs + analysis + venv.
- **A** Config, taxonomy, models, logging, SQLite repositories (dedup + change detection).
- **B** HTTP adapter, 5 scrapers, registry, normalizer (RemoteOK live-verified).
- **C** Enrichment (score/category/skills/quality) + filters.
- **D** Telegram notifier, concurrent runner, scheduler, state, health, backup/archive, CLI.
- **E** Analytics, exporters, demo generator, Streamlit dashboard.
- **F** AI / graph / MCP / REST-API extension layers.
- **G** Docker + compose, GitHub Actions (lint + tests), README + docs, CHANGELOG/ROADMAP, git.

---

## Pending Tasks

None for v1.0. Future enhancements are tracked in [ROADMAP.md](ROADMAP.md) and
[PORTFOLIO_RECOMMENDATIONS.md](PORTFOLIO_RECOMMENDATIONS.md) (LLM digest, Slack/email notifiers,
more sources, hosted demo, Postgres + migrations, saved searches).

---

## Next Recommended Action

The project is shippable. Highest-value next steps if continuing:
1. **Capture the 6 screenshots** (see `screenshots/README.md`) so the README renders fully — seed
   with `python generate_demo_data.py`, run the dashboard, screenshot.
2. **Rotate the Telegram token** (see Known Issues #1) and set the real one in `.env`.
3. Push to a GitHub remote so the CI badges go live (workflows already added).
4. Pick the first ROADMAP item (LLM daily digest via the `ai/` seam) if extending.

---

## Important Decisions

1. **Dedicated `job_monitor/` package** (not the flat root layout) — clean separation from the
   vendored Scrapling library.
2. **curl_cffi + Scrapling `Selector`** instead of Scrapling's `Fetcher` — browser-free runtime
   (verified: suite passes with playwright uninstalled). Stealth is an optional lazy fallback.
3. **Fiverr/Wellfound = honest best-effort** — parse public embedded JSON; return `[]` (never
   fabricate) when blocked; demo mode covers presentation.
4. **Relevance gate** at `score ≥ 1` for storage; notifications gate separately on `NOTIFY_MIN_SCORE`.
5. **Secrets only via gitignored `.env`.** Build-brief files (`instructions.md`, `claude_start.md`)
   are gitignored because they contain the real token — kept locally for resumability, never published.
6. **8 layered git commits** on `main` tell the build story; baseline isolates the vendored library.

---

## Dependencies

**Runtime/core:** lxml, cssselect, orjson, tld, w3lib, typing_extensions, curl_cffi, pydantic,
pydantic-settings, python-dotenv, apscheduler, httpx, tenacity, pandas, openpyxl.
**Dashboard:** streamlit, plotly. **API (optional):** fastapi, uvicorn. **Dev:** pytest,
pytest-cov, ruff. Pinned in `requirements.txt`, `requirements-dashboard.txt`,
`requirements-api.txt`, `requirements-dev.txt`. **playwright intentionally NOT required.**

---

## Known Issues

1. **⚠️ SECURITY — exposed Telegram token.** The original `instructions.md` (~line 239) contains a
   real bot token + chat id in plaintext → treat as compromised, **rotate via @BotFather**. It is
   present only in the local (gitignored) `.env` and the gitignored `instructions.md`; **verified
   absent from all git-tracked content**. `.env.example` holds empty placeholders.
2. **Live runs send real Telegram messages** when `.env` has a valid token + `NOTIFY_ENABLED=true`.
   Use `NOTIFY_ENABLED=false` for safe local testing.
3. **Fiverr/Wellfound** usually return 0 jobs without a browser (anti-bot) — expected; demo mode
   covers the dashboard; RemoteOK/WWR/Freelancer are the reliable live sources.
4. **Screenshots** in `screenshots/` are placeholders — capture real ones before showcasing.
5. Host is Python 3.14 / PEP 668 → work inside `.venv`. CI targets 3.11/3.12 (broad wheel support).

---

## Session Notes

**Session 1 (2026-06-08 → 06-09):** Built the entire product from the brief: read both specs,
analyzed the Scrapling engine, authored the four governance docs, then implemented Phases A–G with
a per-phase Plan→Implement→Test→Document cycle. Ended with 63 passing tests, clean lint, a
live-verified scrape, a fully-rendering dashboard, a working REST API, Docker + CI, SaaS-grade
docs, and an 8-commit git history with no secrets in VCS. Key decision: decoupled from Scrapling's
Playwright-coupled fetcher (curl_cffi + Selector) for a browser-free, CI/Docker-friendly runtime.
Project is at v1.0 and shippable.
