# Installation Guide

Written for non-technical users. Pick **one** of the three ways to run the system:

- **A. Online (recommended, no installation)** — free hosting, 10 minutes, nothing on your computer.
- **B. On your computer (local)** — needs Python.
- **C. Docker** — one command, needs Docker Desktop.

---

## A. Online — no installation

The dashboard runs on Streamlit Community Cloud (free) and the scraping runs on GitHub
(free). Follow [STREAMLIT_DEPLOYMENT_PACKAGE.md](STREAMLIT_DEPLOYMENT_PACKAGE.md) — it
assumes zero experience and takes about 10 minutes total. After that, everything is
automatic: scraping every 6 hours, Telegram alerts, dashboard always up to date.

---

## B. On your computer (local)

### What you need
- **Python 3.11 or newer** — download from https://www.python.org/downloads/
  (during install on Windows, tick **"Add Python to PATH"**).

### Step 1 — Get the project
Either download the ZIP from GitHub (**Code → Download ZIP**, then unzip), or:
```bash
git clone https://github.com/eagora26-hash/job-intelligence-monitor.git
cd job-intelligence-monitor
```

### Step 2 — Create a private Python environment and install
Open a terminal **inside the project folder** and run:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
This takes 1–3 minutes. You only do it once.

### Step 3 — Configure (environment variables)
Copy the example settings file and fill in your Telegram details:
```bash
# Windows:
copy .env.example .env
# Mac/Linux:
cp .env.example .env
```
Open `.env` in any text editor and set:

| Variable | What to put there |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the token from **@BotFather** in Telegram (`/newbot` or `/mybots` → API Token) |
| `TELEGRAM_CHAT_ID` | your chat id (message **@userinfobot** in Telegram, it replies with your id) |
| `NOTIFY_ENABLED` | `true` to receive alerts, `false` to run silently |

Everything else already has sensible defaults — see [ADMIN_GUIDE.md](ADMIN_GUIDE.md) to
change keywords, intervals or sources later.

### Step 4 — Run it
```bash
python main.py --once       # one scrape right now (first run = silent baseline)
python main.py --loop       # keep monitoring (every hour by default), Ctrl+C to stop
python main.py --status     # show what the system knows
```

### Step 5 — Open the dashboard
```bash
streamlit run job_monitor/dashboard/app.py
```
Your browser opens at **http://localhost:8501**. That's it.

---

## C. Docker (one command)

### What you need
- **Docker Desktop** — https://www.docker.com/products/docker-desktop/

### Steps
1. Get the project (same as B, Step 1) and create `.env` (same as B, Step 3).
2. In the project folder run:
   ```bash
   docker compose up
   ```
3. Two services start: the **scheduler** (scrapes + sends alerts on an interval) and the
   **dashboard** at **http://localhost:8501**. The database is stored in a volume, so your
   data survives restarts. Stop with `Ctrl+C` (or `docker compose down`).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Python isn't installed or not on PATH — reinstall and tick "Add to PATH" (Windows) or use `python3`. |
| `pip install` fails with compiler errors | Make sure Python is 3.11–3.13. On a very new Python, run inside the provided `.venv`. |
| Dashboard says "demo data" | The database is empty — run `python main.py --once` first, or press **🌐 Scrape live now** in the sidebar. |
| No Telegram messages | Check `.env`: token + chat id correct, `NOTIFY_ENABLED=true`. Remember: the **first run never sends per-job alerts** (it builds the baseline and sends one summary). Also check `NOTIFY_MIN_SCORE` — low-relevance jobs don't alert. |
| Telegram error 401 in logs | Wrong/revoked token — get a fresh one from @BotFather and update `.env`. |
| Port 8501 already in use | `streamlit run job_monitor/dashboard/app.py --server.port 8502` |
| Wellfound shows 0 jobs | Normal — that site blocks automated access at network level. The other four sources are unaffected. |
| Where are the logs? | `logs/` folder (rotating files). The dashboard's **System Status** page shows run history too. |
