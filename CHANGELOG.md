# Changelog

All notable changes to the Job Intelligence Monitor application are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and the project
aims to follow [Semantic Versioning](https://semver.org/).

## [1.2.0] — 2026-06-10

### Added
- **SaaS dashboard redesign** (dark theme + design-system CSS): executive Overview with
  6 KPI cards (incl. Source Health Score) and a smart-intelligence band; **Insights** page
  with weekly trend, skill×source heatmap, source comparison, and job-score / source-
  reliability leaderboards; new **Portfolio Showcase** page (architecture + data flow +
  client value) and **System Status** page (latest alerts, scrapes, exports, DB statistics).
- **Baseline notification semantics**: the first run on an empty database ingests everything
  silently (one summary message, all jobs pre-marked notified); later runs alert **only**
  genuinely new jobs. `NOTIFY_SOURCES` allow-list silences high-churn marketplaces (Fiverr).
  Documented in `TELEGRAM_NOTIFICATION_ARCHITECTURE.md`; validated live over 3 cycles.
- Analytics service: `new_last_24h`, `weekly_trend`, `skill_source_matrix`, `source_stats`,
  `health_score`, `reliability_leaderboard`, `most_active_source`.
- Zero-experience `DEPLOY_STREAMLIT.md` (exact values, steps, validation, troubleshooting).

## [1.1.0] — 2026-06-10

Completion & gap-closure audit release: every subsystem validated live, all closeable gaps
closed. Evidence: `FINAL_VALIDATION_REPORT.md` + per-subsystem validation reports.

### Fixed
- **Fiverr scraper**: rewritten to parse the `perseus-initial-props` JSON data island that
  public subcategory/search pages embed (~48 gigs/page); ld+json kept as legacy fallback;
  listing URLs switched to gig-bearing pages. **0 → ~90 records/run**, fixture-tested.
- **`Settings`**: `populate_by_name=True` — constructor kwargs by field name were silently
  ignored in favor of `.env` values.
- `.streamlit/config.toml`: removed `enableCORS=false` (conflicted with XSRF protection).
- Lint: unused variable in `test_extensions.py`.

### Added
- **JSON export in the dashboard**: `JobExporter.to_json_bytes()` + an `⬇️ Export JSON`
  download button in Job Explorer (CSV/Excel/JSON now all first-class).
- **5 real dashboard screenshots** (headless Chromium, live data) replacing placeholders;
  README image links updated.
- Audit documentation: `REQUIREMENTS_GAP_ANALYSIS.md`, `SCRAPER_VALIDATION_REPORT.md`,
  `TELEGRAM_VALIDATION_REPORT.md`, `DASHBOARD_VALIDATION_REPORT.md`,
  `EXPORT_VALIDATION_REPORT.md`, `DEPLOY_STREAMLIT.md`, `PORTFOLIO_SHOWCASE.md`,
  `SCREENSHOT_CHECKLIST.md`.

### Validated (live)
- Telegram: 15 real alerts delivered + `sendMessage ok=true`; at-most-once dedup proven.
- Scrapers: RemoteOK 100, WWR 61, Freelancer 97, Fiverr ~90 records/run; Wellfound confirmed
  IP-blocked by Cloudflare even via a stealth Chromium (parser remains fixture-validated).
- Dashboard: 5 pages × 0 errors against the real DB; server health endpoint 200.
- Exports: CSV/Excel/JSON files generated and integrity-checked (229 rows each).
- Suite: **64 tests**, 72% coverage, ruff clean.

## [1.0.0] — 2026-06-09

First complete release: a portfolio-grade, multi-source job intelligence platform built on the
vendored Scrapling engine.

### Added
- **Acquisition:** `BaseScraper` + 5 source scrapers (RemoteOK, We Work Remotely, Freelancer,
  Fiverr, Wellfound), a curl_cffi-based `HttpClient` with retries and an optional Scrapling
  stealth fallback, and a config-driven source registry.
- **Domain:** canonical `JobRecord` model + a normalization layer; SQLite persistence via the
  repository pattern with deduplication, change detection (`job_history`), source health, and
  daily snapshots.
- **Intelligence:** relevance scoring, auto-categorization, skill extraction, and data-quality
  scoring; configurable include/exclude/source/date/remote filtering.
- **Orchestration:** concurrent `PipelineRunner` with per-source failure isolation, an
  APScheduler-based scheduler with graceful shutdown, and JSON resume state.
- **Notifications:** `Notifier` interface with a Telegram implementation (new-job alerts, daily
  summary, startup/error) and a `NullNotifier` for when alerts are disabled.
- **Product surface:** `AnalyticsService`, CSV/Excel/JSON exporters, a multipage Streamlit
  dashboard (overview, analytics, explorer, health, configuration), and a demo-data generator.
- **Extensions (real interfaces):** AI enrichment (working rule-based + LLM seam), an in-memory
  knowledge graph (+ optional Graphiti adapter), an MCP config/registry with working plugins,
  and a FastAPI REST API.
- **Ops & docs:** Docker + Docker Compose, GitHub Actions (lint + tests on push/PR), 63 tests,
  and full project documentation (README, architecture, implementation plan, task board,
  handover, roadmap, demo-video script).

### Security
- Secrets are read only from a gitignored `.env`; `.env.example` ships with placeholders.
  The dashboard configuration page refuses to write secret keys.

### Notes
- Decoupled from Scrapling's Playwright-coupled `Fetcher` (uses curl_cffi + Scrapling's
  `Selector`) so the app runs with no browser stack in CI/Docker.
- Fiverr/Wellfound are honest best-effort sources: they parse public embedded JSON and return
  nothing (never fabricated data) when blocked; demo mode covers the dashboard.
