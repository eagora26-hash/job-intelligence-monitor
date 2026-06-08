"""Internal REST API (FastAPI).

A real, runnable read-API over the monitor's data — the seam for a future mobile dashboard or
external integrations. FastAPI is an optional dependency; importing this subpackage is guarded
so the core app/runtime never requires it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from job_monitor.api.app import create_app

__all__ = ["create_app"]


def __getattr__(name: str):  # lazy import so `import job_monitor.api` doesn't require fastapi
    if name == "create_app":
        from job_monitor.api.app import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
