"""Dashboard view modules. Each exposes ``render(ctx: DashboardContext) -> None``."""

from job_monitor.dashboard.views import (
    analytics,
    config,
    explorer,
    health,
    overview,
    showcase,
    system,
)

__all__ = ["overview", "analytics", "explorer", "health", "config", "showcase", "system"]
