"""RetailMind AI — Persistent SQLite Audit Log Schema."""

AUDIT_SCHEMA_VERSION = 1

CREATE_AUDIT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS audit_schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    audit_id TEXT NOT NULL UNIQUE,
    task_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    action_type TEXT NOT NULL,
    decision TEXT NOT NULL,
    authorization_outcome TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    duration_ms REAL NOT NULL DEFAULT 0.0,
    trace_id TEXT,
    model_id TEXT,
    transport TEXT NOT NULL DEFAULT 'internal',
    redacted_details TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_user_session
    ON audit_events (user_id, session_id);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp
    ON audit_events (timestamp);

CREATE INDEX IF NOT EXISTS idx_audit_decision
    ON audit_events (decision);
"""
