# Deployment — Streamlit Community Cloud + automated scraping & Telegram

This deploys the **dashboard** to Streamlit Community Cloud and runs **scheduled scraping +
Telegram alerts** via GitHub Actions. The two work together:

```
GitHub Actions (cron)  ──scrape──► Telegram alerts (new jobs)
        │
        └─commits refreshed database/jobs.db──► Streamlit Cloud auto-redeploys dashboard
```

> **What I prepared for you** (already in the repo): Cloud-ready root `requirements.txt`,
> `.streamlit/config.toml`, a dashboard that **auto-loads data** (live scrape → demo fallback)
> with a **🌐 Scrape live now** button, a scheduled scrape workflow (`.github/workflows/scrape.yml`),
> and an initial committed `database/jobs.db` with **101 real scraped jobs** so the dashboard
> shows data immediately. The steps below are the parts that need **your accounts**.

---

## Step 1 — Push the repo to GitHub

```bash
# create an EMPTY repo on github.com first (e.g. job-intelligence-monitor), then:
git remote add origin https://github.com/<you>/job-intelligence-monitor.git
git push -u origin main
```

The Telegram token is **not** in the repo (it's gitignored), so this is safe to push public.

## Step 2 — Add Telegram secrets to GitHub Actions

In the GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**, add:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | your bot token from @BotFather (**rotate the old one first**) |
| `TELEGRAM_CHAT_ID` | `8654483730` (your chat id) |

The scheduled workflow uses these to send alerts. (The dashboard itself sends no Telegram, so it
needs no secrets.)

## Step 3 — Deploy the dashboard on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with the **same GitHub account**.
2. **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `<you>/job-intelligence-monitor`
   - **Branch:** `main`
   - **Main file path:** `job_monitor/dashboard/app.py`
4. Click **Deploy**. Streamlit installs the root `requirements.txt` and launches the app.

Your dashboard URL will be something like
`https://<you>-job-intelligence-monitor-...streamlit.app`.

> No Streamlit secrets are required. If you ever want the dashboard to *also* send Telegram,
> add `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` under the app's **Settings → Secrets** — but the
> recommended design keeps alerting in the scheduled Action.

## Step 4 — Trigger the first scrape (optional, immediate)

- GitHub repo → **Actions → Scheduled Scrape → Run workflow** for an immediate scrape + Telegram
  alerts + a data refresh commit (the dashboard redeploys automatically).
- Or just wait for the cron (every 6 hours).
- Or click **🌐 Scrape live now** in the deployed dashboard to refresh its data on demand.

---

## How the pieces fit

| Concern | Handled by | Notes |
|---|---|---|
| Dashboard hosting | Streamlit Community Cloud | Reads the committed `database/jobs.db`; auto-scrapes if empty |
| Ongoing scraping | GitHub Actions (`scrape.yml`, cron 6h) | Disables Fiverr/Wellfound (browser-only) for speed |
| Telegram alerts | GitHub Actions run | Only **new** jobs (dedup against the committed DB) |
| Data freshness | Action commits `database/jobs.db` | Streamlit redeploys on push |
| Keywords | `job_monitor/config/keywords.py` | Edit + commit to change what's monitored |

## Customization

- **Scrape frequency:** edit the `cron` in `.github/workflows/scrape.yml`.
- **Keywords / scoring / categories:** edit `job_monitor/config/keywords.py`.
- **Sources / thresholds:** set env in the workflow (e.g. `NOTIFY_MIN_SCORE`, `ENABLE_*`).

## Notes & gotchas

- **`database/jobs.db` is committed** (force-added) as the dashboard's data + the Action's dedup
  state. It's otherwise gitignored, so it won't appear in `git status` until modified. If local
  `python main.py --once` runs dirty your working tree, run once:
  `git update-index --skip-worktree database/jobs.db`.
- **Streamlit Cloud is ephemeral:** the **🌐 Scrape live now** button writes to the running
  container only (lost on restart); durable data comes from the Action's commits.
- **Fiverr/Wellfound** are disabled in the scheduled run (they need a browser); RemoteOK, We Work
  Remotely, and Freelancer provide the live data. See [FINAL_VALIDATION_REPORT.md](../FINAL_VALIDATION_REPORT.md).
- **🔴 Rotate the Telegram token** before going public — the original was exposed in plaintext.
