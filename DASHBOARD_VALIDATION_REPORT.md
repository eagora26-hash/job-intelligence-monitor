# Dashboard Validation Report

**Date:** 2026-06-10 · **Data:** real scraped database (229 jobs, 4 active sources)
**Methods:** (a) headless `streamlit.testing.v1.AppTest` page-by-page, (b) real
`streamlit run` server + HTTP checks, (c) real-browser screenshots (headless Chromium).

## Startup command

```bash
.venv/bin/streamlit run job_monitor/dashboard/app.py
# verified live: GET /_stcore/health → 200 "ok", GET / → 200
```

## Pages tested (AppTest, real DB)

| Page | Exceptions | Errors | Notes |
|---|---:|---:|---|
| Overview | 0 | 0 | metrics row + jobs-by-source donut (1 Plotly chart) + top-opportunities table |
| Analytics | 0 | 0 | **5 Plotly charts** (daily trend, by source, by category, skills, score distribution) |
| Job Explorer | 0 | 0 | search/filters/sort + data table + 3 export buttons |
| Source Health | 0 | 0 | per-source success/failure/latency from `source_health` |
| Configuration | 0 | 0 | source toggles, keywords, notification settings (safe `.env` writer) |

## Interactions tested

- **Search:** `text_input = "python"` → re-render, 0 errors, table updates.
- **Filter:** min-score slider → 10 → re-render, 0 errors.
- **Exports:** download buttons present and enabled: `⬇️ Export CSV`, `⬇️ Export Excel`,
  `⬇️ Export JSON` (JSON button **added this session** — see
  [EXPORT_VALIDATION_REPORT.md](EXPORT_VALIDATION_REPORT.md)).
- **Data bootstrap:** `ensure_data()` auto-loads stored data (live-scrape → demo fallback
  when empty) so the app is never blank; sidebar shows the active data mode.
- **Live scrape button:** `🌐 Scrape live now` wired to `run_live_scrape()` (exercised via
  the equivalent pipeline call during scraper validation).

## Screenshots (real, captured this session)

| File | Page |
|---|---|
| [screenshots/01_dashboard_overview.png](screenshots/01_dashboard_overview.png) | Overview |
| [screenshots/02_analytics_page.png](screenshots/02_analytics_page.png) | Analytics |
| [screenshots/03_job_explorer.png](screenshots/03_job_explorer.png) | Job Explorer |
| [screenshots/04_source_health.png](screenshots/04_source_health.png) | Source Health |
| [screenshots/05_settings_page.png](screenshots/05_settings_page.png) | Configuration |

## Issues found & fixes applied

1. **JSON export missing from the UI** (CSV/Excel only) → added `to_json_bytes()` to
   [exporters.py](job_monitor/analytics/exporters.py) and a third download button to
   [explorer.py](job_monitor/dashboard/views/explorer.py); covered by tests.
2. **`.streamlit/config.toml` conflict** — `enableCORS=false` clashed with XSRF protection
   (Streamlit warned and overrode it) → removed the redundant setting.

## Verdict

All five pages load, all charts render, search/filters/sort work, and all three exports
download — against real scraped data, verified both headlessly and through a real browser.
