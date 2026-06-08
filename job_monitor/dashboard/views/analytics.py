"""Analytics page: distributions (source/category), daily trend, skills, score histogram."""

from __future__ import annotations

import streamlit as st

from job_monitor.dashboard.components import (
    DashboardContext,
    bar_from_mapping,
    empty_state,
    line_from_mapping,
    load_by_category,
    load_by_source,
    load_jobs_per_day,
    load_overview,
    load_score_distribution,
    load_skill_frequency,
)


def render(ctx: DashboardContext) -> None:
    st.subheader("📈 Analytics")
    if load_overview(ctx.db_path)["total_jobs"] == 0:
        empty_state()
        return

    days = st.slider("Trend window (days)", min_value=7, max_value=60, value=30, step=1)
    trend = line_from_mapping(
        load_jobs_per_day(ctx.db_path, days=days),
        title="New jobs per day", x_label="Day", y_label="Jobs",
    )
    if trend:
        st.plotly_chart(trend, width="stretch")

    left, right = st.columns(2)
    with left:
        fig = bar_from_mapping(
            load_by_source(ctx.db_path), title="Jobs by source",
            x_label="Source", y_label="Jobs",
        )
        if fig:
            st.plotly_chart(fig, width="stretch")
    with right:
        fig = bar_from_mapping(
            load_by_category(ctx.db_path), title="Jobs by category",
            x_label="Category", y_label="Jobs", horizontal=True,
        )
        if fig:
            st.plotly_chart(fig, width="stretch")

    left2, right2 = st.columns(2)
    with left2:
        skills = dict(load_skill_frequency(ctx.db_path, top=15))
        fig = bar_from_mapping(
            skills, title="Most in-demand skills",
            x_label="Skill", y_label="Mentions", horizontal=True,
        )
        if fig:
            st.plotly_chart(fig, width="stretch")
    with right2:
        fig = bar_from_mapping(
            load_score_distribution(ctx.db_path), title="Relevance score distribution",
            x_label="Score band", y_label="Jobs",
        )
        if fig:
            st.plotly_chart(fig, width="stretch")
