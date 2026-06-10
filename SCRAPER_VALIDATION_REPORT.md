# Scraper Validation Report

**Date:** 2026-06-10 · **Environment:** Python 3.14 venv, Linux, live internet
**Method:** every source executed individually through its real scraper class
(`job_monitor/scrapers/*`), two consecutive full runs, plus a full pipeline run
(`python main.py --once`). A run counts as *successful extraction* only when it yields ≥ 1
usable record.

## Summary

| # | Source | Method | Records (run 1 / run 2) | Extraction rate | Avg latency | Status |
|---|--------|--------|------------------------:|----------------:|------------:|--------|
| 1 | RemoteOK | Public JSON API (`/api`) | 100 / 100 | 100% | ~0.3 s | 🟢 Operational |
| 2 | We Work Remotely | RSS (3 category feeds, stdlib XML) | 61 / 61 | 100% | ~1.2 s | 🟢 Operational |
| 3 | Freelancer | Public active-projects JSON API (4 keyword queries) | 97 / 97 | 100% | ~2.3 s | 🟢 Operational |
| 4 | Fiverr | **`perseus-initial-props` JSON island** (fixed this session) | 89 / 91 | 100% | ~2.9 s | 🟢 Operational |
| 5 | Wellfound | `__NEXT_DATA__` JSON island | 0 / 0 (HTTP 403) | 0% | ~0.4 s | 🔴 Blocked (Cloudflare) |

**4 / 5 sources extract real data over plain HTTP.** Full-pipeline evidence
(`main.py --once`, 2026-06-10): `sources ok 5/5 | scraped 347 | new 118 | updated 2 |
notified 15` — per source: remoteok 100, weworkremotely 61, freelancer 96, fiverr 90,
wellfound 0.

## Per-source detail

### 1. RemoteOK — 🟢 production-ready
- **Extraction method:** public JSON API `https://remoteok.com/api`
  ([remoteok.py](job_monitor/scrapers/remoteok.py)); skips the leading legal-notice element.
- **Records:** 100 per run, both runs identical. Latency 215–403 ms.
- **Sample:** *"Technical support" @ LitePOS* → `https://remoteOK.com/remote-jobs/remote-technical-support-litepos-1133035`.
- **Limitations:** full board returned (relevance gate filters downstream); salary often absent.
- **Anti-bot:** none observed.

### 2. We Work Remotely — 🟢 production-ready
- **Extraction method:** RSS, three category feeds parsed with stdlib XML, `<link>` preserved
  ([weworkremotely.py](job_monitor/scrapers/weworkremotely.py)).
- **Records:** 61 per run (de-duplicated across feeds). Latency ~1.2 s.
- **Sample:** *"Senior Software Engineer II" @ Nomad* → `https://weworkremotely.com/remote-jobs/nomad-senior-software-engineer-ii`.
- **Limitations:** RSS exposes limited fields (no salary; company derived from title prefix).
- **Anti-bot:** none observed.

### 3. Freelancer — 🟢 production-ready
- **Extraction method:** public active-projects JSON API across 4 keyword queries
  ([freelancer.py](job_monitor/scrapers/freelancer.py)).
- **Records:** 97 per run (96–103 across the session). Latency ~2.3 s.
- **Sample:** *"Resume-to-AST Conversion"*, budget `USD 10.0–30.0` →
  `https://www.freelancer.com/projects/cplusplus-programming/Resume-AST-Conversion`.
- **Limitations:** client projects have no company field; budgets are ranges in mixed
  currencies; unofficial API may rate-limit under heavy polling.
- **Anti-bot:** none observed at current cadence.

### 4. Fiverr — 🟢 operational (**fixed this session**)
- **Previous state:** 0 records — the parser targeted an `ld+json ItemList` that Fiverr no
  longer emits.
- **Fix applied:** [fiverr.py](job_monitor/scrapers/fiverr.py) now parses the
  `<script id="perseus-initial-props">` JSON island that public subcategory/search pages embed
  server-side (~48 gigs/page under `listings[].gigs`); the ld+json parse is retained as a
  legacy fallback. Listing URLs switched to gig-bearing pages (the old category *hub* pages
  embed no gigs). New fixture + tests: [fiverr_perseus.html](tests/job_monitor/fixtures/fiverr_perseus.html),
  `test_fiverr_perseus_listing_parsing`.
- **Records:** 89–92 per run. Latency ~2.9 s.
- **Sample:** *"Do python web scraping, with scrapy, selenium, bs4…" @ Farhan M.*,
  `USD 30 (starting)` → `https://www.fiverr.com/muhmd_farhan/automate-web-scr…`.
- **Limitations:** these are seller *gigs* (services offered), not buyer requests — Fiverr has
  no public buyer-request feed. Promoted-gig rotation surfaces a few "new" gigs per run
  (~9 on the second run), which inflates new-job counts slightly. The page is served to
  `curl_cffi` impersonation but **blocks real headless browsers** (PerimeterX "It needs a
  human touch" page) — i.e. the plain-HTTP path is the *reliable* one here.
- **Anti-bot:** PerimeterX on browser traffic; curl_cffi impersonation passes.

### 5. Wellfound — 🔴 blocked (documented honestly)
- **Extraction method:** `__NEXT_DATA__` JSON island parse
  ([wellfound.py](job_monitor/scrapers/wellfound.py)) — parser is fixture-validated and correct.
- **Records:** 0. Both role pages return **HTTP 403** (Cloudflare).
- **Fix attempted this session:** installed the full optional browser stack (playwright,
  patchright + Chromium via `PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64`, browserforge,
  msgspec) and exercised Scrapling's `StealthyFetcher` — Wellfound still returns **403 to the
  stealth browser**. The block is at the network/IP-reputation level (datacenter IP), not a
  code defect. Residential proxies would be required; that is out of scope and documented.
- **Recommendation:** keep `ENABLE_WELLFOUND=false` in scheduled runs (already done in
  `.github/workflows/scrape.yml`). The scraper degrades gracefully (returns `[]`, never
  fabricates) and the pipeline isolates the failure.

## Failure isolation (verified)
A blocked source never stops the run: the pipeline reported `sources ok 5/5` with Wellfound
contributing 0 records — errors are logged, health is recorded, remaining sources continue.

## Production readiness verdict
- **RemoteOK, We Work Remotely, Freelancer, Fiverr:** production-ready over plain HTTP.
- **Wellfound:** parser ready; source blocked at IP level — requires residential egress to go
  live. Disabled in scheduled runs by design.
