# Screenshot Checklist

Status legend: ✅ captured (real, in `screenshots/`) · ⬜ manual capture still required.

| # | Screenshot | Page / context | Exact action | Save as | Status |
|---|---|---|---|---|---|
| 1 | Dashboard Overview | Dashboard → **Overview** | `streamlit run job_monitor/dashboard/app.py`, select *Overview*, full window | `screenshots/01_dashboard_overview.png` | ✅ |
| 2 | Analytics Page | Dashboard → **Analytics** | select *Analytics*, charts visible | `screenshots/02_analytics_page.png` | ✅ |
| 3 | Job Explorer | Dashboard → **Job Explorer** | select *Job Explorer*; optionally type `python` in search and apply | `screenshots/03_job_explorer.png` | ✅ |
| 4 | Source Health | Dashboard → **Source Health** | select *Source Health*, health table visible | `screenshots/04_source_health.png` | ✅ |
| 5 | Settings Page | Dashboard → **Configuration** | select *Configuration*, toggles + keywords visible | `screenshots/05_settings_page.png` | ✅ |
| 6 | Telegram Notification | Your Telegram client, chat with `@ejob_monitor_bot` | open the chat — real alerts from the 2026-06-10 validation runs are in history; crop one "🚀 NEW JOB" message | `screenshots/06_telegram_notification.png` | ⬜ (needs chat owner's device) |
| 7 | CSV Export Example | `exports/jobs_export.csv` | open in a spreadsheet/editor showing header + rows | `screenshots/07_csv_export.png` | ⬜ |
| 8 | Excel Export Example | `exports/jobs_export.xlsx` | open in LibreOffice/Excel showing the `Jobs` sheet | `screenshots/08_excel_export.png` | ⬜ |
| 9 | Docker Running | terminal | `docker compose up` → screenshot both services up (`scheduler` + `dashboard`) | `screenshots/09_docker_running.png` | ⬜ (Docker daemon not available in the validation environment) |
| 10 | GitHub Actions Passing | GitHub repo → Actions tab | after first push: green runs for *lint*, *test*, *Scheduled Scrape* | `screenshots/10_github_actions.png` | ⬜ (requires the GitHub remote) |

Notes:
- 1–5 were captured programmatically (headless Chromium, 1600×1000, real 229-job database).
- 6–10 require accounts/devices not available to the automated environment (Telegram client,
  Docker daemon, GitHub remote) — each takes under a minute once those are at hand.
