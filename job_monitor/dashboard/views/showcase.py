"""Portfolio Showcase page: explains the product's architecture and value to a client."""

from __future__ import annotations

import streamlit as st

from job_monitor.dashboard.components import (
    DashboardContext,
    load_overview,
    section,
)

_ARCHITECTURE_DOT = """
digraph {
  rankdir=LR;
  bgcolor="transparent";
  node [shape=box, style="rounded,filled", fillcolor="#1A2336", color="#31416A",
        fontcolor="#E8ECF6", fontname="Helvetica", fontsize=11, margin="0.18,0.10"];
  edge [color="#6C8CFF", fontcolor="#9AA6C3", fontname="Helvetica", fontsize=9];

  subgraph cluster_src {
    label="Sources"; color="#27314A"; fontcolor="#8A96B5";
    RemoteOK; WWR [label="We Work Remotely"]; Freelancer; Fiverr; Wellfound;
  }
  Scrapers [label="Concurrent scrapers\\n(curl_cffi impersonation)", fillcolor="#1D2A45"];
  Normalize [label="Normalizer\\n(canonical JobRecord)"];
  Enrich [label="Enrichment\\nscore · category · skills · quality"];
  DB [label="SQLite\\ndedup · change history · health", fillcolor="#1D2A45"];
  Telegram [label="Telegram alerts\\nnew jobs only", fillcolor="#233524"];
  Dash [label="Streamlit dashboard\\nanalytics · search · export", fillcolor="#233524"];
  API [label="REST API\\n(FastAPI)"];

  {RemoteOK WWR Freelancer Fiverr Wellfound} -> Scrapers;
  Scrapers -> Normalize -> Enrich -> DB;
  DB -> Telegram [label="baseline → only new"];
  DB -> Dash; DB -> API;
}
"""


def render(ctx: DashboardContext) -> None:
    st.markdown("## 🏆 Portfolio Showcase")
    st.caption("What this product is, how it works, and why it matters — in two minutes.")

    m = load_overview(ctx.db_path)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Marketplaces monitored", "5")
    c2.metric("Jobs under management", f"{m['total_jobs']:,}")
    c3.metric("Automated tests", "65+")
    c4.metric("Alert latency", "< 1 min", help="From discovery to Telegram push.")

    # ---- architecture --------------------------------------------------------
    section("Architecture", "layered design — every box is a swappable module")
    st.graphviz_chart(_ARCHITECTURE_DOT, width="stretch")
    st.caption(
        "Layers depend downward only: interfaces (CLI / dashboard / API) → orchestration "
        "(concurrent runner, scheduler, resume state) → services (enrichment, analytics, "
        "notifications, backup) → domain (models, repositories) → acquisition (scrapers)."
    )

    # ---- data flow --------------------------------------------------------------
    section("Data flow", "what happens on every monitoring cycle")
    st.markdown(
        """
1. **Scrape** — all enabled sources run **in parallel**; a failing source is isolated, logged
   and reported, never fatal.
2. **Normalize** — every raw posting becomes one canonical `JobRecord`; no source-specific
   shape leaks downstream.
3. **Enrich** — keyword relevance score, one of 8 auto-categories, extracted skills, and a
   data-quality score.
4. **Store** — URL-deduplicated upsert into SQLite; content changes are diffed into a full
   `job_history` audit trail.
5. **Notify** — first run silently establishes a baseline; afterwards **only never-seen jobs**
   above the relevance threshold are pushed to Telegram (at-most-once, state in DB).
6. **Observe** — per-source health, daily snapshots, resume checkpoint, rotating logs.
        """
    )

    # ---- sources ------------------------------------------------------------------
    section("Sources", "live extraction status, validated 2026-06-10")
    st.markdown(
        """
| Source | Method | Live yield |
|---|---|---|
| RemoteOK | public JSON API | ~100 jobs/run |
| We Work Remotely | RSS (3 feeds) | ~61 jobs/run |
| Freelancer | public projects API | ~97 jobs/run |
| Fiverr | embedded JSON data island | ~90 gigs/run |
| Wellfound | JSON island (parser ready) | blocked by Cloudflare — isolated gracefully |
        """
    )

    # ---- automation / notifications / export ------------------------------------------
    section("Automation features")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown(
            "**🔁 Continuous monitoring**\n\n"
            "- APScheduler loop (`--loop`) with graceful shutdown\n"
            "- GitHub Actions cron every 6 h\n"
            "- resume state survives restarts\n"
            "- 30-day rolling backups + archive DB"
        )
    with a2:
        st.markdown(
            "**📨 Notification system**\n\n"
            "- baseline run → one summary, zero spam\n"
            "- then **only new** jobs, never repeats\n"
            "- relevance threshold + per-source filter\n"
            "- rate-capped (15/run + rollup message)"
        )
    with a3:
        st.markdown(
            "**📤 Export system**\n\n"
            "- CSV / Excel / JSON, one click\n"
            "- exports respect active filters\n"
            "- same engine powers scheduled file exports\n"
            "- Google-Sheets-ready architecture"
        )

    st.divider()
    st.markdown(
        "**Built with:** Python · Scrapling · curl_cffi · pydantic · SQLite · APScheduler · "
        "pandas · Streamlit · Plotly · FastAPI · Docker · GitHub Actions · pytest *(65+ tests, "
        "CI on every push)*"
    )
