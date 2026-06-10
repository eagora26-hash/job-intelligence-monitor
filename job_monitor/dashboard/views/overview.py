"""Executive Overview: headline KPIs, smart job intelligence, and opportunity tables."""

from __future__ import annotations

import streamlit as st

from job_monitor.dashboard.components import (
    DashboardContext,
    SOURCE_LABELS,
    bar_from_mapping,
    empty_state,
    hero,
    load_by_category,
    load_by_source,
    load_intelligence,
    load_jobs_df,
    load_overview,
    load_score_distribution,
    load_skill_frequency,
    pie_from_mapping,
    section,
)


def render(ctx: DashboardContext) -> None:
    metrics = load_overview(ctx.db_path)
    if metrics["total_jobs"] == 0:
        empty_state("No jobs in the database yet.")
        return

    intel = load_intelligence(ctx.db_path)
    hero(
        "Job Intelligence Monitor",
        "Five marketplaces, one scored opportunity feed — scraped, deduplicated and "
        "alerted automatically.",
        chips=[
            f"🛰️ {metrics['source_count']} active sources",
            f"🧠 {metrics['skill_count']} skills tracked",
            f"📨 {metrics['notified_count']} alerts delivered",
            f"❤️ fleet health {intel['health_score']}%",
        ],
    )

    # ---- executive KPI band ------------------------------------------------
    section("Executive overview", "live numbers from the monitoring database")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total jobs", f"{metrics['total_jobs']:,}")
    c2.metric("New today", metrics["jobs_today"],
              delta=f"+{intel['new_last_24h']} last 24h")
    c3.metric("Avg. relevance", metrics["avg_score"],
              help="Mean keyword-relevance score across all stored jobs (0–50+).")
    c4.metric("Active sources", metrics["source_count"])
    c5.metric("Alerts delivered", metrics["notified_count"],
              help="Jobs pushed to Telegram (at-most-once per job).")
    c6.metric("Source health", f"{intel['health_score']}%",
              help="Run-weighted scrape success rate across all sources.")

    # ---- smart job intelligence ---------------------------------------------
    section("Smart job intelligence", "what the market wants right now")
    i1, i2, i3 = st.columns(3)
    i1.metric("🔥 Most active source",
              str(intel["most_active_source"]), f"{intel['most_active_count']} jobs")
    top_skills = load_skill_frequency(ctx.db_path, top=10)
    i2.metric("📈 Top trending skill",
              top_skills[0][0] if top_skills else "—",
              f"{top_skills[0][1]} mentions" if top_skills else None)
    categories = load_by_category(ctx.db_path)
    top_cat = max(categories.items(), key=lambda kv: kv[1]) if categories else ("—", 0)
    i3.metric("🏷️ Top category", top_cat[0], f"{top_cat[1]} jobs")

    left, right = st.columns(2)
    with left:
        fig = bar_from_mapping(dict(top_skills), title="Top trending skills",
                               x_label="Skill", y_label="Mentions", horizontal=True)
        if fig:
            st.plotly_chart(fig, width="stretch")
    with right:
        fig = bar_from_mapping(categories, title="Top categories",
                               x_label="Category", y_label="Jobs", horizontal=True)
        if fig:
            st.plotly_chart(fig, width="stretch")

    d1, d2 = st.columns(2)
    with d1:
        fig = bar_from_mapping(load_score_distribution(ctx.db_path),
                               title="Relevance distribution",
                               x_label="Score band", y_label="Jobs")
        if fig:
            st.plotly_chart(fig, width="stretch")
    with d2:
        by_source = {SOURCE_LABELS.get(k, k): v for k, v in load_by_source(ctx.db_path).items()}
        fig = pie_from_mapping(by_source, title="Category distribution by source")
        if fig:
            st.plotly_chart(fig, width="stretch")

    # ---- opportunity tables ---------------------------------------------------
    section("Top opportunities", "highest-relevance matches, ready to open")
    df = load_jobs_df(ctx.db_path).sort_values("score", ascending=False).head(10)
    st.dataframe(
        df[["title", "company", "source", "score", "category", "salary", "url"]],
        hide_index=True,
        width="stretch",
        column_config={
            "score": st.column_config.ProgressColumn(
                "Relevance", min_value=0, max_value=max(int(df["score"].max()), 1),
                format="%d",
            ),
            "url": st.column_config.LinkColumn("Link", display_text="open"),
        },
    )

    section("Latest discoveries", "most recently scraped jobs across all sources")
    latest = load_jobs_df(ctx.db_path).sort_values("first_seen", ascending=False).head(12)
    st.dataframe(
        latest[["first_seen", "title", "company", "source", "score", "category", "url"]],
        hide_index=True,
        width="stretch",
        column_config={
            "first_seen": st.column_config.DatetimeColumn("Discovered", format="MMM D, HH:mm"),
            "url": st.column_config.LinkColumn("Link", display_text="open"),
        },
    )
