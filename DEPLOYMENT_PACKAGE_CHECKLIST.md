# Deployment Package Checklist — Client Handoff

Everything required to hand the running system to a client. Status legend:
✅ done/included · 🔲 client action (instructions provided).

## 1. Code & repository
- ✅ Source code pushed to GitHub (`main` branch, CI green)
- ✅ Git history clean of secrets (verified — token only in gitignored `.env`)
- ✅ `.env.example` with every variable documented
- ✅ Layered requirements files (`requirements*.txt`) + `Dockerfile.app` + `docker-compose.yml`
- 🔲 Transfer repository ownership to the client's GitHub org (Settings → Transfer), or add them as admin

## 2. Credentials (client-owned)
- 🔲 **Rotate the Telegram bot token** (@BotFather → Revoke) — the original appeared in the project brief
- 🔲 Put the new token in: local `.env` + GitHub secret `TELEGRAM_BOT_TOKEN`
- ✅ GitHub secret names documented (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
- ✅ No other credentials exist in the system (no paid APIs, no DB server)

## 3. Automation
- ✅ Scheduled scrape workflow live (every 6 h) and green
- ✅ Baseline/only-new alert behavior active (no alert floods on fresh databases)
- ✅ CI: Lint + Tests run on every push/PR

## 4. Hosted dashboard
- 🔲 Deploy on Streamlit Community Cloud (10 min, [STREAMLIT_DEPLOYMENT_PACKAGE.md](STREAMLIT_DEPLOYMENT_PACKAGE.md))
- ✅ Committed seed database so the app shows data immediately
- ✅ No secrets needed by the dashboard

## 5. Data
- ✅ Live database included (249 scraped jobs at delivery)
- ✅ Automatic backups (30-day retention) + restore procedure documented
- ✅ Export samples verifiable from Job Explorer (CSV/Excel/JSON)

## 6. Documentation handed over
- ✅ CLIENT_DELIVERY_PACKAGE.md (what you received)
- ✅ INSTALLATION.md (local / Docker / cloud)
- ✅ USER_GUIDE.md (daily use)
- ✅ ADMIN_GUIDE.md (keywords, sources, intervals, backup/restore)
- ✅ TELEGRAM_NOTIFICATION_ARCHITECTURE.md (alert behavior)
- ✅ FINAL_CLIENT_HANDOFF.md (handoff summary)
- ✅ PROJECT_COMPLETENESS_AUDIT.md (honest completion audit)
- ✅ Validation reports (scrapers / Telegram / dashboard / exports / final)

## 7. Visual assets
- ✅ 7 real dashboard screenshots in `screenshots/`
- 🔲 Screenshots 6–10 (Telegram client, exports in viewers, Docker, CI) — [SCREENSHOT_CAPTURE_GUIDE.md](SCREENSHOT_CAPTURE_GUIDE.md)
- ✅ Demo video script — [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md)

## 8. Acceptance test (run together with the client, ~10 min)
1. `python main.py --once` on a fresh clone → baseline summary arrives on Telegram
2. Second run → no duplicate alerts
3. Dashboard opens, all 7 pages render with data
4. Job Explorer: search "python" → export CSV downloads
5. GitHub → Actions → all three workflows green
6. Streamlit Cloud URL loads (after step 4 above)
