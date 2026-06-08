#!/usr/bin/env python3
"""Seed the database with realistic demo data for dashboard demonstrations.

Usage:
    python generate_demo_data.py            # 120 demo jobs
    python generate_demo_data.py --count 250
"""

from __future__ import annotations

import argparse
import sys

from job_monitor.config import get_settings
from job_monitor.observability import configure_logging
from job_monitor.services.demo import generate_demo_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed demo job data.")
    parser.add_argument("--count", type=int, default=120, help="Number of demo jobs to create.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = parser.parse_args(argv)

    settings = get_settings()
    configure_logging(level=settings.log_level, log_dir=settings.log_dir)
    created = generate_demo_data(count=args.count, settings=settings, seed=args.seed)
    print(f"✅ Seeded {created} demo jobs into {settings.database_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
