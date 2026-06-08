#!/usr/bin/env python3
"""Command-line entrypoint for the Multi-Source AI Job Intelligence Monitor.

Examples
--------
    python main.py --once          # run a single scrape→store→notify cycle
    python main.py --loop          # run forever on the configured polling interval
    python main.py --demo          # seed the database with realistic demo data
    python main.py --status        # print current state + per-source health
"""

from __future__ import annotations

import argparse
import sys

from job_monitor.config import get_settings
from job_monitor.observability import configure_logging, get_logger


def _cmd_once() -> int:
    from job_monitor.pipeline.runner import PipelineRunner

    report = PipelineRunner().run_once()
    print(report.summary_line())
    for info in report.sources:
        status = "ok " if info.success else "ERR"
        detail = info.error if not info.success else (
            f"scraped={info.scraped} new={info.new} updated={info.updated}"
        )
        print(f"  [{status}] {info.source:16s} {detail}")
    return 0


def _cmd_loop() -> int:
    from job_monitor.scheduler import run_scheduler

    run_scheduler()
    return 0


def _cmd_demo(count: int) -> int:
    from job_monitor.services.demo import generate_demo_data

    created = generate_demo_data(count=count)
    print(f"Seeded {created} demo jobs.")
    return 0


def _cmd_status() -> int:
    from job_monitor.database import Database, HealthRepository, JobRepository
    from job_monitor.services.state import StateStore

    settings = get_settings()
    db = Database(settings.database_path)
    db.initialize()
    jobs = JobRepository(db)
    health = HealthRepository(db)
    state = StateStore(settings.state_file).load()

    print("=== Job Monitor status ===")
    print(f"Total jobs:        {jobs.count()}")
    print(f"Jobs today:        {jobs.count_today()}")
    print(f"Last run:          {state.last_run}")
    print(f"Last success:      {state.last_successful_run}")
    print(f"Total runs:        {state.total_runs}")
    print("By source:")
    for source, n in jobs.count_by_source().items():
        print(f"  {source:16s} {n}")
    print("Source health:")
    for h in health.all():
        print(f"  {h.source:16s} {h.status:9s} ok={h.success_count} fail={h.failure_count}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="job-monitor",
        description="Multi-Source AI Job Intelligence Monitor",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="Run a single scrape cycle.")
    group.add_argument("--loop", action="store_true", help="Run continuously on a schedule.")
    group.add_argument("--demo", action="store_true", help="Seed the DB with demo data.")
    group.add_argument("--status", action="store_true", help="Print current status + health.")
    parser.add_argument("--count", type=int, default=120, help="Demo job count (with --demo).")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    configure_logging(level=settings.log_level, log_dir=settings.log_dir)
    get_logger("main").info("CLI invoked")

    if args.once:
        return _cmd_once()
    if args.loop:
        return _cmd_loop()
    if args.demo:
        return _cmd_demo(args.count)
    if args.status:
        return _cmd_status()
    return 1


if __name__ == "__main__":
    sys.exit(main())
