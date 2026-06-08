"""Blocking scheduler that runs the pipeline on a fixed interval with graceful shutdown.

Uses APScheduler's ``BlockingScheduler``. ``SIGINT``/``SIGTERM`` are handled so an in-flight
run is allowed to finish before the process exits (important for Docker ``docker compose down``).
"""

from __future__ import annotations

import signal
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler

from job_monitor.config import Settings, get_settings
from job_monitor.observability import configure_logging, get_logger
from job_monitor.pipeline.runner import PipelineRunner

logger = get_logger("scheduler")


class MonitorScheduler:
    """Runs :meth:`PipelineRunner.run_once` immediately, then every ``polling_interval`` seconds."""

    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        runner: Optional[PipelineRunner] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.runner = runner or PipelineRunner(settings=self.settings)
        self._scheduler = BlockingScheduler(timezone="UTC")

    def _job(self) -> None:
        try:
            self.runner.run_once()
        except Exception as exc:  # noqa: BLE001 - never let a run crash the scheduler loop
            logger.exception("Run failed: %s", exc)

    def start(self) -> None:
        interval = max(60, self.settings.polling_interval)
        logger.info("Scheduler starting; interval = %d s", interval)
        self.runner.notifier.notify_startup(
            f"Polling every {interval}s across {len(self.runner.scrapers)} source(s)."
        )

        self._job()  # run once immediately on startup
        self._scheduler.add_job(self._job, "interval", seconds=interval, max_instances=1)

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, lambda *_: self.stop())
            except ValueError:
                pass  # not in main thread (e.g. under some test runners)

        try:
            self._scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stop()

    def stop(self) -> None:
        if self._scheduler.running:
            logger.info("Scheduler shutting down gracefully...")
            self._scheduler.shutdown(wait=True)


def run_scheduler(settings: Optional[Settings] = None) -> None:
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, log_dir=settings.log_dir)
    MonitorScheduler(settings=settings).start()
