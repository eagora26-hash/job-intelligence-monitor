# Demo Video Script — 60–90 seconds

Screen recording + voiceover (or captions). Prep before recording: dashboard closed,
terminal open in the project folder, Telegram visible on phone or second window.
To guarantee fresh alerts during the demo, add a new keyword in
`job_monitor/config/keywords.py` beforehand (new matches → new alerts).

| Time | Screen | Action | Voiceover / caption |
|---|---|---|---|
| 0:00–0:08 | Terminal | type `python main.py --once`, hit Enter | "Five job marketplaces. One command." |
| 0:08–0:20 | Terminal output | let the run log scroll: `Starting monitoring run with 5 source(s)` → per-source `Scraped N jobs` lines | "RemoteOK, We Work Remotely, Freelancer, Fiverr — scraped in parallel, about 350 postings in seconds." |
| 0:20–0:28 | Terminal summary line | zoom/highlight `Run finished … new X | notified Y` | "It deduplicates against everything seen before — only genuinely new, relevant jobs get through." |
| 0:28–0:38 | **Telegram** (phone or window) | show the `🚀 NEW JOB` alert(s) arriving; tap one to show the link | "And those land on Telegram instantly. Never the same job twice." |
| 0:38–0:50 | Browser | open the dashboard (Streamlit Cloud URL or localhost) → **📊 Overview** | "The live dashboard: total pipeline, new today, relevance, source health — at a glance." |
| 0:50–1:00 | **📈 Insights** | scroll: daily trend → skill heatmap | "Trends and skill demand across all sources — what the market wants this week." |
| 1:00–1:12 | **🔎 Job Explorer** | type `python`, Apply filters, click **⬇️ Export Excel**, show the downloaded file opening | "Search everything, filter by relevance, export to Excel in one click." |
| 1:12–1:20 | **🩺 Source Health** | show the green status cards | "Every source monitored for reliability — this thing runs itself, every six hours, for free." |
| 1:20–1:30 | GitHub Actions tab (optional) or back to Overview | show green scheduled runs / end on the hero | "Job Intelligence Monitor. Built in Python. Link in the description." |

## Recording notes
- 1080p, hide bookmarks bar, dark browser theme (matches the dashboard).
- If a live run yields 0 alerts on camera, use the pre-added-keyword trick above, or record
  the Telegram segment separately right after a run that did alert.
- Keep the cursor calm; pause ~1 s on each number you mention.
- Tools: OBS Studio (free) or any screen recorder; trim dead seconds in editing.
