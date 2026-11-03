"""RetailMind AI — SQLite Memory Schema Definitions."""

SCHEMA_VERSION = 1

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
"""

CREATE_ANALYTICAL_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS analytical_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    query TEXT NOT NULL,
    dataset_fingerprint TEXT NOT NULL,
    verified_summary TEXT NOT NULL,
    tool_calls_json TEXT,
    task_status TEXT NOT NULL,
    is_verified INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
"""

CREATE_MEMORY_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_mem_user_dataset ON analytical_memory(user_id, dataset_fingerprint);
CREATE INDEX IF NOT EXISTS idx_mem_user_session ON analytical_memory(user_id, session_id);
"""
