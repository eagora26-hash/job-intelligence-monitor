# Upwork Portfolio Project Description

## Title
Job Intelligence Monitor — 5-Source Scraping Platform with Telegram Alerts & Analytics

## Short description (project summary line)
Production Python platform monitoring 5 job marketplaces: concurrent anti-bot-aware
scraping, keyword relevance scoring, only-new Telegram alerts, 7-page Streamlit analytics
dashboard, CSV/Excel/JSON export, Docker + GitHub Actions CI/CD.

## Long description (project details)

A complete monitoring product I architected, implemented, tested and deployed — from
scraper to hosted dashboard.

**Challenge.** Opportunities scatter across five marketplaces and the good ones go to the
fastest responder. The client profile (freelancer/agency) needed one scored feed and
instant alerts, with zero recurring infrastructure cost.

**What I built.**
- *Acquisition*: five isolated scrapers running concurrently; TLS-fingerprint impersonation
  (curl_cffi) passes anti-bot checks browser-free; per-source failure isolation means one
  blocked site never stops the pipeline. When one source (Fiverr) silently changed its
  markup, I diagnosed the new embedded-JSON format and restored extraction (0 → ~90
  records/run).
- *Intelligence*: weighted keyword scoring, 8-category auto-classification, 30+ skill
  extraction, data-quality scores; URL deduplication with field-level change history.
- *Alerting*: Telegram notifications engineered as a true monitoring system — first run
  builds a silent baseline, then only never-seen-before jobs alert, at most once each,
  with state persisted in the database (validated live across consecutive runs).
- *Product*: 7-page analytics dashboard (executive KPIs, trend analysis, skill-demand
  heatmap, source benchmarking, leaderboards, searchable explorer, health/system pages),
  exports in three formats.
- *Operations*: Docker Compose; GitHub Actions running lint, a test matrix and a 6-hourly
  scheduled scrape that refreshes the hosted dashboard automatically; automatic backups;
  resume-safe state.

**Outcome.** 249 real jobs under management at delivery; ~350 jobs/run live extraction;
65 automated tests (67% coverage); all CI green; documentation a non-technical client can
operate from. Live demo + repository available.

## Key features
Multi-source concurrent scraping · anti-bot TLS impersonation · keyword scoring &
classification · baseline/only-new Telegram alerts · analytics dashboard · 3 export
formats · Docker · CI/CD · free-tier cloud deployment

## Deliverables (for similar engagements)
Source code (your repo) · deployed dashboard · configured alert bot · full documentation ·
test suite + CI · handoff support

## Ideal clients
Companies replacing manual monitoring with automation · agencies needing lead-gen feeds ·
recruiters tracking market demand · founders who want a data product built right the first
time.

## Skills to tag
Python · Web Scraping · Data Extraction · Automation · Telegram API · Streamlit · Data
Visualization · SQLite · Docker · CI/CD · ETL · pandas
