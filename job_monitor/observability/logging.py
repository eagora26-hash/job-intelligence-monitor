"""Centralized logging configuration: console + rotating file handlers.

Call :func:`configure_logging` once at process startup (CLI, scheduler, dashboard). Every
module obtains its logger via :func:`get_logger` so logs are consistent and namespaced.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_CONFIGURED = False
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
ROOT_LOGGER_NAME = "job_monitor"


def configure_logging(
    *,
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configure the ``job_monitor`` logger tree (idempotent).

    Adds a console handler and, when ``log_dir`` is given, a rotating file handler writing
    to ``<log_dir>/job_monitor.log``. Safe to call multiple times — only configures once.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "job_monitor.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced child logger (``job_monitor.<name>``)."""
    safe = name.replace("job_monitor.", "")
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{safe}")
