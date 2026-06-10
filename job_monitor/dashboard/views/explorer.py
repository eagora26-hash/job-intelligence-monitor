"""Job Explorer page: full-text search, faceted filters, and CSV/Excel/JSON export."""

from __future__ import annotations

import streamlit as st

from job_monitor.analytics import JobExporter
from job_monitor.dashboard.components import DashboardContext, empty_state, load_jobs
from job_monitor.pipeline import FilterConfig, JobFilter


def render(ctx: DashboardContext) -> None:
    st.subheader("🔎 Job Explorer")
    jobs = load_jobs(ctx.db_path)
    if not jobs:
        empty_state()
        return

    sources = sorted({j.source for j in jobs})
    categories = sorted({j.category for j in jobs if j.category})
    max_score = max((j.score for j in jobs), default=0)

    with st.form("filters"):
        c1, c2, c3 = st.columns(3)
        query = c1.text_input("Search (title, company, skills)")
        chosen_sources = c2.multiselect("Sources", sources, default=sources)
        chosen_categories = c3.multiselect("Categories", categories)
        c4, c5, c6 = st.columns(3)
        min_score = c4.slider("Min relevance score", 0, int(max_score) or 1, 0)
        remote_only = c5.checkbox("Remote only")
        sort_by = c6.selectbox("Sort by", ["score", "recent", "quality"])
        st.form_submit_button("Apply filters", width="stretch")

    # Apply structured filters via the same JobFilter used by the pipeline.
    flt = JobFilter(
        FilterConfig(
            include_keywords=[query] if query else [],
            sources=chosen_sources or None,
            min_score=min_score,
            remote_only=remote_only,
        )
    )
    results = flt.apply(jobs)
    if chosen_categories:
        results = [j for j in results if j.category in chosen_categories]

    sort_key = {"score": lambda j: -j.score, "quality": lambda j: -j.quality_score,
                "recent": lambda j: (j.first_seen or j.scraped_at)}
    reverse = sort_by == "recent"
    results = sorted(results, key=sort_key[sort_by], reverse=reverse)

    st.caption(f"**{len(results)}** of {len(jobs)} jobs match.")

    exporter = JobExporter(results)
    df = exporter.to_dataframe()
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={"url": st.column_config.LinkColumn("Link", display_text="open")},
    )

    d1, d2, d3, _ = st.columns([1, 1, 1, 3])
    d1.download_button(
        "⬇️ Export CSV", data=exporter.to_csv_bytes(),
        file_name="jobs_export.csv", mime="text/csv", width="stretch",
        disabled=not results,
    )
    d2.download_button(
        "⬇️ Export Excel", data=exporter.to_excel_bytes(),
        file_name="jobs_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch", disabled=not results,
    )
    d3.download_button(
        "⬇️ Export JSON", data=exporter.to_json_bytes(),
        file_name="jobs_export.json", mime="application/json",
        width="stretch", disabled=not results,
    )
