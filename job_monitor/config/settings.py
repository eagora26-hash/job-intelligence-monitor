"""Application settings, loaded from environment / ``.env`` via pydantic-settings.

All runtime configuration flows through :class:`Settings`. Nothing else in the codebase
should read ``os.environ`` directly — inject a ``Settings`` instance instead. Secrets are
never hardcoded; they come from a gitignored ``.env`` file (see ``.env.example``).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Project root = two levels up from this file (job_monitor/config/settings.py -> repo root).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Typed, validated application configuration.

    Values resolve in this precedence order: real environment variables > ``.env`` file >
    the defaults declared below. Path-like settings are resolved relative to the project
    root so the app behaves identically regardless of the current working directory.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram / notifications ---
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    notify_enabled: bool = Field(default=True, alias="NOTIFY_ENABLED")
    notify_min_score: int = Field(default=10, alias="NOTIFY_MIN_SCORE")

    # --- Scheduling ---
    polling_interval: int = Field(default=3600, alias="POLLING_INTERVAL")

    # --- Source toggles ---
    enable_remoteok: bool = Field(default=True, alias="ENABLE_REMOTEOK")
    enable_wwr: bool = Field(default=True, alias="ENABLE_WWR")
    enable_freelancer: bool = Field(default=True, alias="ENABLE_FREELANCER")
    enable_fiverr: bool = Field(default=True, alias="ENABLE_FIVERR")
    enable_wellfound: bool = Field(default=True, alias="ENABLE_WELLFOUND")

    # --- Acquisition tuning ---
    max_workers: int = Field(default=5, alias="MAX_WORKERS")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")
    request_retries: int = Field(default=3, alias="REQUEST_RETRIES")
    http_impersonate: str = Field(default="chrome", alias="HTTP_IMPERSONATE")
    use_stealth_fallback: bool = Field(default=False, alias="USE_STEALTH_FALLBACK")

    # --- Storage & paths (relative to PROJECT_ROOT unless absolute) ---
    database_path: Path = Field(default=Path("database/jobs.db"), alias="DATABASE_PATH")
    archive_db_path: Path = Field(default=Path("database/archive.db"), alias="ARCHIVE_DB_PATH")
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    log_dir: Path = Field(default=Path("logs"), alias="LOG_DIR")
    backup_dir: Path = Field(default=Path("backup"), alias="BACKUP_DIR")
    export_dir: Path = Field(default=Path("exports"), alias="EXPORT_DIR")

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Optional filter overrides (comma-separated in env) ---
    # NoDecode disables pydantic-settings' JSON decoding so the CSV validator below runs.
    include_keywords: Annotated[List[str], NoDecode] = Field(
        default_factory=list, alias="INCLUDE_KEYWORDS"
    )
    exclude_keywords: Annotated[List[str], NoDecode] = Field(
        default_factory=list, alias="EXCLUDE_KEYWORDS"
    )

    # ----------------------------------------------------------------- validators
    @field_validator("include_keywords", "exclude_keywords", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow comma-separated strings for list-valued env vars."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "database_path", "archive_db_path", "data_dir", "log_dir", "backup_dir", "export_dir",
        mode="after",
    )
    @classmethod
    def _resolve_path(cls, value: Path) -> Path:
        """Resolve relative paths against the project root for CWD-independence."""
        return value if value.is_absolute() else (PROJECT_ROOT / value)

    # ----------------------------------------------------------------- helpers
    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def state_file(self) -> Path:
        return self.data_dir / "state.json"

    def enabled_sources(self) -> dict[str, bool]:
        """Map canonical source key -> enabled flag (used by the scraper registry)."""
        return {
            "remoteok": self.enable_remoteok,
            "weworkremotely": self.enable_wwr,
            "freelancer": self.enable_freelancer,
            "fiverr": self.enable_fiverr,
            "wellfound": self.enable_wellfound,
        }

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    def ensure_directories(self) -> None:
        """Create all runtime directories the app writes to (idempotent)."""
        for path in (
            self.database_path.parent,
            self.archive_db_path.parent,
            self.data_dir,
            self.log_dir,
            self.backup_dir,
            self.export_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance.

    Cached so configuration is parsed once. Tests can clear the cache via
    ``get_settings.cache_clear()`` after mutating the environment.
    """
    return Settings()
