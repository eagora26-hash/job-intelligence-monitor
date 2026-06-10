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
from job_monitor.notifications.base import NullNotifier

_CACHE_TTL = 30  # seconds
# Sources that work over plain HTTP (no browser). Used for the dashboard's live-scrape so it
# stays fast and reliable on Streamlit Cloud; Fiverr/Wellfound need the browser/stealth path.
_RELIABLE_SOURCES = ("remoteok", "weworkremotely", "freelancer")
_PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#6C8CFF"
_COLORWAY = ["#6C8CFF", "#4FD1C5", "#F6AD55", "#FC8181", "#B794F4", "#68D391", "#F687B3"]

SOURCE_LABELS = {
    "remoteok": "RemoteOK",
    "weworkremotely": "We Work Remotely",
    "freelancer": "Freelancer",
    "fiverr": "Fiverr",
    "wellfound": "Wellfound",
}

_CSS = """
<style>
/* ---- layout & typography ------------------------------------------------ */
.block-container { padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1300px; }
h1, h2, h3 { letter-spacing: -0.02em; }
#MainMenu, footer { visibility: hidden; }

/* ---- KPI metric cards ---------------------------------------------------- */
div[data-testid="stMetric"] {
  background: linear-gradient(160deg, #1A2336 0%, #141B2B 100%);
  border: 1px solid #27314A;
  border-radius: 14px;
  padding: 14px 18px 12px 18px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.25);
}
div[data-testid="stMetric"] label { color: #9AA6C3 !important; font-size: 0.78rem;
  text-transform: uppercase; letter-spacing: 0.06em; }
div[data-testid="stMetricValue"] { font-size: 1.7rem; font-weight: 700; }
div[data-testid="stMetricDelta"] { font-size: 0.85rem; }

/* ---- section headers ------------------------------------------------------ */
.jm-section { margin: 1.6rem 0 0.4rem 0; display: flex; align-items: baseline; gap: 0.6rem; }
.jm-section h3 { margin: 0; font-size: 1.12rem; }
.jm-section span { color: #8A96B5; font-size: 0.85rem; }
.jm-rule { border: none; border-top: 1px solid #27314A; margin: 0.35rem 0 1rem 0; }

/* ---- hero banner ----------------------------------------------------------- */
.jm-hero { padding: 6px 2px 2px 2px; }
.jm-hero h1 { font-size: 1.65rem; margin: 0; }
.jm-hero p { color: #8A96B5; margin: 2px 0 0 0; font-size: 0.95rem; }
.jm-chip { display: inline-block; background: #1D2A45; color: #A9BBFF;
  border: 1px solid #31416A; border-radius: 999px; padding: 2px 12px;
  font-size: 0.75rem; margin-right: 6px; }

/* ---- tables ---------------------------------------------------------------- */
div[data-testid="stDataFrame"] { border: 1px solid #27314A; border-radius: 12px; }

/* ---- sidebar ---------------------------------------------------------------- */
section[data-testid="stSidebar"] { border-right: 1px solid #222C44; }
section[data-testid="stSidebar"] .stRadio label p { font-size: 0.95rem; }
</style>
"""


