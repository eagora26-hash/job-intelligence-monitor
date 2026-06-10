# Project Metrics

Measured at delivery (2026-06-10). Sources: repository, test runner, live validation runs.

## Scope
| Metric | Value |
|---|---|
| Sources monitored | **5** implemented (RemoteOK, We Work Remotely, Freelancer, Fiverr, Wellfound) — **4 extracting live** |
| Live yield per run | ~350 jobs (RemoteOK ~100 · WWR ~61 · Freelancer ~97 · Fiverr ~90) |
| Jobs in database at delivery | **249** real scraped jobs (208 with alert state) |
| Dashboard pages | **7** (Overview, Insights, Job Explorer, Source Health, System Status, Portfolio Showcase, Configuration) |
| Notification channels | **1 live** (Telegram) behind a channel-agnostic `Notifier` interface (Slack/email-ready) |
| Export formats | **3** (CSV, Excel, JSON) |
| Job categories (auto-classified) | 8 |
| Skills tracked | 30+ taxonomy (31 distinct extracted at delivery) |
| REST API endpoints | 7 (FastAPI) |

## Quality
| Metric | Value |
|---|---|
| Automated tests | **65** (pytest), all passing |
| Coverage | **67%** (network/browser paths excluded; parsing covered via fixtures) |
| Lint | ruff — clean |
| CI | 3 GitHub Actions workflows (Lint, Tests on 3.11/3.12, Scheduled Scrape) — all green |
| Headless dashboard validation | 7 pages × 0 exceptions / 0 errors |
| Live validations performed | scraper (2 runs/source), Telegram delivery + dedup (3-cycle baseline test), exports, server health |

## Database entities
| Entity | Purpose |
|---|---|
| `jobs` | canonical records: source, title, company, url (UNIQUE), score, category, skills, quality, remote, salary, first_seen, last_seen, notified, content_hash |
| `job_history` | field-level change audit (title/salary/description diffs) |
| `source_health` | per-source success/failure counts, latency, last error |
| `daily_snapshots` | historical totals for trend analytics |
| `archive.db` | separate archive database for aged-out jobs |

## Codebase
| Metric | Value |
|---|---|
| Application package | `job_monitor/` — 17 modules (config, models, scrapers, normalizers, pipeline, database, notifications, analytics, dashboard, services, observability, scheduler, ai, graph, mcp, api) |
| Git history | 21 layered commits over 3 days (2026-06-08 → 06-10) |
| Documentation files | 25+ (guides, validation reports, architecture, portfolio) |
| Screenshots | 7 real dashboard captures |

## Technologies
Python 3.11–3.14 · Scrapling (vendored engine) · curl_cffi · lxml · pydantic /
pydantic-settings · SQLite · APScheduler · httpx · tenacity · pandas · openpyxl ·
Streamlit · Plotly · FastAPI · Docker / Compose · GitHub Actions · pytest · ruff
*(details in [TECH_STACK.md](TECH_STACK.md))*
