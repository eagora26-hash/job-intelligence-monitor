# User Guide — Job Intelligence Monitor

How to use the system day-to-day. (For installation see [INSTALLATION.md](INSTALLATION.md);
for changing settings see [ADMIN_GUIDE.md](ADMIN_GUIDE.md).)

---

## The dashboard

Start it with `streamlit run job_monitor/dashboard/app.py` (or open your Streamlit Cloud
URL). Navigation is in the left sidebar; the two buttons there do exactly what they say:

- **🌐 Scrape live now** — fetch fresh jobs immediately (uses the three fast sources).
- **🔄 Refresh view** — re-read the database (e.g. after a scheduled scrape ran).

### 📊 Overview — your daily starting point
The executive summary: total jobs, new today (with last-24h delta), average relevance,
active sources, alerts delivered, and overall source health. Below it, the "smart
intelligence" band shows the most active source, the top trending skill and the top
category, followed by **Top opportunities** (the highest-scoring jobs, with a relevance
bar and an *open* link) and **Latest discoveries**.

> 📷 `screenshots/01_dashboard_overview.png`

### 📈 Insights — analytics
- **Trend analysis** — new jobs per day (adjustable window) and per week.
- **Skill demand heatmap** — which sources ask for which skills.
- **Source comparison** — volume vs. average relevance vs. data quality per source.
- **Leaderboards** — best-scoring jobs and most reliable sources.

> 📷 `screenshots/02_analytics_page.png`

### 🔎 Job Explorer — search & export
Type what you're looking for (e.g. *python scraping*), narrow by source, category,
minimum relevance or remote-only, choose the sorting, press **Apply filters**.
The result table is exportable with one click: **CSV**, **Excel** or **JSON** — the export
contains exactly what you filtered.

> 📷 `screenshots/03_job_explorer.png` · `07_csv_export.png` · `08_excel_export.png`

### 🩺 Source Health — is everything working?
A status card per source (🟢 healthy / 🟡 degraded / 🔴 failing), success rates, response
times and the last error, plus system metrics (database size, total runs).

> 📷 `screenshots/04_source_health.png`

### 🖥️ System Status — what happened recently
Latest Telegram alerts, the outcome of the most recent scrape per source, the latest export
files, and database statistics. This is the page to check if you wonder "did it run?".

> 📷 `screenshots/11_system_status.png`

### 🏆 Portfolio Showcase
A self-explaining page about the product (architecture, data flow, value) — useful when
showing the system to someone new.

> 📷 `screenshots/12_portfolio_showcase.png`

### ⚙️ Configuration — settings without code
Toggle sources on/off, edit the keyword list, and adjust notification settings from the
browser. Changes are saved to the configuration file safely (the page refuses to touch
secrets). Details in [ADMIN_GUIDE.md](ADMIN_GUIDE.md).

> 📷 `screenshots/05_settings_page.png`

---

## Notifications (Telegram)

You receive a message like this when a **new, relevant** job appears:

```
🚀 NEW JOB

Title: Build a Python web-scraping bot
Company: …
Source: RemoteOK
Tags: python, scraping
Link: https://…
```

What to expect:
- **The very first run sends no job alerts** — it ingests everything and sends one
  "📊 Baseline established" summary. From then on you only hear about *new* jobs.
- A job alerts **at most once**, ever. Re-posts and updates don't re-alert.
- At most 15 alerts per run; more than that arrives as a "+N more" summary.
- Only jobs scoring above your relevance threshold alert (`NOTIFY_MIN_SCORE`), and only
  from the sources you allow (`NOTIFY_SOURCES`).

> 📷 `screenshots/06_telegram_notification.png`

---

## Exports

Three ways to get data out:
1. **Dashboard** — Job Explorer → filter → **Export CSV / Excel / JSON** (downloads instantly).
2. **Files** — exports are also written to the `exports/` folder when generated.
3. The Excel file has a single clean `Jobs` sheet; the JSON is an array of job objects —
   both contain the same 14 columns as the CSV (source, title, company, category, score,
   quality, remote, location, salary, skills, tags, dates, link).

---

## Quick answers

| Question | Answer |
|---|---|
| How fresh is the data? | The scheduled scrape runs every 6 hours; press **🌐 Scrape live now** anytime. |
| Why didn't job X alert me? | Either it was seen before, scored below the threshold, or its source isn't in the alert list. The System Status page shows what was alerted. |
| Can I search by company? | Yes — the Explorer search matches title, company and skills. |
| Something looks broken? | Check **Source Health** first, then [INSTALLATION.md → Troubleshooting](INSTALLATION.md#troubleshooting). |
