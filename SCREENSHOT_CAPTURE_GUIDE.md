# Screenshot Capture Guide

12 screenshots for portfolio and client presentation. **1–5, 11–12 are already captured**
(real, headless Chromium, dark theme, live data — in `screenshots/`); re-capture them only
if the UI changes. 6–10 need your accounts/devices — exact steps below.

General settings: 1600×1000 window (or full screen), 100% zoom, PNG, < 500 KB if possible.
Dashboard prep: `streamlit run job_monitor/dashboard/app.py` → http://localhost:8501
(or use your Streamlit Cloud URL).

| # | Screenshot | Exact page | Exact action | Save as | Status |
|---|---|---|---|---|---|
| 1 | Dashboard Overview | Dashboard → **📊 Overview** | open page, wait for charts, capture full window | `screenshots/01_dashboard_overview.png` | ✅ done |
| 2 | Analytics | Dashboard → **📈 Insights** | capture with the trend + heatmap visible | `screenshots/02_analytics_page.png` | ✅ done |
| 3 | Job Explorer | Dashboard → **🔎 Job Explorer** | type `python` in Search → **Apply filters** → capture results + export buttons | `screenshots/03_job_explorer.png` | ✅ done |
| 4 | Source Health | Dashboard → **🩺 Source Health** | capture status cards + table | `screenshots/04_source_health.png` | ✅ done |
| 5 | Settings | Dashboard → **⚙️ Configuration** | capture source toggles + keyword editor | `screenshots/05_settings_page.png` | ✅ done |
| 6 | Telegram Alert | **Your phone/desktop Telegram**, chat with `@ejob_monitor_bot` | scroll to a `🚀 NEW JOB` message (sent during validation) or run `python main.py --once` after adding a new keyword; crop to 1–2 messages | `screenshots/06_telegram_notification.png` | ⬜ your device |
| 7 | Excel Export | LibreOffice Calc / Excel | Job Explorer → **⬇️ Export Excel** → open the downloaded `jobs_export.xlsx` → capture the `Jobs` sheet with columns visible | `screenshots/08_excel_export.png` | ⬜ your device |
| 8 | CSV Export | Spreadsheet or text editor | Job Explorer → **⬇️ Export CSV** → open `jobs_export.csv` → capture header + ~15 rows | `screenshots/07_csv_export.png` | ⬜ your device |
| 9 | Docker Running | Terminal | in the project folder: `docker compose up` → wait for both services → capture terminal showing `scheduler` + `dashboard` logs (or `docker compose ps`) | `screenshots/09_docker_running.png` | ⬜ needs Docker |
| 10 | GitHub Actions | Browser → `github.com/eagora26-hash/job-intelligence-monitor/actions` | capture the runs list showing green **Tests**, **Lint**, **Scheduled Scrape** (all green as of 2026-06-10) | `screenshots/10_github_actions.png` | ⬜ 1 minute |
| 11 | System Status | Dashboard → **🖥️ System Status** | capture alerts + scrapes + DB stats | `screenshots/11_system_status.png` | ✅ done |
| 12 | Streamlit Cloud Deployment | Browser → your `*.streamlit.app` URL | capture the deployed Overview page **with the cloud URL visible in the address bar** | `screenshots/13_streamlit_cloud.png` | ⬜ after deploy |
| — | Portfolio Showcase *(bonus, done)* | Dashboard → **🏆 Portfolio Showcase** | architecture diagram visible | `screenshots/12_portfolio_showcase.png` | ✅ done |
| — | Scheduler Running *(requested as #12 alt)* | Terminal | `python main.py --loop` → capture the startup log (`Scheduler starting; interval = …`) + one completed run line, then Ctrl+C showing graceful shutdown | `screenshots/14_scheduler_running.png` | ⬜ 2 minutes |

Tip: after capturing, drop the new files into `screenshots/` and they're automatically
referenced by the README and guides.
