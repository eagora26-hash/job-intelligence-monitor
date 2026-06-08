# Roadmap — Job Intelligence Monitor

> Roadmap for the **application**. The vendored Scrapling engine's original roadmap is preserved
> in [README_SCRAPLING.md](README_SCRAPLING.md).

## ✅ Shipped (v1.0)

- 5 source scrapers (RemoteOK, We Work Remotely, Freelancer, Fiverr, Wellfound) + normalization
- Relevance scoring, auto-categorization, skill extraction, data-quality scoring
- SQLite persistence with dedup, change history, source health, daily snapshots
- Concurrent pipeline runner with per-source failure isolation + resume state
- Telegram notifications (new jobs, daily summary, startup, errors)
- Streamlit dashboard (overview, analytics, explorer, health, configuration)
- CSV / Excel / JSON export · demo-data generator
- Backup + archive services
- Extension layers: AI enrichment, knowledge graph, MCP registry, FastAPI REST API
- Docker Compose, GitHub Actions (lint + tests), 63 tests

## 🔜 Near-term

- [ ] LLM-powered daily "opportunity digest" via the AI-enrichment seam (Claude/OpenAI)
- [ ] Additional notifier implementations (Slack, Discord, email) — interface already supports it
- [ ] More sources (remote.co, Jobicy, Working Nomads, python.org/jobs)
- [ ] Richer change-detection UI (diff timeline per job)
- [ ] Scheduled backups + archive via the scheduler

## 🌅 Longer-term

- [ ] Hosted read-only demo (Streamlit Community Cloud / Fly.io)
- [ ] Postgres backend + Alembic migrations for multi-user/hosted scale
- [ ] Saved searches + per-user alert profiles (the seed of a real SaaS)
- [ ] Browser-based stealth fetching enabled by default for anti-bot sources
- [ ] Full MCP server exposing `search_jobs` / `get_analytics` to agent tooling
