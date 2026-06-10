# Telegram Validation Report

**Date:** 2026-06-10 · **Validation type:** live end-to-end (real messages sent)

## Configuration

| Item | Value / location |
|---|---|
| Bot | `@ejob_monitor_bot` (id `8959268251`) — verified via `getMe` → HTTP 200 |
| Secrets | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` in gitignored `.env` ([.env.example](.env.example) has placeholders) |
| Enable flag | `NOTIFY_ENABLED=true` |
| Score gate | `NOTIFY_MIN_SCORE=10` (only relevant jobs alert) |
| Rate guard | max 15 alerts/run + 50 ms spacing, then a "+N more" rollup ([telegram.py](job_monitor/notifications/telegram.py)) |
| Factory | `build_notifier()` returns `TelegramNotifier` when configured + enabled, else `NullNotifier` — call sites never branch on config |

## Trigger logic (verified in code + live)

1. Pipeline upserts each normalized job; repository returns `new` / `updated` / `unchanged`.
2. Only **`new`** jobs with **score ≥ NOTIFY_MIN_SCORE** are notified.
3. The `notified` flag is stored per job, so a job is alerted **at most once**.

## Delivery proof (live, 2026-06-10)

1. **Full pipeline run** (`python main.py --once`):
   `scraped 347 | new 118 | updated 2 | notified 15` — 15 real alert messages delivered to
   chat `8654483730` (capped at 15/run; rollup message sent for the remainder).
2. **Direct API send** captured:
   `sendMessage → HTTP 200, ok=true, message_id=37, chat=8654483730, date=1781085449`.
3. **Duplicate avoidance:** an immediate second `--once` run re-scraped 346 jobs and
   re-notified **none** of the previously seen ones (RemoteOK/WWR: 0 new). The 10 alerts it
   sent were for genuinely new listings (Fiverr promoted-gig rotation + 1 new Freelancer
   project).

## Formatting

`format_job()` produces the spec layout — HTML-bold, link preview disabled:

```
🚀 NEW JOB

Title: …
Company: …
Source: …
Tags: …
Link: …
```

## Screenshots path

`screenshots/06_telegram_notification.png` — capture from your Telegram client (the bot's
messages from the runs above are in chat history; see [SCREENSHOT_CHECKLIST.md](SCREENSHOT_CHECKLIST.md)).
This is the one artifact that cannot be captured from this machine (requires the chat owner's
client).

## Known limitations

1. **🔴 Token rotation still pending** — the token was exposed in plaintext in the original
   `instructions.md` (gitignored, never in VCS). Rotate via @BotFather before public showcase.
2. Fiverr gig rotation generates a few new-job alerts per run; raise `NOTIFY_MIN_SCORE` or
   disable Fiverr alerts if too chatty.
3. Failures are swallowed and logged (by design) so a Telegram outage never breaks a scrape.
4. No burst/load test beyond the 15-alert cap was performed.
