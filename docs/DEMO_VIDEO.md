# Portfolio Demo Video — Script (2–3 minutes)

A tight runtime that exercises every claimed capability. Record at 1440×900, light theme.

## Shot list

| # | Time | Action | On-screen narration |
|---|---|---|---|
| 1 | 0:00–0:15 | Show the repo + README hero, scroll the architecture diagram | "A multi-source job intelligence monitor — scraping, analytics, alerts, all in one." |
| 2 | 0:15–0:35 | Terminal: `python generate_demo_data.py` | "One command seeds a realistic dataset so the platform is demo-able instantly." |
| 3 | 0:35–1:05 | `streamlit run job_monitor/dashboard/app.py`; walk the **Overview** | "KPIs, jobs-by-source, and the top opportunities ranked by relevance." |
| 4 | 1:05–1:30 | **Analytics** page — trend, categories, top skills | "Daily trends, category breakdowns, and the most in-demand skills." |
| 5 | 1:30–1:55 | **Job Explorer** — search "python", filter, click **Export CSV** + **Excel** | "Full-text search, faceted filters, and one-click CSV/Excel export." |
| 6 | 1:55–2:10 | **Source Health** page | "Per-source health and live system metrics — this is a monitored platform." |
| 7 | 2:10–2:35 | Terminal: `python main.py --once` (a real scrape); show new jobs; Telegram alert pops | "A real scrape across live sources — new jobs detected and pushed to Telegram." |
| 8 | 2:35–2:50 | `docker compose up` | "And the whole stack — scheduler + dashboard — runs with one command." |

## Prep checklist

- [ ] `cp .env.example .env` with a **test** Telegram bot/chat (or skip shot 7's alert).
- [ ] `python generate_demo_data.py --count 200` for a fuller dashboard.
- [ ] Pre-pull Docker base image so shot 8 is fast.
- [ ] Clear terminal scrollback; use a large font.

## Suggested tooling

- Screen capture: OBS Studio / QuickTime.
- Trim & caption: any editor; keep it under 3 minutes.
- Export 1080p MP4; embed/link it at the top of the README.
