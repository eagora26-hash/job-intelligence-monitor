# Screenshots

Five **real captures** (headless Chromium, 1600×1000, live scraped data — 229 jobs) were
generated on 2026-06-10. The full capture plan, including the five remaining manual shots,
is in [SCREENSHOT_CHECKLIST.md](../SCREENSHOT_CHECKLIST.md).

| File | Content | Status |
|---|---|---|
| `01_dashboard_overview.png` | Dashboard Overview — KPIs, jobs-by-source donut, top opportunities | ✅ captured |
| `02_analytics_page.png` | Analytics — daily trend, source/category bars, skills | ✅ captured |
| `03_job_explorer.png` | Job Explorer — search, filters, results table, CSV/Excel/JSON export | ✅ captured |
| `04_source_health.png` | Source Health — per-source status + system metrics | ✅ captured |
| `05_settings_page.png` | Configuration — source toggles, keywords, notifications | ✅ captured |
| `06_telegram_notification.png` | A "🚀 NEW JOB" alert in the Telegram client | ⬜ manual (chat owner's device) |
| `07_csv_export.png` | `exports/jobs_export.csv` opened in a spreadsheet | ⬜ manual |
| `08_excel_export.png` | `exports/jobs_export.xlsx` opened (Jobs sheet) | ⬜ manual |
| `09_docker_running.png` | `docker compose up` with both services healthy | ⬜ manual (needs Docker daemon) |
| `10_github_actions.png` | Green lint/test/scrape workflow runs | ⬜ manual (after GitHub push) |

To re-capture 01–05: `streamlit run job_monitor/dashboard/app.py`, light theme, 100% zoom.
Keep files < 500 KB (PNG) so the README loads quickly on GitHub.