def inject_css() -> None:
    """Inject the SaaS design system once per rerun (cheap, idempotent)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def section(title: str, caption: str = "") -> None:
    """Consistent section header with optional explainer caption."""
    cap = f"<span>{caption}</span>" if caption else ""
    st.markdown(f'<div class="jm-section"><h3>{title}</h3>{cap}</div><hr class="jm-rule">',
                unsafe_allow_html=True)


def hero(title: str, subtitle: str, chips: List[str]) -> None:
    """Page hero: product title, one-line value statement, status chips."""
    chip_html = "".join(f'<span class="jm-chip">{c}</span>' for c in chips)
    st.markdown(
        f'<div class="jm-hero"><h1>{title}</h1><p>{subtitle}</p>'
        f'<div style="margin-top:8px">{chip_html}</div></div>',
        unsafe_allow_html=True,
    )


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


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_intelligence(db_path: str) -> Dict[str, object]:
    """One cached bundle for the executive page: 24h volume, leaders, health score."""
    svc = AnalyticsService(Database(db_path))
    active, top_count = svc.most_active_source()
    return {
        "new_last_24h": svc.new_last_24h(),
        "most_active_source": SOURCE_LABELS.get(active, active),
        "most_active_count": top_count,
        "health_score": svc.health_score(),
    }


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_weekly_trend(db_path: str, weeks: int = 8) -> Dict[str, int]:
    return AnalyticsService(Database(db_path)).weekly_trend(weeks=weeks)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_skill_matrix(db_path: str, top: int = 12) -> Dict[str, Dict[str, int]]:
    return AnalyticsService(Database(db_path)).skill_source_matrix(top=top)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_source_stats(db_path: str) -> List[Dict[str, object]]:
    return AnalyticsService(Database(db_path)).source_stats()


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def load_reliability(db_path: str) -> List[Dict[str, object]]:
    return AnalyticsService(Database(db_path)).reliability_leaderboard()


def load_jobs(db_path: str) -> List[JobRecord]:
    """Uncached: full job objects (used by the explorer/export for live filtering)."""
    return JobRepository(Database(db_path)).all_jobs()


def load_health(db_path: str):
    return HealthRepository(Database(db_path)).all()


# --------------------------------------------------------------------------- live scraping
def run_live_scrape(db_path: str) -> dict:
    """Run a bounded live scrape (reliable HTTP sources only) into ``db_path``.

    Telegram is intentionally suppressed here (``NullNotifier``) — the dashboard refreshes data;
    notifications are the scheduled job's responsibility. Returns a small summary dict.
    """
    from job_monitor.pipeline.runner import PipelineRunner
    from job_monitor.scrapers.http import HttpClient
    from job_monitor.scrapers.registry import SCRAPER_CLASSES

    settings = get_settings()
    fast = HttpClient(timeout=10, retries=1)
    scrapers = [SCRAPER_CLASSES[n](http=fast) for n in _RELIABLE_SOURCES if n in SCRAPER_CLASSES]
    runner = PipelineRunner(
        settings=settings, database=Database(db_path), scrapers=scrapers, notifier=NullNotifier()
    )
    report = runner.run_once()
    return {"new": report.total_new, "scraped": report.total_scraped}


@st.cache_data(show_spinner="Loading job data…")
def ensure_data(db_path: str) -> dict:
    """Guarantee the dashboard has data on first load.

    If the database is empty (e.g. a fresh Streamlit Cloud deploy) this performs a one-off live
    scrape; if that yields nothing (sources blocked / offline) it falls back to demo data so the
    dashboard is never blank. Cached, so it runs once per process. Returns the data ``mode``.
    """
    repo = JobRepository(Database(db_path))
    if repo.count() > 0:
        return {"mode": "existing", "count": repo.count()}

    try:
        run_live_scrape(db_path)
    except Exception:  # noqa: BLE001 - never let data-bootstrap crash the dashboard
        pass
    if repo.count() > 0:
        return {"mode": "live", "count": repo.count()}

    try:  # last-resort fallback so the dashboard always shows something
        from job_monitor.services.demo import generate_demo_data

        generate_demo_data(count=120, settings=get_settings(), seed=42)
    except Exception:  # noqa: BLE001
        pass
    return {"mode": "demo", "count": JobRepository(Database(db_path)).count()}


# --------------------------------------------------------------------------- chart helpers
def _style(fig, height: int = 340):
    fig.update_layout(
        template=_PLOTLY_TEMPLATE,
        margin=dict(l=10, r=10, t=42, b=10),
        colorway=_COLORWAY,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(22,29,46,0.55)",
        font=dict(color="#C7D0E4", size=12),
        title_font=dict(size=14, color="#E8ECF6"),
        xaxis=dict(gridcolor="#222C44", zerolinecolor="#222C44"),
        yaxis=dict(gridcolor="#222C44", zerolinecolor="#222C44"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
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


def heatmap_from_matrix(matrix: Dict[str, Dict[str, int]], *, title: str):
    """Skill × source demand heatmap."""
    if not matrix:
        return None
    sources = sorted({s for row in matrix.values() for s in row})
    skills = list(matrix.keys())
    z = [[matrix[skill].get(src, 0) for src in sources] for skill in skills]
    fig = px.imshow(
        z,
        x=[SOURCE_LABELS.get(s, s) for s in sources],
        y=skills,
        title=title,
        color_continuous_scale=["#161D2E", "#31416A", "#6C8CFF", "#A9BBFF"],
        text_auto=True,
        aspect="auto",
    )
    fig.update_coloraxes(showscale=False)
    return _style(fig, height=max(340, 30 * len(skills) + 90))


def grouped_bar(df: pd.DataFrame, *, x: str, ys: List[str], title: str):
    """Multi-metric comparison bars (e.g. per-source volume vs score vs quality)."""
    if df.empty:
        return None
    melted = df.melt(id_vars=[x], value_vars=ys, var_name="metric", value_name="value")
    fig = px.bar(melted, x=x, y="value", color="metric", barmode="group", title=title,
                 text="value")
    fig.update_traces(textposition="outside")
    return _style(fig)


def empty_state(message: str = "No data yet.") -> None:
    """Friendly placeholder shown when the database is empty."""
    st.info(
        f"{message}\n\nSeed demo data with `python generate_demo_data.py` "
        "or run a live scrape with `python main.py --once`."
    )
