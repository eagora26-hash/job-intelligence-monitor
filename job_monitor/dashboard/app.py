"""Streamlit entrypoint for the Job Intelligence Monitor dashboard.

Run with::

    streamlit run job_monitor/dashboard/app.py

A single entrypoint with sidebar navigation that dispatches to the view modules in
``job_monitor/dashboard/views`` (version-agnostic; avoids Streamlit's magic ``pages/`` folder).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when launched via `streamlit run`.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from job_monitor.dashboard.components import (  # noqa: E402
    ensure_data,
    get_context,
    run_live_scrape,
)
from job_monitor.dashboard.views import (  # noqa: E402
    analytics,
    config,
    explorer,
    health,
    overview,
)

_DATA_MODE_LABEL = {
    "existing": "📦 stored data",
    "live": "🌐 freshly scraped (live)",
    "demo": "🧪 demo data (live sources unavailable)",
}

_PAGES = {
    "Overview": overview.render,
    "Analytics": analytics.render,
    "Job Explorer": explorer.render,
    "Source Health": health.render,
    "Configuration": config.render,
}


def main() -> None:
    st.set_page_config(
        page_title="Job Intelligence Monitor",
        page_icon="🛰️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    ctx = get_context()

    st.sidebar.title("🛰️ Job Intelligence Monitor")
    st.sidebar.caption("Multi-source AI job monitoring platform")
    choice = st.sidebar.radio("Navigate", list(_PAGES.keys()), label_visibility="collapsed")
    st.sidebar.divider()

    # Bootstrap data on first load (live scrape → demo fallback) so the app is never blank.
    data_info = ensure_data(ctx.db_path)

    if st.sidebar.button("🌐 Scrape live now", width="stretch", type="primary"):
        with st.spinner("Scraping live sources…"):
            try:
                result = run_live_scrape(ctx.db_path)
                st.sidebar.success(f"+{result['new']} new jobs (of {result['scraped']} scraped)")
            except Exception as exc:  # noqa: BLE001
                st.sidebar.error(f"Scrape failed: {exc}")
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("🔄 Refresh view", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.caption(f"Showing: {_DATA_MODE_LABEL.get(str(data_info.get('mode')), 'data')}")
    st.sidebar.caption(
        "Telegram alerts are sent by the scheduled scrape (CLI / GitHub Action), not the dashboard."
    )

    st.title("Job Intelligence Monitor")
    _PAGES[choice](ctx)


main()
