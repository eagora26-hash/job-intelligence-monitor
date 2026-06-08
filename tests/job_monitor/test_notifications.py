"""Tests for notification formatting and the Telegram notifier (httpx mocked)."""

from __future__ import annotations

import pytest

from job_monitor.config.settings import Settings
from job_monitor.models import JobRecord
from job_monitor.notifications import NullNotifier, TelegramNotifier, build_notifier
from job_monitor.notifications.formatters import format_daily_summary, format_job


def _job(**kw) -> JobRecord:
    base = dict(source="remoteok", url="https://remoteok.com/jobs/1",
                title="Python Automation Engineer", company="Acme",
                tags=["python", "automation"], score=30, category="Automation")
    base.update(kw)
    return JobRecord(**base)


def test_format_job_matches_spec_layout():
    msg = format_job(_job())
    assert "🚀 <b>NEW JOB</b>" in msg
    assert "<b>Title:</b> Python Automation Engineer" in msg
    assert "<b>Company:</b> Acme" in msg
    assert "<b>Source:</b> RemoteOK" in msg          # human label, not the key
    assert "<b>Link:</b> https://remoteok.com/jobs/1" in msg
    assert "python, automation" in msg


def test_format_job_escapes_html():
    msg = format_job(_job(title="Dev <script> & co"))
    assert "&lt;script&gt;" in msg and "&amp;" in msg


def test_format_daily_summary():
    summary = {"total_jobs": 100, "jobs_today": 5, "by_source": {"remoteok": 60},
               "top_skills": [("Python", 40), ("Docker", 10)]}
    msg = format_daily_summary(summary)
    assert "Daily Job Intelligence Summary" in msg
    assert "100" in msg and "remoteok" in msg and "Python" in msg


def test_build_notifier_returns_null_when_unconfigured():
    settings = Settings(_env_file=None, TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    assert isinstance(build_notifier(settings), NullNotifier)


def test_build_notifier_returns_telegram_when_configured():
    settings = Settings(_env_file=None, TELEGRAM_BOT_TOKEN="tok", TELEGRAM_CHAT_ID="123",
                        NOTIFY_ENABLED=True)
    assert isinstance(build_notifier(settings), TelegramNotifier)


def test_telegram_sends_messages(monkeypatch):
    sent = []

    class _Resp:
        status_code = 200
        text = "ok"

    def _fake_post(url, json, timeout):
        sent.append(json)
        return _Resp()

    monkeypatch.setattr("job_monitor.notifications.telegram.httpx.post", _fake_post)
    notifier = TelegramNotifier("tok", "chat", max_alerts_per_run=5)
    count = notifier.notify_new_jobs([_job(url="u1"), _job(url="u2")])

    assert count == 2
    assert len(sent) == 2
    assert sent[0]["chat_id"] == "chat"
    assert sent[0]["parse_mode"] == "HTML"


def test_telegram_caps_alerts_and_summarizes(monkeypatch):
    sent = []
    monkeypatch.setattr(
        "job_monitor.notifications.telegram.httpx.post",
        lambda url, json, timeout: sent.append(json) or type("R", (), {"status_code": 200, "text": ""})(),
    )
    notifier = TelegramNotifier("tok", "chat", max_alerts_per_run=2)
    jobs = [_job(url=f"u{i}") for i in range(5)]
    notifier.notify_new_jobs(jobs)
    # 2 individual alerts + 1 "N more" summary message.
    assert len(sent) == 3
    assert "more new jobs" in sent[-1]["text"]
