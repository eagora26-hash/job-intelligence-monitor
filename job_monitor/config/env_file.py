"""Safe ``.env`` updates for the dashboard configuration page.

Updates or appends ``KEY=value`` lines while preserving existing comments/ordering. Secret
keys are refused by default so the UI can never accidentally rewrite or expose the bot token.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

# Keys the configuration UI is allowed to write (never secrets).
WRITABLE_KEYS = {
    "NOTIFY_ENABLED", "NOTIFY_MIN_SCORE", "POLLING_INTERVAL",
    "ENABLE_REMOTEOK", "ENABLE_WWR", "ENABLE_FREELANCER", "ENABLE_FIVERR", "ENABLE_WELLFOUND",
    "MAX_WORKERS", "REQUEST_TIMEOUT", "INCLUDE_KEYWORDS", "EXCLUDE_KEYWORDS", "LOG_LEVEL",
}

_SECRET_KEYS = {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}


def update_env_file(path: Path | str, updates: Mapping[str, str]) -> None:
    """Apply ``updates`` to the ``.env`` file at ``path`` (create if missing).

    Raises ``ValueError`` if a secret or non-whitelisted key is supplied.
    """
    path = Path(path)
    for key in updates:
        if key in _SECRET_KEYS:
            raise ValueError(f"Refusing to write secret key '{key}' from the UI.")
        if key not in WRITABLE_KEYS:
            raise ValueError(f"Key '{key}' is not user-writable.")

    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    remaining = dict(updates)

    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in remaining:
                out.append(f"{key}={remaining.pop(key)}")
                continue
        out.append(line)

    for key, value in remaining.items():  # append any keys not already present
        out.append(f"{key}={value}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
