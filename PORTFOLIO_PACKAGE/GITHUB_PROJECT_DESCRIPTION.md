# GitHub Project Description

## Repository "About" (max ~350 chars)

> 🛰️ Production-grade job intelligence platform: 5 marketplaces scraped concurrently
> (anti-bot aware), keyword relevance scoring, only-new Telegram alerts, 7-page Streamlit
> analytics dashboard, CSV/Excel/JSON export, Docker, GitHub Actions CI + scheduled
> scraping, Streamlit Cloud ready. 65 tests.

## Topics (repository tags)

`python` `web-scraping` `automation` `telegram-bot` `streamlit` `plotly` `data-engineering`
`monitoring` `sqlite` `docker` `github-actions` `fastapi` `dashboard` `etl` `job-search`

## README intro paragraph (if needed standalone)

**Job Intelligence Monitor** turns five job marketplaces (RemoteOK, We Work Remotely,
Freelancer, Fiverr, Wellfound) into one scored, deduplicated opportunity feed. Concurrent
scrapers with TLS-fingerprint impersonation collect ~350 postings per run; an enrichment
pipeline scores each against configurable keywords, classifies it into 8 categories and
extracts 30+ skills; SQLite persistence provides URL deduplication with full change
history; and a Telegram engine alerts **only on never-seen-before matches** (a first run
silently establishes the baseline). A 7-page Streamlit dashboard adds trend analytics, a
skill-demand heatmap, source benchmarking, full-text search and one-click CSV/Excel/JSON
export. The whole loop runs free: GitHub Actions scrapes every 6 hours and the hosted
dashboard redeploys itself with fresh data.

## Social preview / pinned-repo tagline

Five job boards. One scored feed. Telegram pings only for what's new.
