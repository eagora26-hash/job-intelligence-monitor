# Changelog

All notable changes to the Job Intelligence Monitor application are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and the project
aims to follow [Semantic Versioning](https://semver.org/).

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
