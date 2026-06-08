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

from job_monitor.dashboard.components import get_context  # noqa: E402
from job_monitor.dashboard.views import (  # noqa: E402
    analytics,
    config,
    explorer,
    health,
    overview,
)

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

    st.sidebar.title("🛰️ Job Intelligence Monitor")
    st.sidebar.caption("Multi-source AI job monitoring platform")
    choice = st.sidebar.radio("Navigate", list(_PAGES.keys()), label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.caption(
        "Data via the SQLite store. Seed with `python generate_demo_data.py` "
        "or scrape with `python main.py --once`."
    )

    ctx = get_context()
    st.title("Job Intelligence Monitor")
    _PAGES[choice](ctx)


main()
