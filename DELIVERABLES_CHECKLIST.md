# Deliverables Checklist

Every delivered feature, verified at delivery (2026-06-10). Evidence column references the
validation trail.

## Core platform
- ✅ **5 source scrapers** (RemoteOK, We Work Remotely, Freelancer, Fiverr, Wellfound) — 4 extracting live (~350 jobs/run); Wellfound parser ready, site blocks at network level *(SCRAPER_VALIDATION_REPORT.md)*
- ✅ **Normalization layer** — one canonical job record across all sources
- ✅ **Relevance scoring** — weighted keywords, stored, sortable
- ✅ **Auto-categorization** — 8 categories
- ✅ **Skill extraction** — 30+ skills tracked
- ✅ **Data-quality scoring** — per-job completeness score
- ✅ **SQLite database** — 249 real jobs at delivery; URL dedup, change history, health, snapshots
- ✅ **Change detection** — content-hash diff into `job_history` audit table
- ✅ **Concurrent pipeline** — sources scraped in parallel, failures isolated

## Notifications
- ✅ **Telegram alerts** — live-delivery proven (`sendMessage ok=true`) *(TELEGRAM_VALIDATION_REPORT.md)*
- ✅ **Baseline behavior** — first run ingests silently, one summary message *(validated over 3 live cycles)*
- ✅ **Only-new alerting** — at-most-once per job, state in DB, survives restarts
- ✅ **Noise controls** — relevance threshold, per-source allow-list, 15/run cap + rollup
- ✅ **Daily summary / startup / error messages** — implemented behind one Notifier interface

## Dashboard (7 pages, all error-free against real data)
- ✅ **Overview** — executive KPIs + smart-intelligence band
- ✅ **Insights** — daily/weekly trends, skill×source heatmap, source comparison, leaderboards
- ✅ **Job Explorer** — search, faceted filters, sortable results
- ✅ **Source Health** — per-source reliability + system metrics
- ✅ **System Status** — latest alerts/scrapes/exports, DB statistics
- ✅ **Portfolio Showcase** — self-explaining product page
- ✅ **Configuration** — sources/keywords/notifications without code

## Exports
- ✅ **CSV export** — verified (80 KB, 229 rows at validation)
- ✅ **Excel export** — verified (valid `.xlsx`, `Jobs` sheet)
- ✅ **JSON export** — verified (parseable array of records)
- ✅ Exports respect active dashboard filters *(EXPORT_VALIDATION_REPORT.md)*

## Automation & operations
- ✅ **Scheduler** — local loop (`--loop`, graceful shutdown) + GitHub Actions cron (6 h), running green in production
- ✅ **CLI** — `--once / --loop / --demo / --status`
- ✅ **Resume state** — `data/state.json`, atomic writes
- ✅ **Backups** — automatic, 30-day retention; restore documented
- ✅ **Archive** — old-job archive database
- ✅ **Logging** — structured, rotating
- ✅ **Docker** — `docker compose up` brings up scheduler + dashboard (config validated)
- ✅ **CI** — Lint + Tests workflows, green on GitHub

## Extensions (working interfaces)
- ✅ **REST API** — FastAPI, 7 endpoints, test-covered
- ✅ **AI enrichment seam** — working rule-based enricher + LLM-ready interface
- ✅ **Knowledge graph** — in-memory store + optional Graphiti adapter
- ✅ **MCP plugin registry** — 2 working plugins

## Quality & documentation
- ✅ **65 automated tests** (pytest), 67% coverage, ruff lint clean
- ✅ **Installation guide** (non-technical) — INSTALLATION.md
- ✅ **User guide** — USER_GUIDE.md
- ✅ **Admin guide** — ADMIN_GUIDE.md
- ✅ **Deployment guide** — STREAMLIT_DEPLOYMENT_PACKAGE.md / DEPLOY_STREAMLIT.md
- ✅ **Architecture docs** — README.md (Mermaid diagrams), docs/ARCHITECTURE.md
- ✅ **Validation reports** — scraper / Telegram / dashboard / export / final
- ✅ **7 real dashboard screenshots** — `screenshots/`

## Known limitations (disclosed)
- ⚠️ Wellfound: live extraction blocked by Cloudflare at IP level (needs residential egress); disabled in scheduled runs
- ⚠️ Telegram token must be rotated by the owner before public showcase (original was exposed in the project brief)
- ⚠️ Screenshots 6–10 (Telegram client, export viewers, Docker, CI) require the owner's devices — capture guide provided
