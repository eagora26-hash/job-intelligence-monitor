# Streamlit Deployment Package

Everything needed to put the dashboard online, for a complete beginner.
*(This is the packaged summary; the long-form walkthrough with the same values is
[DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md).)*

## Deployment facts

| Item | Value |
|---|---|
| **Repository URL** | `https://github.com/eagora26-hash/job-intelligence-monitor` |
| **Branch** | `main` |
| **Entrypoint (main file path)** | `job_monitor/dashboard/app.py` |
| **Python version** | Streamlit Cloud default works; set **3.12** in Advanced settings if a build fails |
| **Required Streamlit secrets** | **None** — the dashboard reads the committed database and sends nothing |
| **Required environment variables** | **None** for the dashboard. Alerts use GitHub Actions secrets instead: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |

## Deployment steps

1. **(Already done)** Code is on GitHub and CI is green.
2. **Add alert secrets** (one time): GitHub repo → **Settings → Secrets and variables →
   Actions** → add `TELEGRAM_BOT_TOKEN` (fresh token from @BotFather — rotate the old one
   first) and `TELEGRAM_CHAT_ID`.
3. Go to **https://share.streamlit.io** → **Continue with GitHub** → authorize.
4. **Create app → Deploy a public app from GitHub** and enter the three values from the
   table above (repository, branch, main file path) → **Deploy**.
5. Wait 2–4 minutes for the first build. Your dashboard is live at
   `https://<something>.streamlit.app` — bookmark and share it.

## Validation (after deploy)

- [ ] App loads with the dark Overview page and non-zero job counts
- [ ] Sidebar says "Showing: 📦 stored data"
- [ ] All 7 sidebar pages open without a red error box
- [ ] Job Explorer search + **Export CSV** works
- [ ] GitHub → Actions → run **Scheduled Scrape** manually → green run; dashboard data
      refreshes itself afterwards (Actions commit → auto-redeploy)

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: job_monitor` | Main file path must be exactly `job_monitor/dashboard/app.py`. |
| Dependency build error | App **Settings → Advanced** → Python 3.12 → Reboot. |
| Shows demo data | Committed DB missing on the branch — run the Scheduled Scrape action once. |
| App asleep / slow first load | Free tier sleeps after inactivity; first visit wakes it (~30 s). |
| "Scrape live now" data disappears later | Expected (ephemeral container); durable data comes from the Action's commits. |
| No Telegram alerts | Alerts come from GitHub Actions, not the dashboard — check secrets + the Action log. First-ever run sends only the baseline summary by design. |
