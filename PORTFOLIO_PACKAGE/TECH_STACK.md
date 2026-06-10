# Tech Stack

Every major technology in the project and why it was chosen.

## Acquisition (scraping)

- **Scrapling** *(vendored engine)* — provides the adaptive `Selector` parser (CSS/XPath/
  regex/JSON over lxml) used by every scraper, plus the optional `StealthyFetcher` browser
  fallback. The project reuses its parser and its HTTP philosophy while staying browser-free.
- **curl_cffi** — HTTP client that impersonates real browsers' TLS fingerprints. This is
  what lets plain HTTP pass anti-bot checks that block `requests`/`httpx` (and, in Fiverr's
  case, even real headless browsers). Core of the acquisition layer.
- **lxml + cssselect** — fast, battle-tested HTML/XML parsing underneath the Selector.
- **tenacity** — declarative retry policies (exponential backoff) around every fetch.
- **Playwright / Patchright** *(optional)* — stealth browser fallback for JS-only targets;
  intentionally not required at runtime so CI and containers stay slim.

## Domain & configuration

- **pydantic v2** — typed, validated domain models (`JobRecord`, `SourceHealth`, …); data
  is validated at the boundary, not deep inside the app.
- **pydantic-settings + python-dotenv** — all configuration from environment/`.env` with
  types, defaults and aliases; zero hardcoded secrets.
- **SQLite** — single-file, zero-ops persistence with `UNIQUE` URL dedup, WAL mode, and a
  repository layer on top (no SQL outside `database/`). Right-sized for the workload;
  the repository pattern keeps a Postgres swap straightforward.

## Orchestration

- **ThreadPoolExecutor** — sources scraped concurrently (network-bound), results stored
  serially (SQLite write discipline).
- **APScheduler** — interval scheduling with graceful shutdown for `--loop` mode.
- **httpx** — Telegram Bot API calls (timeouts, clean error surface).

## Product surface

- **Streamlit** — the 7-page dashboard; chosen for speed-of-iteration and free hosting on
  Community Cloud. Custom CSS design system on top for the SaaS look.
- **Plotly** — interactive charts (trends, heatmap, comparisons) with a consistent dark
  template.
- **pandas + openpyxl** — dataframe backbone for tables and the CSV/Excel/JSON exporters.
- **FastAPI** — the REST extension layer (7 endpoints), TestClient-covered.

## Operations & quality

- **Docker + Docker Compose** — one-command startup of scheduler + dashboard with a shared
  SQLite volume.
- **GitHub Actions** — three workflows: ruff lint, pytest matrix (3.11/3.12), and the
  6-hourly scheduled scrape that sends alerts and commits the refreshed database (which in
  turn redeploys the hosted dashboard — a free, serverless cron).
- **pytest (+ pytest-cov)** — 65 tests: fixture-based parser tests (no network), repository
  round-trips, runner behavior with fake scrapers and a capturing notifier, headless
  dashboard smoke via Streamlit's `AppTest`.
- **ruff** — linting, enforced in CI.

## Integrations & extensions

- **Telegram Bot API** — alert channel, called directly over HTTPS (no SDK dependency),
  behind a swappable `Notifier` interface.
- **MCP registry / knowledge-graph store / AI-enricher seam** — working extension
  interfaces (rule-based enricher included; LLM, Graphiti and MCP plugins slot in without
  touching core code).
