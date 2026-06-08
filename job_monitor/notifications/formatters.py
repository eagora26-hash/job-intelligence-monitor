"""HTML message formatters for Telegram notifications (parse_mode=HTML)."""

from __future__ import annotations

from html import escape
from typing import Mapping

from job_monitor.config.sources import source_label
from job_monitor.models import JobRecord


def _esc(value: object) -> str:
    return escape(str(value or ""))


def format_job(job: JobRecord) -> str:
    """Render a single new-job alert in the format from instructions.md (+ score/category)."""
    lines = [
        "🚀 <b>NEW JOB</b>",
        "",
        f"<b>Title:</b> {_esc(job.title)}",
    ]
    if job.company:
        lines.append(f"<b>Company:</b> {_esc(job.company)}")
    lines.append(f"<b>Source:</b> {_esc(source_label(job.source))}")
    if job.location:
        lines.append(f"<b>Location:</b> {_esc(job.location)}")
    if job.salary:
        lines.append(f"<b>Salary:</b> {_esc(job.salary)}")
    if job.category:
        lines.append(f"<b>Category:</b> {_esc(job.category)}")
    lines.append(f"<b>Score:</b> {job.score}")
    if job.tags:
        lines.append(f"<b>Tags:</b> {_esc(', '.join(job.tags[:8]))}")
    lines.append("")
    lines.append(f"<b>Link:</b> {_esc(job.url)}")
    return "\n".join(lines)


def format_daily_summary(summary: Mapping[str, object]) -> str:
    """Render the daily digest from an analytics summary mapping."""
    lines = ["📊 <b>Daily Job Intelligence Summary</b>", ""]
    lines.append(f"<b>Total jobs tracked:</b> {summary.get('total_jobs', 0)}")
    lines.append(f"<b>New today:</b> {summary.get('jobs_today', 0)}")
    by_source = summary.get("by_source") or {}
    if isinstance(by_source, Mapping) and by_source:
        lines.append("")
        lines.append("<b>By source:</b>")
        for source, count in by_source.items():
            lines.append(f"  • {_esc(source)}: {count}")
    top_skills = summary.get("top_skills") or []
    if isinstance(top_skills, list) and top_skills:
        names = ", ".join(str(s[0]) if isinstance(s, (list, tuple)) else str(s) for s in top_skills[:8])
        lines.append("")
        lines.append(f"<b>Top skills:</b> {_esc(names)}")
    return "\n".join(lines)
