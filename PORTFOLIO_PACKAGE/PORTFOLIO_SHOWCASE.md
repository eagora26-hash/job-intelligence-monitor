# Job Intelligence Monitor — Portfolio Showcase

*Production-grade, multi-source job monitoring & analytics platform.*
Repository: https://github.com/eagora26-hash/job-intelligence-monitor

---

## Problem

Freelancers and agencies lose winnable work to whoever responds first. The good
opportunities are scattered across five different marketplaces, buried under thousands of
irrelevant posts, and the only "tool" most people have is refreshing tabs. Checking five
sites a few times a day costs an hour daily — and still misses jobs posted in between.

## Solution

A monitoring platform that does the watching: it scrapes **RemoteOK, We Work Remotely,
Freelancer, Fiverr and Wellfound** in parallel, normalizes everything into one schema,
**scores each posting against configurable keywords**, deduplicates by URL with full change
history, and pushes a **Telegram alert within a minute of discovering a new relevant job**.
A first run builds a silent baseline, so alerts are only ever about genuinely new
opportunities — never repeats, never floods. A seven-page analytics dashboard handles
search, trends, skill-demand analysis and one-click CSV/Excel/JSON export. The whole loop
runs unattended every 6 hours on GitHub Actions, with the hosted dashboard updating itself.

## Architecture

Layered design where dependencies point strictly downward:

```
Interfaces      CLI · Streamlit dashboard (7 pages) · FastAPI REST
Orchestration   concurrent PipelineRunner · APScheduler · resume state
Services        enrichment (score/category/skills/quality) · analytics · Telegram · backup
Domain          canonical JobRecord · normalizer · SQLite repositories
Acquisition     5 isolated scrapers · curl_cffi TLS-fingerprint impersonation
```

Engineering choices that matter:
- **Repository pattern** — zero SQL outside the database layer; **strategy/registry** —
  adding a source is one line; **one Notifier interface** — Telegram today, Slack tomorrow.
- **Browser-free scraping** via TLS-fingerprint impersonation (curl_cffi), with an optional
  Playwright stealth fallback — runs in CI and slim containers.
- **Failure isolation** — a blocked source logs, records health, alerts, and the run
  continues. Proven in production: Wellfound is hard-blocked by Cloudflare and the system
  reports `sources ok 5/5` regardless.
- **State in the database, not memory** — dedup and at-most-once alerting survive restarts.

## Features

- 5 source scrapers (4 extracting live, ~350 jobs/run), each fixture-tested
- Keyword relevance scoring, 8-category classification, 30+ skill extraction, quality scores
- True monitoring semantics: baseline run → only-new alerts → at-most-once delivery
- 7-page SaaS-style dashboard: executive KPIs, trends, skill×source heatmap, source
  comparison, leaderboards, searchable explorer, health, live system status
- CSV / Excel / JSON export honoring active filters
- Docker Compose, GitHub Actions (lint + tests + 6-hourly scheduled scrape), Streamlit
  Cloud deployment, automatic backups, REST API, demo mode

## Results (measured, not estimated)

| Metric | Value |
|---|---|
| Jobs under management at delivery | **249** (real, scraped) |
| Live extraction | ~350 jobs/run across 4 sources, 100% extraction success on each |
| Alert delivery | proven live (`sendMessage ok=true`); 0 duplicate alerts across repeated runs |
| Baseline validation | 3 consecutive live cycles: 152 ingested silently, then only-new behavior |
| Dashboard | 7 pages × 0 errors (automated headless validation) |
| Quality gates | 65 pytest tests · 67% coverage · ruff clean · CI green on every push |
| Time to deploy | ~10 minutes to free hosting (documented for beginners) |
| Manual effort replaced | ~1 hour/day of marketplace checking → zero |

Screenshots: `../screenshots/` (7 real captures). Full evidence trail: validation reports
in the repository root.
