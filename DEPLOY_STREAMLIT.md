# Streamlit Community Cloud Deployment Guide

Deployment readiness was **verified 2026-06-10**: entrypoint runs, root `requirements.txt`
installs the dashboard stack, the server answers `GET /_stcore/health → 200 "ok"`, and a real
scraped database is committed so the app shows data immediately.
(Companion doc with the full architecture: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).)

## App entrypoint

```
job_monitor/dashboard/app.py
```

## Exact deployment steps

1. **Push to GitHub** (create an empty repo first):
   ```bash
   git remote add origin https://github.com/<you>/job-intelligence-monitor.git
   git push -u origin main
   ```
   Safe to push public — secrets live only in the gitignored `.env`.
2. **Add GitHub Actions secrets** (for the scheduled scrape + Telegram alerts, *not* the
   dashboard): repo **Settings → Secrets and variables → Actions**:
   - `TELEGRAM_BOT_TOKEN` — **rotate the old token via @BotFather first**
   - `TELEGRAM_CHAT_ID`
3. **Deploy on https://share.streamlit.io** → *Create app → from GitHub*:
   - Repository: `<you>/job-intelligence-monitor` · Branch: `main`
   - Main file path: `job_monitor/dashboard/app.py`
   - Click **Deploy** — Streamlit Cloud auto-installs the root `requirements.txt`.
4. **First data refresh** (optional): GitHub → Actions → *Scheduled Scrape* → *Run workflow*
   (otherwise the 6-hour cron handles it; the dashboard also ships with a committed dataset
   and has a **🌐 Scrape live now** button).

## Required secrets / environment variables

| Where | Variable | Required? |
|---|---|---|
| Streamlit Cloud | — | **None.** The dashboard reads the committed `database/jobs.db` and sends no Telegram. |
| GitHub Actions | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Yes, for scheduled alerts ([scrape.yml](.github/workflows/scrape.yml)) |
| Local (optional) | everything in [.env.example](.env.example) | Loaded automatically via pydantic-settings |

## Verified readiness checklist

- ✅ Entrypoint `job_monitor/dashboard/app.py` self-bootstraps `sys.path` (works under `streamlit run` from any CWD)
- ✅ Root `requirements.txt` contains the full dashboard stack (streamlit, plotly, pandas, …) — no browser/Playwright needed
- ✅ `.streamlit/config.toml` committed (headless, theme; CORS/XSRF conflict removed 2026-06-10)
- ✅ `database/jobs.db` committed (force-added) with real scraped jobs → app renders immediately
- ✅ No secrets required by the app; `.env` gitignored; token verified absent from tracked content
- ✅ Health check passes locally: `GET /_stcore/health → 200`

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| **ModuleNotFoundError: job_monitor** | Wrong main-file path — must be exactly `job_monitor/dashboard/app.py`. |
| **App deploys but shows demo data** | `database/jobs.db` missing/empty on the branch — run the *Scheduled Scrape* action or commit a DB (`git add -f database/jobs.db`). |
| **Dependency build failure on deploy** | Streamlit Cloud uses Python 3.11–3.13; all pins in `requirements.txt` are ranges with wheels for those versions. Pin `python_version` in *Advanced settings* if needed. |
| **"Scrape live now" data disappears** | Expected — the Cloud container filesystem is ephemeral. Durable data comes from the Action's DB commits. |
| **No Telegram alerts** | Alerts are sent by the GitHub Action, not the dashboard. Check repo secrets and the Action run log; `NOTIFY_MIN_SCORE` gates low-relevance jobs. |
| **Wellfound always 0 jobs** | Cloudflare blocks datacenter IPs (validated). It is disabled in `scrape.yml`; leave it off. |
| **App sleeps after inactivity** | Streamlit free tier sleeps apps; first visit revives it (~30 s). |
