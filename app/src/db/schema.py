SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          TEXT PRIMARY KEY,
    query       TEXT        NOT NULL,
    word_count  INTEGER     NOT NULL DEFAULT 1000,
    status      TEXT        NOT NULL DEFAULT 'PENDING',
    error       TEXT,
    created_at  DATETIME    NOT NULL DEFAULT (datetime('now')),
    updated_at  DATETIME    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS checkpoints (
    job_id      TEXT        NOT NULL REFERENCES jobs(id),
    stage       TEXT        NOT NULL,          -- matches status enum value
    payload     TEXT        NOT NULL,          -- JSON blob  (model_dump → json.dumps)
    saved_at    DATETIME    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (job_id, stage)
);
"""

STAGE_ORDER = [
    "PENDING",
    "SERP_FETCHED",
    "PAGES_SCRAPED",
    "PRELIM_ANALYSES_COMPLETE",
    "BLUEPRINT_READY",
    "ARTICLE_GENERATED",
]
