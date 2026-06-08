"""Overview page: headline KPIs, source split, and the latest/top jobs tables."""

from __future__ import annotations

import streamlit as st

from job_monitor.dashboard.components import (
    DashboardContext,
    empty_state,
    load_by_source,
    load_jobs_df,
    load_overview,
    pie_from_mapping,
)


def render(ctx: DashboardContext) -> None:
    st.subheader("📊 Overview")
    metrics = load_overview(ctx.db_path)

    if metrics["total_jobs"] == 0:
        empty_state("No jobs in the database yet.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total jobs", metrics["total_jobs"])
    c2.metric("New today", metrics["jobs_today"])
    c3.metric("Sources", metrics["source_count"])
    c4.metric("Avg. relevance", metrics["avg_score"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Remote", metrics["remote_count"])
    c6.metric("Categories", metrics["category_count"])
    c7.metric("Skills tracked", metrics["skill_count"])
    c8.metric("Notified", metrics["notified_count"])

    st.divider()
    left, right = st.columns([1, 1])
    with left:
        fig = pie_from_mapping(load_by_source(ctx.db_path), title="Jobs by source")
        if fig:
            st.plotly_chart(fig, width="stretch")
    with right:
        st.markdown("#### 🏆 Top opportunities (by relevance)")
        df = load_jobs_df(ctx.db_path).sort_values("score", ascending=False).head(8)
        st.dataframe(
            df[["title", "company", "source", "score", "category"]],
            hide_index=True,
            width="stretch",
        )

    st.divider()
    st.markdown("#### 🆕 Latest jobs")
    latest = load_jobs_df(ctx.db_path).sort_values("first_seen", ascending=False).head(15)
    st.dataframe(
        latest[["title", "company", "source", "score", "category", "salary", "url"]],
        hide_index=True,
        width="stretch",
        column_config={"url": st.column_config.LinkColumn("Link", display_text="open")},
    )
