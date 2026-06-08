"""Canonical source presentation metadata (labels + homepages).

Single source of truth for turning an internal source key (e.g. ``"weworkremotely"``) into a
human label (``"We Work Remotely"``) for the UI and notifications.
"""

from __future__ import annotations

SOURCE_LABELS: dict[str, str] = {
    "remoteok": "RemoteOK",
    "weworkremotely": "We Work Remotely",
    "freelancer": "Freelancer",
    "fiverr": "Fiverr",
    "wellfound": "Wellfound",
}

SOURCE_URLS: dict[str, str] = {
    "remoteok": "https://remoteok.com",
    "weworkremotely": "https://weworkremotely.com",
    "freelancer": "https://www.freelancer.com",
    "fiverr": "https://www.fiverr.com",
    "wellfound": "https://wellfound.com",
}


def source_label(key: str) -> str:
    """Human-friendly label for a source key (falls back to a title-cased key)."""
    return SOURCE_LABELS.get(key, key.replace("_", " ").title())
