"""Job Explorer page: full-text search, faceted filters, and CSV/Excel/JSON export."""

from __future__ import annotations

import streamlit as st

from job_monitor.analytics import JobExporter
from job_monitor.dashboard.components import (
    DashboardContext,
    SOURCE_LABELS,
    empty_state,
    load_jobs,
    section,
)
from job_monitor.pipeline import FilterConfig, JobFilter


def render(ctx: DashboardContext) -> None:
    st.markdown("## 🔎 Job Explorer")
    st.caption("Search and slice every stored opportunity, then export the result.")
    jobs = load_jobs(ctx.db_path)
    if not jobs:
        empty_state()
        return

    sources = sorted({j.source for j in jobs})
    categories = sorted({j.category for j in jobs if j.category})
    max_score = max((j.score for j in jobs), default=0)

    with st.form("filters", border=True):
        c1, c2 = st.columns([3, 1])
        query = c1.text_input(
            "Search", placeholder="e.g. python scraping, telegram bot, shopify…",
            help="Matches title, company and extracted skills.",
        )
        sort_by = c2.selectbox("Sort by", ["score", "recent", "quality"],
                               format_func=str.capitalize)
        c3, c4, c5, c6 = st.columns([2, 2, 2, 1])
        chosen_sources = c3.multiselect(
            "Sources", sources, default=sources,
            format_func=lambda s: SOURCE_LABELS.get(s, s),
        )
        chosen_categories = c4.multiselect("Categories", categories)
        min_score = c5.slider("Min relevance", 0, int(max_score) or 1, 0)
        remote_only = c6.checkbox("Remote only")
        st.form_submit_button("Apply filters", type="primary", width="stretch")

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

    section("Results", f"{len(results)} of {len(jobs)} jobs match")

    exporter = JobExporter(results)
    df = exporter.to_dataframe()
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "score": st.column_config.ProgressColumn(
                "Relevance", min_value=0, max_value=max(int(max_score), 1), format="%d",
            ),
            "url": st.column_config.LinkColumn("Link", display_text="open"),
        },
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
