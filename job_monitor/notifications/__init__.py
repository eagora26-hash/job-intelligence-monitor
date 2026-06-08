"""Notification layer: a Notifier interface with Telegram and Null implementations."""

from job_monitor.notifications.base import NullNotifier, Notifier
from job_monitor.notifications.telegram import TelegramNotifier, build_notifier

__all__ = ["Notifier", "NullNotifier", "TelegramNotifier", "build_notifier"]
