"""Shared dashboard helpers: cached data access, context, and Plotly chart builders.

All database reads are funneled through ``st.cache_data``-wrapped functions keyed on the DB
path + a TTL, so pages stay snappy and we read the SQLite file in exactly one place per metric.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from job_monitor.analytics import AnalyticsService, JobExporter
from job_monitor.config import Settings, get_settings
from job_monitor.database import Database, HealthRepository, JobRepository
from job_monitor.models import JobRecord

_CACHE_TTL = 30  # seconds
_PLOTLY_TEMPLATE = "plotly_white"
_COLORWAY = px.colors.qualitative.Vivid


@dataclass
class DashboardContext:
    settings: Settings
    db_path: str


def get_context() -> DashboardContext:
    settings = get_settings()
    settings.ensure_directories()
    Database(settings.database_path).initialize()
    return DashboardContext(settings=settings, db_path=str(settings.database_path))


# --------------------------------------------------------------------------- cached reads
@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_overview(db_path: str) -> Dict[str, object]:
    return AnalyticsService(Database(db_path)).overview()


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_jobs_df(db_path: str) -> pd.DataFrame:
    jobs = JobRepository(Database(db_path)).all_jobs()
    return JobExporter(jobs).to_dataframe()


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_by_source(db_path: str) -> Dict[str, int]:
    return AnalyticsService(Database(db_path)).by_source()


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_by_category(db_path: str) -> Dict[str, int]:
    return AnalyticsService(Database(db_path)).by_category()


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_jobs_per_day(db_path: str, days: int = 30) -> Dict[str, int]:
    return AnalyticsService(Database(db_path)).jobs_per_day(days=days)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_skill_frequency(db_path: str, top: int = 15) -> List[Tuple[str, int]]:
    return AnalyticsService(Database(db_path)).skill_frequency(top=top)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_score_distribution(db_path: str) -> Dict[str, int]:
    return AnalyticsService(Database(db_path)).score_distribution()


def load_jobs(db_path: str) -> List[JobRecord]:
    """Uncached: full job objects (used by the explorer/export for live filtering)."""
    return JobRepository(Database(db_path)).all_jobs()


def load_health(db_path: str):
    return HealthRepository(Database(db_path)).all()


# --------------------------------------------------------------------------- chart helpers
def _style(fig):
    fig.update_layout(
        template=_PLOTLY_TEMPLATE,
        margin=dict(l=10, r=10, t=40, b=10),
        colorway=_COLORWAY,
        height=360,
    )
    return fig


def bar_from_mapping(mapping: Dict[str, int], *, title: str, x_label: str, y_label: str,
                     horizontal: bool = False):
    if not mapping:
        return None
    df = pd.DataFrame({x_label: list(mapping.keys()), y_label: list(mapping.values())})
    if horizontal:
        df = df.sort_values(y_label)
        fig = px.bar(df, x=y_label, y=x_label, orientation="h", title=title, text=y_label)
    else:
        fig = px.bar(df, x=x_label, y=y_label, title=title, text=y_label)
    fig.update_traces(textposition="outside")
    return _style(fig)


def pie_from_mapping(mapping: Dict[str, int], *, title: str):
    if not mapping:
        return None
    df = pd.DataFrame({"label": list(mapping.keys()), "value": list(mapping.values())})
    fig = px.pie(df, names="label", values="value", title=title, hole=0.45)
    return _style(fig)


def line_from_mapping(mapping: Dict[str, int], *, title: str, x_label: str, y_label: str):
    if not mapping:
        return None
    df = pd.DataFrame({x_label: list(mapping.keys()), y_label: list(mapping.values())})
    fig = px.area(df, x=x_label, y=y_label, title=title, markers=True)
    return _style(fig)


def empty_state(message: str = "No data yet.") -> None:
    """Friendly placeholder shown when the database is empty."""
    st.info(
        f"{message}\n\nSeed demo data with `python generate_demo_data.py` "
        "or run a live scrape with `python main.py --once`."
    )
