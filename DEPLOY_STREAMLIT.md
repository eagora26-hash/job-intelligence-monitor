# Deploying the Dashboard to Streamlit Community Cloud

A complete, zero-experience walkthrough. Local readiness was **verified 2026-06-10**
(entrypoint runs, dependencies install from the root `requirements.txt`, health endpoint
answers `200 ok`, a real scraped database is committed so the app shows data immediately).

## The facts you will be asked for

| Setting | Value |
|---|---|
| **Repository URL** | `https://github.com/<your-username>/job-intelligence-monitor` *(created in Step 1)* |
| **Branch** | `main` |
| **Entrypoint (main file path)** | `job_monitor/dashboard/app.py` |
| **Python version** | 3.11 – 3.13 (Streamlit Cloud default works; pin 3.12 in *Advanced settings* if asked) |
| **Streamlit secrets** | **none required** — the dashboard reads the committed database and sends no Telegram |
| **GitHub Actions secrets** | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (for the scheduled scrape + alerts, not the dashboard) |
| **Environment variables** | none required for the dashboard; optional tuning via `.env` keys (see [.env.example](.env.example)) |

---

## Step 1 — Put the project on GitHub (one time)

1. Create a GitHub account at https://github.com if you don't have one.
2. Click **+** (top-right) → **New repository** → name it `job-intelligence-monitor` →
   **Public** → **do not** tick "Add a README" → **Create repository**.
3. In a terminal, from the project folder:
   ```bash
   git remote add origin https://github.com/<your-username>/job-intelligence-monitor.git
   git push -u origin main
   ```
   This is safe to publish: the Telegram token lives only in the gitignored `.env`
   (verified absent from git history).

## Step 2 — Add the Telegram secrets to GitHub (for automatic monitoring)

1. **First rotate the bot token**: in Telegram, open **@BotFather** → `/mybots` → your bot →
   **API Token** → **Revoke current token**. Copy the new token (also update your local `.env`).
2. On GitHub: your repo → **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret**:
   - Name `TELEGRAM_BOT_TOKEN`, value = the new token → **Add secret**
   - Name `TELEGRAM_CHAT_ID`, value = your chat id → **Add secret**
3. That's all the automation needs: the included workflow
   ([.github/workflows/scrape.yml](.github/workflows/scrape.yml)) now scrapes every 6 hours,
   sends Telegram alerts for **new jobs only**, and commits the refreshed database — which
   makes the dashboard redeploy itself with fresh data.

## Step 3 — Deploy the dashboard

1. Go to **https://share.streamlit.io** → **Continue with GitHub** → authorize.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Fill in exactly:
   - **Repository:** `<your-username>/job-intelligence-monitor`
   - **Branch:** `main`
   - **Main file path:** `job_monitor/dashboard/app.py`
4. Click **Deploy**. The first build takes 2–4 minutes (it installs `requirements.txt`).
5. Your dashboard is live at a URL like
   `https://<your-username>-job-intelligence-monitor-….streamlit.app` — share it freely.

## Step 4 — Validate the deployment (5 checks)

1. **App loads** with the dark "Job Intelligence Monitor" overview and non-zero KPI numbers
   (it ships with a real scraped database).
2. Sidebar shows **"Showing: 📦 stored data"** — confirms it read the committed DB.
3. Open every page in the sidebar — Overview, Insights, Job Explorer, Source Health,
   System Status, Portfolio Showcase, Configuration — each must render without a red error box.
4. In **Job Explorer**, type `python` → **Apply filters** → results shrink; click
   **⬇️ Export CSV** → a file downloads.
5. Click **🌐 Scrape live now** in the sidebar → after ~10 s the job counts increase.
   *(This refresh lives only in the running container; durable refreshes come from the
   GitHub Action commits.)*

Then validate the automation: GitHub repo → **Actions** → **Scheduled Scrape** →
**Run workflow**. Within ~2 minutes you should see a green run; on its **first** execution
against a fresh DB you get one Telegram "📊 Baseline established" message, afterwards alerts
arrive **only when genuinely new jobs appear** ([TELEGRAM_NOTIFICATION_ARCHITECTURE.md](TELEGRAM_NOTIFICATION_ARCHITECTURE.md)).

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `ModuleNotFoundError: job_monitor` during deploy | Main file path is wrong. It must be exactly `job_monitor/dashboard/app.py` (no leading `/`). |
| Build fails installing dependencies | In the app's **Settings → Advanced**, set Python to **3.12** and reboot the app. |
| App shows demo data instead of real jobs | The committed `database/jobs.db` is missing on your branch — run the *Scheduled Scrape* action once, or locally `git add -f database/jobs.db && git commit && git push`. |
| App loads forever / sleeps | Free-tier apps sleep after inactivity; the first visit wakes them (~30 s). |
| "Scrape live now" results vanish later | Expected — Cloud storage is ephemeral; durable data comes from the Action's DB commits. |
| No Telegram messages | Alerts come from the **GitHub Action**, not the dashboard. Check repo secrets, the Action log, and that the first (baseline) run already happened. |
| Telegram error 401 in the Action log | Token wrong/revoked — re-create the `TELEGRAM_BOT_TOKEN` secret with the current @BotFather token. |
| Wellfound shows 0 jobs / red health | Known: Cloudflare blocks datacenter IPs. It's disabled in the scheduled scrape on purpose. |
| You changed keywords but nothing happens | Keywords live in `job_monitor/config/keywords.py` — edit, commit, push; the next Action run uses them. |

## How the pieces fit (one diagram)

```
GitHub Actions cron (6h) ──scrape──► Telegram (new jobs only)
        │
        └── commits database/jobs.db ──► Streamlit Cloud auto-redeploys the dashboard
```
