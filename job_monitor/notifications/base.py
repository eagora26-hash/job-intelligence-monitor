"""Notifier abstraction so the alerting channel is swappable (Telegram today, Slack/email later)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Mapping

from job_monitor.models import JobRecord
from job_monitor.observability import get_logger

logger = get_logger("notifications")


class Notifier(ABC):
    """Interface every notification channel implements."""

    @abstractmethod
    def send(self, text: str) -> bool:
        """Send a single freeform message. Returns success."""

    @abstractmethod
    def notify_new_jobs(self, jobs: List[JobRecord]) -> int:
        """Send alerts for newly-discovered jobs. Returns count successfully sent."""

    @abstractmethod
    def notify_daily_summary(self, summary: Mapping[str, object]) -> bool:
        """Send a daily digest built from analytics metrics."""

    def notify_startup(self, message: str = "") -> bool:
        return self.send(f"✅ <b>Job Monitor started</b>\n{message}".strip())

    def notify_error(self, message: str) -> bool:
        return self.send(f"⚠️ <b>Job Monitor error</b>\n{message}")


class NullNotifier(Notifier):
    """No-op notifier used when notifications are disabled or unconfigured.

    Keeps call sites simple — they never branch on "is notification enabled"; they always
    call the notifier and this implementation simply does nothing (and logs at debug level).
    """

    def send(self, text: str) -> bool:
        logger.debug("NullNotifier.send (suppressed): %s", text[:80])
        return True

    def notify_new_jobs(self, jobs: List[JobRecord]) -> int:
        logger.debug("NullNotifier.notify_new_jobs (suppressed): %d jobs", len(jobs))
        return 0

    def notify_daily_summary(self, summary: Mapping[str, object]) -> bool:
        return True
