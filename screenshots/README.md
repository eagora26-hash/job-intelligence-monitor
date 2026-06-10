# Screenshots

Real captures (headless Chromium, 1600×1000, live scraped data — 229 jobs) were
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
| `07_csv_export.png` | real `jobs_export.csv` contents as a data grid | ✅ captured |
| `08_excel_export.png` | real `jobs_export.xlsx` Jobs sheet as a data grid | ✅ captured |
| `09_docker_running.png` | `docker compose up` with both services healthy | ⬜ manual (needs Docker daemon) |
| `10_github_actions.png` | GitHub Actions page — all workflows green | ✅ captured |
| `14_scheduler_running.png` | `python main.py --loop` — 2 timed cycles + graceful shutdown | ✅ captured |
| `11_system_status.png` | System Status — alerts, scrapes, exports, DB stats | ✅ captured |
| `12_portfolio_showcase.png` | Portfolio Showcase — architecture + value page | ✅ captured |

To re-capture 01–05: `streamlit run job_monitor/dashboard/app.py`, light theme, 100% zoom.
Keep files < 500 KB (PNG) so the README loads quickly on GitHub.
