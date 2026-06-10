# Portfolio Showcase — Multi-Source AI Job Intelligence Monitor

## Project summary

A production-grade job-intelligence platform that continuously scrapes five job/freelance
marketplaces, normalizes everything into one canonical schema, scores each opportunity for
relevance, stores it in SQLite with dedup + change history, pushes instant Telegram alerts
for high-value matches, and serves a five-page Streamlit analytics dashboard — deployable to
Streamlit Community Cloud with scheduled scraping via GitHub Actions.

## Key features

- **5 source scrapers** (RemoteOK, We Work Remotely, Freelancer, Fiverr, Wellfound), each
  isolated, fixture-tested, and failure-contained — one blocked source never stops a run.
- **Normalization layer**: no source-specific shape leaks past the scrapers.
- **Enrichment pipeline**: keyword relevance scoring, 8-category auto-classification, skill
  extraction (30+ skills), data-quality scoring.
- **Smart persistence**: URL-deduplication, change detection with full `job_history`,
  source-health tracking, daily snapshots, archive + 30-day backups.
- **Telegram alerts**: new-job alerts (score-gated), daily summaries, rate-capped, at-most-once
  per job — validated live.
- **Dashboard**: overview KPIs, Plotly analytics, searchable/filterable job explorer,
  CSV/Excel/JSON export, source health, no-code configuration page.
- **Ops**: CLI (`--once/--loop/--demo/--status`), APScheduler loop, resume-state, structured
  rotating logs, Docker Compose, GitHub Actions (lint + tests + scheduled scrape), demo mode.
- **Extension seams**: rule-based AI enricher (LLM-ready interface), knowledge-graph store,
  MCP plugin registry, FastAPI REST API.

## Architecture highlights

- Layered, dependencies point downward only: interfaces → orchestration → services → domain →
  acquisition (Mermaid diagrams in [README.md](README.md) / [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)).
- Repository pattern (zero SQL outside `database/`), strategy/registry for pluggable sources,
  service layer, dependency-injected `Settings` (pydantic-settings), typed models end-to-end.
- Reuses the vendored **Scrapling** engine's `Selector` parser + `curl_cffi` browser-fingerprint
  impersonation — browser-free runtime with an optional Playwright stealth fallback.
- 64 pytest tests (72% coverage), ruff-clean, CI on 3.11/3.12.

## Technologies

Python · Scrapling · curl_cffi · lxml · pydantic / pydantic-settings · SQLite · APScheduler ·
httpx · tenacity · pandas / openpyxl · Streamlit · Plotly · FastAPI · Docker · GitHub Actions ·
pytest · ruff · Telegram Bot API · (optional) Playwright/Patchright stealth browsing

## Business value

- **For job seekers / freelancers**: one feed of scored, deduplicated opportunities across 5
  marketplaces with instant alerts — minutes-to-opportunity instead of manual browsing.
- **For clients**: the same architecture is a template for any monitor-and-alert product —
  price tracking, lead generation, tender/RFP watching, competitor monitoring.
- **Demonstrated reliability**: honest anti-bot handling, health metrics, failure isolation,
  resume capability — the traits production scraping contracts actually require.

## Screenshots

See [SCREENSHOT_CHECKLIST.md](SCREENSHOT_CHECKLIST.md) — five real dashboard captures are in
`screenshots/` (overview, analytics, explorer, source health, configuration); Telegram /
Docker / CI captures are listed with exact instructions.

## Demo video script (2–3 min)

1. *(0:00)* "Five job boards, one intelligence feed" — show README architecture diagram.
2. *(0:20)* `python main.py --once` — live scrape: 347 jobs in, ~120 new, 15 Telegram alerts.
3. *(0:50)* Show the Telegram chat receiving "🚀 NEW JOB" alerts.
4. *(1:10)* Dashboard Overview: KPIs, jobs by source, top opportunities.
5. *(1:30)* Analytics: trends, categories, skills demand.
6. *(1:50)* Job Explorer: search "python", filter score ≥ 10, export CSV/Excel/JSON.
7. *(2:20)* Source Health + Configuration pages: ops visibility, no-code settings.
8. *(2:40)* Close: `docker compose up` + GitHub Actions green badges.

## Fiverr gig description

> **I will build a custom job/data monitoring bot with Telegram alerts and a live dashboard**
>
> Get every opportunity the moment it appears. I build production-grade monitoring systems
> that scrape multiple websites (even anti-bot protected ones), deduplicate and score results
> by *your* keywords, and alert you instantly on Telegram — plus a beautiful live analytics
> dashboard you can open from any device.
>
> ✔ Multi-site scraping (APIs, RSS, JS pages) ✔ Smart keyword scoring & categories
> ✔ Telegram/Slack/email alerts ✔ Searchable dashboard with CSV/Excel export
> ✔ Runs 24/7 (Docker / GitHub Actions / cloud) ✔ Clean, documented, tested code
>
> Portfolio: a 5-source job-intelligence platform — live dashboard, 60+ tests, CI/CD.
> Tell me what you want monitored, and I'll deliver a system that never misses it.

## Freelancer profile description

> **Python Automation & Web-Scraping Engineer — Monitoring Systems Specialist**
>
> I design end-to-end data pipelines: multi-source scraping (anti-bot aware via TLS
> fingerprint impersonation), normalization, SQLite/Postgres storage with deduplication and
> change history, real-time Telegram/Slack alerting, and Streamlit/Plotly dashboards with
> exports. Recent build: a job-intelligence monitor aggregating RemoteOK, We Work Remotely,
> Freelancer and Fiverr — concurrent scrapers, relevance scoring, health monitoring, Docker +
> GitHub Actions CI, 64 automated tests. I deliver maintainable, typed, tested code with
> documentation a client's next developer can pick up cold.

## GitHub project description

> 🛰️ **Job Intelligence Monitor** — production-grade multi-source job scraping & monitoring
> platform: 5 scrapers (anti-bot aware), keyword relevance scoring, SQLite with dedup +
> change history, Telegram alerts, Streamlit/Plotly analytics dashboard, CSV/Excel/JSON
> export, Docker, GitHub Actions CI + scheduled scraping, Streamlit Cloud ready.
> Python · Scrapling · pydantic · pandas · FastAPI.
