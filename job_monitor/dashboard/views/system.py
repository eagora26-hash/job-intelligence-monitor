"""System Status page (demonstration mode): live operational state of the whole platform."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from job_monitor.dashboard.components import (
    DashboardContext,
    SOURCE_LABELS,
    load_health,
    load_jobs,
    load_overview,
    section,
)
from job_monitor.services.state import StateStore


def _fmt_ts(value) -> str:
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)[:16].replace("T", " ")


def render(ctx: DashboardContext) -> None:
    st.markdown("## 🖥️ System Status")
    st.caption("Live operational state: alerts, scrapes, exports and database statistics.")

    state = StateStore(ctx.settings.state_file).load()
    metrics = load_overview(ctx.db_path)
    health = load_health(ctx.db_path)

    # ---- status band -----------------------------------------------------------
    ok_sources = sum(1 for h in health if h.status == "healthy")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("System", "🟢 Operational" if ok_sources else "🟡 Idle",
              help="Healthy when at least one source scrapes successfully.")
    s2.metric("Total runs", state.total_runs)
    s3.metric("Last run", _fmt_ts(state.last_run))
    s4.metric("Last success", _fmt_ts(state.last_successful_run))

    # ---- latest alerts ------------------------------------------------------------
    section("Latest alerts", "most recent jobs pushed to Telegram")
    notified_jobs = sorted(
        (j for j in load_jobs(ctx.db_path) if j.notified),
        key=lambda j: (j.first_seen or datetime.min.replace(tzinfo=None)).isoformat(),
        reverse=True,
    )[:8]
    if not notified_jobs:
        st.info("No alerts recorded yet — alerts appear after the first post-baseline "
                "discovery of a high-relevance job.")
    else:
        rows = [
            {
                "alerted": _fmt_ts(j.first_seen),
                "title": j.title,
                "source": SOURCE_LABELS.get(j.source, j.source),
                "score": j.score,
                "url": j.url,
            }
            for j in notified_jobs
        ]
        st.dataframe(
            pd.DataFrame(rows), hide_index=True, width="stretch",
            column_config={"url": st.column_config.LinkColumn("Link", display_text="open")},
        )

    # ---- latest scrapes --------------------------------------------------------------
    section("Latest scrapes", "per-source outcome of the most recent runs")
    if state.source_status:
        rows = [
            {
                "source": SOURCE_LABELS.get(name, name),
                "status": "✅ success" if s.last_status == "success" else "❌ failure",
                "last run": _fmt_ts(s.last_run),
                "jobs stored": s.last_jobs_found,
                "error": s.last_error or "—",
            }
            for name, s in state.source_status.items()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("No scrape state yet — run `python main.py --once`.")

    # ---- latest exports -----------------------------------------------------------------
    section("Latest exports", "files produced by the export engine")
    export_dir = Path(ctx.settings.export_dir)
    files = sorted(export_dir.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        rows = [
            {
                "file": f.name,
                "size": f"{f.stat().st_size / 1024:.1f} KB",
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            }
            for f in files[:10]
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("No export files yet — use Job Explorer → Export, or the CLI exporter.")

    # ---- database statistics ----------------------------------------------------------------
    section("Database statistics")
    db_path = Path(ctx.db_path)
    db_size = db_path.stat().st_size / 1024 if db_path.exists() else 0
    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Database size", f"{db_size:,.0f} KB")
    d2.metric("Jobs", f"{metrics['total_jobs']:,}")
    d3.metric("Notified", f"{metrics['notified_count']:,}")
    d4.metric("Categories", metrics["category_count"])
    d5.metric("Skills", metrics["skill_count"])
    st.caption(
        "Tables: jobs · job_history (change audit) · source_health · daily_snapshots. "
        "Deduplication is enforced by a UNIQUE constraint on the job URL."
    )
