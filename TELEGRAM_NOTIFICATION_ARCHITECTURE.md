# Telegram Notification Architecture

**Last validated:** 2026-06-10 (live, 3 consecutive cycles on a fresh database — see §5).

The notifier behaves as a **true monitoring system**: the first run establishes a silent
baseline; every later run alerts **only** about jobs that have never been seen before, with
at-most-once delivery guaranteed by database state.

## 1. Baseline behavior (first run)

A run is a **baseline run** when the `jobs` table is empty (fresh install / new deployment).
Detected in [`PipelineRunner.run_once`](job_monitor/pipeline/runner.py):

- all scraped jobs are ingested normally (normalize → enrich → filter → upsert);
- **no per-job alerts are sent** — the chat is never flooded by a first run;
- every ingested job is immediately marked `notified = 1`;
- one summary message is sent instead:
  `📊 Baseline established — N jobs ingested (source breakdown). From now on you will only be alerted about new jobs.`

## 2. New-job detection

Every scraped job is upserted by URL (`UNIQUE` constraint). The repository classifies each
upsert ([repository.py](job_monitor/database/repository.py)):

| Outcome | Meaning | Alert? |
|---|---|---|
| `NEW` | URL never seen before → row inserted with `first_seen = now` | ✅ candidate |
| `UPDATED` | URL known, content hash changed → row updated, `last_seen` refreshed, diff written to `job_history` | ❌ |
| `UNCHANGED` | URL known, same content → only `last_seen` refreshed | ❌ |

Only `NEW` jobs can ever generate an alert — re-scraped jobs are structurally incapable of
re-alerting.

## 3. Duplicate prevention (three independent layers)

1. **URL uniqueness** — a job can exist only once; re-scrapes hit `UPDATED/UNCHANGED`.
2. **`notified` flag** — set in the same transaction batch as a successful send
   (`mark_notified`); baseline jobs are pre-marked. A job whose flag is set is never
   re-alerted, even across restarts (state lives in SQLite, not memory).
3. **Run-scoped candidate list** — `_notify()` receives only this run's `NEW` records, so
   even a notifier failure cannot resend older jobs on the next cycle.

## 4. Notification workflow

```
scrape (concurrent) → normalize → enrich (score) → filter → upsert
                                                              │
                              NEW records only ───────────────┘
                                       │
                    baseline run? ── yes ─► mark all notified + 1 summary msg
                                       │ no
                                       ▼
                    score ≥ NOTIFY_MIN_SCORE  (default 10)
                                       ▼
                    source ∈ NOTIFY_SOURCES   (default: remoteok, weworkremotely,
                                       │       freelancer — silences marketplace
                                       ▼       gig-rotation churn, e.g. Fiverr)
                    TelegramNotifier.notify_new_jobs()
                      · max 15 alerts/run + "+N more" rollup
                      · 50 ms spacing (rate-limit safety)
                                       ▼
                    mark_notified(urls)  →  notified=1 in DB
```

Database fields backing this (schema, `jobs` table): **`first_seen`**, **`last_seen`**,
**`notified`** (+ `content_hash` for change detection).

Configuration (`.env` / GitHub Actions env):

| Variable | Purpose | Default |
|---|---|---|
| `NOTIFY_ENABLED` | master switch (off → `NullNotifier`) | `true` |
| `NOTIFY_MIN_SCORE` | minimum relevance score to alert | `10` |
| `NOTIFY_SOURCES` | CSV allow-list of sources that may alert (empty = all) | `remoteok,weworkremotely,freelancer` |

## 5. Live validation (2026-06-10, fresh DB, 3 cycles ~20 s apart)

```
CYCLE 1  Run finished | BASELINE | sources ok 5/5 | scraped 346 | new 152 | notified 0
CYCLE 2  Run finished |            sources ok 5/5 | scraped 345 | new 13  | notified 0
CYCLE 3  Run finished |            sources ok 5/5 | scraped 347 | new 6   | notified 0
```

Database state after cycle 3: **171 jobs total, 152 marked notified** (the baseline set),
19 post-baseline discoveries stored without alerts — all 19 were either Fiverr gig-rotation
items (silenced by `NOTIFY_SOURCES`) or below `NOTIFY_MIN_SCORE`. Exactly **one** Telegram
message was produced across all three cycles: the baseline summary.

Earlier same-day validation (pre-baseline-feature, production DB) additionally proved real
per-job delivery: 15 alerts delivered with `sendMessage ok=true` and an immediate re-run
re-alerting none of them ([TELEGRAM_VALIDATION_REPORT.md](TELEGRAM_VALIDATION_REPORT.md)).

**Conclusion:** first run = silent baseline · later runs = only genuinely new, relevant jobs ·
nothing is ever re-sent · state survives restarts because it lives in the database.

Unit coverage: `test_first_run_establishes_baseline_without_alerts`,
`test_monitoring_run_notifies_only_new_jobs`, `test_notify_sources_filter`
([test_runner.py](tests/job_monitor/test_runner.py)).
