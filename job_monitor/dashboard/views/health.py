"""Source Health & Observability page: per-source health + system metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from job_monitor.dashboard.components import DashboardContext, load_health, load_overview
from job_monitor.services.state import StateStore

_STATUS_EMOJI = {"healthy": "🟢", "degraded": "🟡", "failing": "🔴", "unknown": "⚪"}


def render(ctx: DashboardContext) -> None:
    st.markdown("## 🩺 Source Health")
    st.caption("Per-source reliability and the platform's operational metrics.")

    health = load_health(ctx.db_path)
    if not health:
        st.info("No scrape runs recorded yet. Run `python main.py --once` to populate health.")
    else:
        cols = st.columns(min(len(health), 5))
        for col, h in zip(cols, health):
            col.metric(
                f"{_STATUS_EMOJI.get(h.status, '⚪')} {h.source}",
                f"{h.success_rate * 100:.0f}%",
                help=f"ok={h.success_count} fail={h.failure_count}",
            )

        rows = [
            {
                "source": h.source,
                "status": h.status,
                "success": h.success_count,
                "failure": h.failure_count,
                "avg_ms": round(h.avg_response_ms, 0),
                "last_jobs": h.last_jobs_found,
                "last_success": h.last_success.strftime("%Y-%m-%d %H:%M") if h.last_success else "—",
                "last_error": (h.last_error[:60] + "…") if len(h.last_error) > 60 else h.last_error,
            }
            for h in health
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    st.divider()
    st.markdown("#### ⚙️ System metrics")
    metrics = load_overview(ctx.db_path)
    db_path = Path(ctx.db_path)
    db_size = db_path.stat().st_size / 1024 if db_path.exists() else 0
    state = StateStore(ctx.settings.state_file).load()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Database size", f"{db_size:.0f} KB")
    m2.metric("Total jobs", metrics["total_jobs"])
    m3.metric("Total runs", state.total_runs)
    m4.metric("Notifications sent", metrics["notified_count"])

    st.caption(
        f"Last run: {state.last_run or '—'}  •  Last success: {state.last_successful_run or '—'}"
    )
