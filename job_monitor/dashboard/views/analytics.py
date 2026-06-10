"""Insights page: trend analysis, skill heatmap, source comparison, and leaderboards."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from job_monitor.dashboard.components import (
    DashboardContext,
    SOURCE_LABELS,
    bar_from_mapping,
    empty_state,
    grouped_bar,
    heatmap_from_matrix,
    line_from_mapping,
    load_jobs_df,
    load_jobs_per_day,
    load_overview,
    load_reliability,
    load_skill_matrix,
    load_source_stats,
    load_weekly_trend,
    section,
)


def render(ctx: DashboardContext) -> None:
    st.markdown("## 📈 Insights")
    st.caption("Trend analysis, demand intelligence and source benchmarking.")
    if load_overview(ctx.db_path)["total_jobs"] == 0:
        empty_state()
        return

    # ---- trends ---------------------------------------------------------------
    section("Trend analysis", "discovery volume over time")
    t1, t2 = st.columns([3, 2])
    with t1:
        days = st.slider("Daily window (days)", min_value=7, max_value=60, value=30, step=1)
        fig = line_from_mapping(load_jobs_per_day(ctx.db_path, days=days),
                                title="New jobs per day", x_label="Day", y_label="Jobs")
        if fig:
            st.plotly_chart(fig, width="stretch")
    with t2:
        weekly = load_weekly_trend(ctx.db_path, weeks=8)
        fig = bar_from_mapping(weekly, title="New jobs per week (8w)",
                               x_label="ISO week", y_label="Jobs")
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Weekly trend appears after the first week of data.")

    # ---- skill demand heatmap ----------------------------------------------------
    section("Skill demand heatmap", "which sources ask for which skills")
    fig = heatmap_from_matrix(load_skill_matrix(ctx.db_path, top=12),
                              title="Skill × source job counts")
    if fig:
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No skills extracted yet.")

    # ---- source comparison ----------------------------------------------------------
    section("Source comparison", "volume vs. relevance vs. data quality")
    stats = load_source_stats(ctx.db_path)
    if stats:
        df = pd.DataFrame(stats)
        df["source"] = df["source"].map(lambda s: SOURCE_LABELS.get(s, s))
        fig = grouped_bar(df, x="source", ys=["jobs", "avg_score", "avg_quality"],
                          title="Jobs · avg relevance · avg quality, per source")
        if fig:
            st.plotly_chart(fig, width="stretch")

    # ---- leaderboards -----------------------------------------------------------------
    section("Leaderboards", "the best opportunities and the most reliable sources")
    l1, l2 = st.columns(2)
    with l1:
        st.markdown("**🏆 Job score leaderboard**")
        jobs = load_jobs_df(ctx.db_path).sort_values("score", ascending=False).head(10)
        st.dataframe(
            jobs[["title", "source", "score", "url"]],
            hide_index=True, width="stretch",
            column_config={
                "score": st.column_config.ProgressColumn(
                    "Relevance", min_value=0,
                    max_value=max(int(jobs["score"].max()), 1), format="%d"),
                "url": st.column_config.LinkColumn("Link", display_text="open"),
            },
        )
    with l2:
        st.markdown("**🥇 Source reliability leaderboard**")
        rel = pd.DataFrame(load_reliability(ctx.db_path))
        if rel.empty:
            st.info("Run the pipeline to record source health.")
        else:
            rel["source"] = rel["source"].map(lambda s: SOURCE_LABELS.get(s, s))
            st.dataframe(
                rel[["source", "success_rate", "runs", "avg_response_ms", "last_jobs_found"]],
                hide_index=True, width="stretch",
                column_config={
                    "success_rate": st.column_config.ProgressColumn(
                        "Success rate", min_value=0, max_value=100, format="%d%%"),
                    "avg_response_ms": st.column_config.NumberColumn("Avg latency (ms)"),
                    "last_jobs_found": st.column_config.NumberColumn("Last yield"),
                },
            )
