-- Multi-Source AI Job Intelligence Monitor — SQLite schema.
-- Applied idempotently on startup by job_monitor.database.connection.Database.initialize().

-- Canonical job postings. `url` is the natural unique key used for deduplication.
CREATE TABLE IF NOT EXISTS jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT    NOT NULL,
    title         TEXT    NOT NULL DEFAULT '',
    company       TEXT    NOT NULL DEFAULT '',
    url           TEXT    NOT NULL UNIQUE,
    description   TEXT    NOT NULL DEFAULT '',
    posted_at     TEXT,                         -- ISO-8601 or NULL
    location      TEXT    NOT NULL DEFAULT '',
    salary        TEXT    NOT NULL DEFAULT '',
    tags          TEXT    NOT NULL DEFAULT '[]',-- JSON array
    score         INTEGER NOT NULL DEFAULT 0,
    category      TEXT    NOT NULL DEFAULT '',
    skills        TEXT    NOT NULL DEFAULT '[]',-- JSON array
    quality_score INTEGER NOT NULL DEFAULT 0,
    remote        INTEGER NOT NULL DEFAULT 0,   -- 0/1
    content_hash  TEXT    NOT NULL DEFAULT '',
    first_seen    TEXT    NOT NULL,             -- ISO-8601
    last_seen     TEXT    NOT NULL,             -- ISO-8601
    notified      INTEGER NOT NULL DEFAULT 0    -- 0/1
);

CREATE INDEX IF NOT EXISTS idx_jobs_source     ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_score      ON jobs(score);
CREATE INDEX IF NOT EXISTS idx_jobs_category   ON jobs(category);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen);
CREATE INDEX IF NOT EXISTS idx_jobs_notified   ON jobs(notified);

-- Audit trail of field-level changes detected on re-scrape (change detection).
CREATE TABLE IF NOT EXISTS job_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_url     TEXT NOT NULL,
    field       TEXT NOT NULL,
    old_value   TEXT NOT NULL DEFAULT '',
    new_value   TEXT NOT NULL DEFAULT '',
    detected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_url ON job_history(job_url);

-- Rolling per-source scraper health.
CREATE TABLE IF NOT EXISTS source_health (
    source          TEXT PRIMARY KEY,
    success_count   INTEGER NOT NULL DEFAULT 0,
    failure_count   INTEGER NOT NULL DEFAULT 0,
    last_success    TEXT,
    last_failure    TEXT,
    last_error      TEXT NOT NULL DEFAULT '',
    avg_response_ms REAL NOT NULL DEFAULT 0,
    last_jobs_found INTEGER NOT NULL DEFAULT 0
);

-- Once-per-day headline metric rollups for historical trend analytics.
CREATE TABLE IF NOT EXISTS daily_snapshots (
    snapshot_date  TEXT PRIMARY KEY,           -- ISO date (YYYY-MM-DD)
    total_jobs     INTEGER NOT NULL DEFAULT 0,
    new_jobs       INTEGER NOT NULL DEFAULT 0,
    source_count   INTEGER NOT NULL DEFAULT 0,
    keyword_count  INTEGER NOT NULL DEFAULT 0,
    notified_count INTEGER NOT NULL DEFAULT 0,
    avg_score      REAL NOT NULL DEFAULT 0
);
