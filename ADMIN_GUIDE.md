# Admin Guide — Job Intelligence Monitor

Operating and customizing the system. Most changes are either a line in `.env` (local
settings) or an edit in one Python list (keywords). Nothing here requires programming
beyond copy-paste.

---

## 1. Changing keywords (what counts as "relevant")

Keywords, their score weights, categories and the skill list all live in **one file**:

```
job_monitor/config/keywords.py
```

- `DEFAULT_KEYWORDS` / `KEYWORD_WEIGHTS` — what to look for and how many points each match
  adds (e.g. `"python": 10`). A job's score is the sum of its matches; jobs scoring 0 are
  not stored, jobs below `NOTIFY_MIN_SCORE` are stored but not alerted.
- `CATEGORY_RULES` — keyword → category mapping (Automation, Web Scraping, E-commerce, …).
- `SKILLS` — the skills extracted and tracked in analytics.
- `DEFAULT_EXCLUDE_KEYWORDS` — hard "ignore" words.

Quick include/exclude overrides without editing code: set `INCLUDE_KEYWORDS` /
`EXCLUDE_KEYWORDS` (comma-separated) in `.env`. You can also edit keywords from the
dashboard's **⚙️ Configuration** page.

**If you run via GitHub Actions:** commit + push the change; the next scheduled run uses it.

## 2. Enabling / disabling sources

In `.env` (or the Configuration page):

```
ENABLE_REMOTEOK=true
ENABLE_WWR=true
ENABLE_FREELANCER=true
ENABLE_FIVERR=true
ENABLE_WELLFOUND=false     # blocked by its anti-bot protection; keep off
```

In the scheduled workflow the same flags are set in
[.github/workflows/scrape.yml](.github/workflows/scrape.yml) under `env:`.

## 3. Adding a new source (developer task, ~1 hour)

1. Copy an existing scraper in `job_monitor/scrapers/` (e.g. `remoteok.py`) and implement
   `fetch_raw()` returning the standard raw-job dicts.
2. Register it — **one line** in `job_monitor/scrapers/registry.py` (`SCRAPER_CLASSES`).
3. Add `ENABLE_<NAME>` to `Settings.enabled_sources()` in `job_monitor/config/settings.py`.
4. Add a fixture + parser test in `tests/job_monitor/` (copy an existing one).
Everything else (normalization, scoring, dedup, alerts, dashboard) picks it up automatically.

## 4. Changing the monitoring interval

| Where it runs | What to change |
|---|---|
| Local loop (`python main.py --loop`) | `POLLING_INTERVAL` in `.env` (seconds, minimum 60; default 3600) |
| GitHub Actions | the `cron:` line in `.github/workflows/scrape.yml` (default `0 */6 * * *` = every 6 h) |
| Docker | `POLLING_INTERVAL` in `.env` (compose passes it through) |

## 5. Telegram configuration

| Setting (`.env` or GitHub secret) | Meaning |
|---|---|
| `TELEGRAM_BOT_TOKEN` | from @BotFather (`/mybots` → API Token). **Rotate it if it ever leaks** — revoke + replace, then update `.env` *and* the GitHub secret. |
| `TELEGRAM_CHAT_ID` | your chat (get it from @userinfobot) |
| `NOTIFY_ENABLED` | master on/off switch |
| `NOTIFY_MIN_SCORE` | minimum relevance to alert (default 10; raise it for fewer messages) |
| `NOTIFY_SOURCES` | comma-separated sources allowed to alert (default `remoteok,weworkremotely,freelancer` — keeps high-churn marketplaces quiet) |

Behavior reference (baseline, only-new, at-most-once):
[TELEGRAM_NOTIFICATION_ARCHITECTURE.md](TELEGRAM_NOTIFICATION_ARCHITECTURE.md).

## 6. Backups

Automatic: every pipeline run stores a timestamped copy of the database in `backup/` and
prunes copies older than **30 days** (`job_monitor/services/backup.py`).

Manual backup — just copy two files while the app isn't mid-run:
```
database/jobs.db        # all job data
data/state.json         # run/resume state (optional)
```

## 7. Restoring data

1. Stop the scheduler/dashboard.
2. Replace `database/jobs.db` with the backup copy
   (from `backup/jobs-YYYYMMDD-HHMMSS.db` — rename it to `jobs.db`).
3. Start again. Nothing else is needed — all state lives in that file.
   *(If you also restored an old `state.json`, the next run simply continues from there.)*

To start completely fresh instead: delete `database/jobs.db` — the next run re-creates it
and re-establishes the notification baseline (one summary message, no alert flood).

## 8. Archive & housekeeping

- Old jobs can be moved to `database/archive.db` (`job_monitor/services/archive.py`) to keep
  the active database small.
- Logs rotate automatically in `logs/`.
- The GitHub Action commits the refreshed database back to the repo after each run — that's
  by design (it's what keeps the online dashboard current).

## 9. Health monitoring

- Dashboard → **🩺 Source Health** (per-source success/failure/latency) and
  **🖥️ System Status** (recent runs, alerts, exports, DB stats).
- CLI: `python main.py --status`.
- If a source starts failing permanently, the run continues without it and the failure is
  recorded + alerted; disable the source if the site changed (`ENABLE_*=false`) and have a
  developer update its parser (see §3).
