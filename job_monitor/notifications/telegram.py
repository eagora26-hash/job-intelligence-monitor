"""Telegram notifier implementation (Bot API via httpx).

Sends new-job alerts, daily summaries, and startup/error messages. Failures are swallowed and
logged so a notification outage never breaks a scrape run. Secrets come from
:class:`~job_monitor.config.Settings` (never hardcoded).
"""

from __future__ import annotations

import time
from typing import List, Mapping, Optional

import httpx

from job_monitor.config import Settings, get_settings
from job_monitor.models import JobRecord
from job_monitor.notifications.base import NullNotifier, Notifier
from job_monitor.notifications.formatters import format_daily_summary, format_job
from job_monitor.observability import get_logger

logger = get_logger("notifications.telegram")

_API_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotifier(Notifier):
    """Sends messages to a Telegram chat via the Bot API."""

    def __init__(
        self,
        token: str,
        chat_id: str,
        *,
        max_alerts_per_run: int = 15,
        timeout: int = 15,
    ) -> None:
        self._token = token
        self._chat_id = chat_id
        self._max_alerts = max_alerts_per_run
        self._timeout = timeout

    def send(self, text: str) -> bool:
        url = _API_TEMPLATE.format(token=self._token)
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            response = httpx.post(url, json=payload, timeout=self._timeout)
            if response.status_code != 200:
                logger.warning("Telegram send failed (%s): %s", response.status_code, response.text[:200])
                return False
            return True
        except httpx.HTTPError as exc:
            logger.warning("Telegram send error: %s", exc)
            return False

    def notify_new_jobs(self, jobs: List[JobRecord]) -> int:
        if not jobs:
            return 0
        sent = 0
        for job in jobs[: self._max_alerts]:
            if self.send(format_job(job)):
                sent += 1
            time.sleep(0.05)  # stay well under Telegram's rate limit
        remaining = len(jobs) - self._max_alerts
        if remaining > 0:
            self.send(f"➕ <b>{remaining} more new jobs</b> were found. Open the dashboard for the full list.")
        return sent

    def notify_daily_summary(self, summary: Mapping[str, object]) -> bool:
        return self.send(format_daily_summary(summary))


def build_notifier(settings: Optional[Settings] = None) -> Notifier:
    """Factory: a real :class:`TelegramNotifier` when configured+enabled, else a no-op.

    Call sites depend only on the :class:`Notifier` interface and never branch on config.
    """
    settings = settings or get_settings()
    if settings.notify_enabled and settings.telegram_configured:
        logger.info("Telegram notifications enabled.")
        return TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    logger.info("Telegram notifications disabled or unconfigured; using NullNotifier.")
    return NullNotifier()
