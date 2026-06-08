# HANDOVER — Multi-Source AI Job Intelligence Monitor

> **Single source of truth for project state.** Any engineer (human or AI) can resume from:
> `instructions.md` → `claude_start.md` → `IMPLEMENTATION_PLAN.md` → `TASKS.md` → this file.
> Last updated: **2026-06-09** (end of Phase D — orchestration).

---

## Current Project Status

Phases **0–D complete**. The product spine runs end-to-end and is validated live:
`python main.py --once` scraped **99 RemoteOK jobs → 13 relevant stored**, and `--status`
reports state + health correctly. **43 unit/integration tests pass** (`pytest -c
pytest_job_monitor.ini`). No network/browser needed for tests. Remaining: Phase E (analytics +
Streamlit dashboard + demo data), Phase F (optional extension interfaces), Phase G (Docker, CI,
README/docs, git init).

---

## Current Architecture

Installable package **`job_monitor/`** that reuses Scrapling's **`Selector`** parser and the
**curl_cffi** impersonation backend (NOT Scrapling's Playwright-coupled `Fetcher` — see
Decision #2). Layers, top→bottom:

- **Interfaces:** `main.py` CLI (`--once/--loop/--demo/--status`); Streamlit dashboard (Phase E).
- **Orchestration:** `pipeline/runner.py` (concurrent `PipelineRunner`), `scheduler.py`
  (APScheduler, graceful shutdown), `services/state.py` (resume).
- **Services:** `pipeline/enrichment.py`, `notifications/` (Telegram + Null + formatters),
  `services/{backup,archive}.py`, analytics (Phase E).
- **Domain:** `models/` (JobRecord, SourceHealth, DailySnapshot, JobChange),
  `normalizers/normalizer.py`, `database/` (SQLite + repository pattern: jobs/history/health/snapshots).
- **Acquisition:** `scrapers/` — `BaseScraper` + 5 sources + registry, on `scrapers/http.py`.

Data flow: **scrape (concurrent) → normalize → enrich (score/category/skills/quality) → filter
(include/exclude + relevance gate) → upsert (dedup + change detection) → notify new → checkpoint
state → write daily snapshot.**

---

## Completed Tasks

- **Phase 0:** four governance docs + repo/Scrapling analysis + venv provisioning.
- **Phase A (15 tests):** package, `Settings` (pydantic-settings), keyword taxonomy, domain
  models, rotating logging, SQLite schema + repositories (dedup + change detection).
- **Phase B (27 tests):** HTTP adapter (curl_cffi + tenacity + lazy stealth fallback),
  `BaseScraper`, 5 scrapers (RemoteOK/WWR/Freelancer/Fiverr/Wellfound), registry, normalizer;
  fixture-based parser tests; **RemoteOK live-verified**.
- **Phase C (35 tests):** `Enricher` (scoring/classification/skills/quality), `JobFilter`.
- **Phase D (43 tests):** Telegram notifier + formatters, concurrent `PipelineRunner`, state
  store, health recording, scheduler, `main.py` CLI, backup + archive services.

---

## Pending Tasks

See [TASKS.md](TASKS.md) Phases **E–G**:
- **E:** analytics service, CSV/Excel exporters, multipage Streamlit dashboard, `generate_demo_data.py`.
- **F:** AI-enrichment / graph / MCP / REST-API interfaces (real, no fakes).
- **G:** pytest config polish, Docker + compose, GitHub Actions, README/CHANGELOG/screenshots,
  `git init` + first commits.

---

## Next Recommended Action

Start **Phase E**: implement `job_monitor/analytics/metrics.py` (totals, by-source, keyword/skill
frequency, daily/weekly trend, health summary, daily-summary dict for Telegram) and
`analytics/exporters.py` (CSV/Excel), then `services/demo.py` + root `generate_demo_data.py`, then
the Streamlit app under `job_monitor/dashboard/`. Seed with `python main.py --demo` and verify the
dashboard renders before moving on.

---

## Important Decisions

1. **Dedicated `job_monitor/` package** (not the flat root layout in instructions) — clean
   separation from the vendored Scrapling library; permitted by claude_start.md PHASE 3.
2. **curl_cffi directly + Scrapling `Selector`**, not Scrapling's `Fetcher`. Reason: importing
   `scrapling.fetchers` pulls in `playwright` at module load; using curl_cffi (the same backend
   `Fetcher` wraps) keeps the app runnable with **no browser stack** in CI/Docker. Verified: full
   suite passes with playwright uninstalled. Playwright `StealthyFetcher` remains a lazy, optional
   fallback (`USE_STEALTH_FALLBACK`).
3. **Fiverr/Wellfound are honest best-effort** — parse public embedded JSON (ld+json /
   `__NEXT_DATA__`); return `[]` (never fabricate) when blocked. Demo mode covers the dashboard.
4. **Relevance gate:** runner stores only jobs with `score ≥ 1` (matched ≥1 keyword), so the niche
   monitor isn't flooded by every remote listing. Notifications gate separately on `NOTIFY_MIN_SCORE`.
5. **Secrets only via gitignored `.env`.** See Known Issues #1.

---

## Dependencies

**Installed & verified:** lxml, cssselect, orjson, tld, w3lib, typing_extensions, curl_cffi,
pydantic, pydantic-settings, python-dotenv, apscheduler, httpx, tenacity, pandas, openpyxl,
pytest, pytest-cov, streamlit, plotly. **Pinned in** `requirements.txt` (core+app),
`requirements-dashboard.txt`, `requirements-dev.txt`. **playwright is intentionally NOT required**
(optional for stealth). Optional future: fastapi+uvicorn (Phase F API), graphiti-core (Phase F graph).

---

## Known Issues

1. **⚠️ SECURITY — exposed Telegram token.** `instructions.md` (~line 239) contains a real bot
   token + chat id in plaintext → treat as compromised; **rotate via @BotFather**. The app reads
   it only from the gitignored `.env`; `.env.example` holds placeholders.
2. **Live runs send real Telegram messages** when `.env` has a valid token and `NOTIFY_ENABLED=true`.
   For safe local testing use `NOTIFY_ENABLED=false` (as done during `--once` verification).
3. **Fiverr/Wellfound** typically return 0 jobs without a browser (anti-bot) — expected; demo mode
   covers presentation. RemoteOK/WWR/Freelancer are the reliable live sources.
4. **Not yet a git repository** — `git init` is Phase G (Task G.6); `.gitignore` already authored.
5. Host is Python 3.14 / PEP 668 → all work inside `.venv`.

---

## Session Notes

**Session 1 (2026-06-08 → 06-09):** Completed Phases 0–D. Built the full acquisition → intelligence
→ persistence → orchestration → notification spine with 43 passing tests and a live-verified
end-to-end run. Key engineering decision: decoupled from Scrapling's Playwright-coupled fetcher in
favor of curl_cffi + Scrapling's Selector for a browser-free, CI/Docker-friendly runtime. Next
session starts at Phase E (analytics + dashboard + demo data).
