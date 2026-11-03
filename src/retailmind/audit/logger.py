"""RetailMind AI — Persistent SQLite Audit Subsystem.

Provides append-only, transactional, durable audit logging for all agent actions,
permission decisions, security alerts, and tool executions. Survives complete process restarts.
Never logs API keys, authorization secrets, or raw private customer data.
"""

import json
import logging
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.retailmind.audit.schema import AUDIT_SCHEMA_VERSION, CREATE_AUDIT_SCHEMA_SQL

logger = logging.getLogger("retailmind.audit")

SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:api_?key|auth_?token|authorization|ticket|secret|password|credential|bearer)",
    re.IGNORECASE,
)


def redact_sensitive_dict(data: Any, max_string_len: int = 500) -> Any:
    """Recursively redacts secrets, keys, and lengthy raw customer text."""
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            if SENSITIVE_KEY_PATTERN.search(str(k)):
                cleaned[k] = "[REDACTED_SECRET]"
            else:
                cleaned[k] = redact_sensitive_dict(v, max_string_len)
        return cleaned
    elif isinstance(data, list):
        return [redact_sensitive_dict(item, max_string_len) for item in data]
    elif isinstance(data, str):
        if len(data) > max_string_len:
            return data[:max_string_len] + f"... [TRUNCATED_{len(data)}_CHARS]"
        return data
    else:
        return data


class AuditLogger:
    """Append-only persistent SQLite audit logger with multi-tenant filtering."""

    _default_instance: Optional["AuditLogger"] = None

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "audit.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrency and crash resilience
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
        return self._conn

    def _initialize_db(self) -> None:
        """Applies schema migrations if needed."""
        conn = self._get_connection()
        with conn:
            conn.executescript(CREATE_AUDIT_SCHEMA_SQL)
            cursor = conn.execute("SELECT version FROM audit_schema_version ORDER BY version DESC LIMIT 1;")
            row = cursor.fetchone()
            if not row:
                conn.execute("INSERT INTO audit_schema_version (version) VALUES (?);", (AUDIT_SCHEMA_VERSION,))

    def log_event(
        self,
        task_id: str,
        user_id: str,
        session_id: str,
        tool_name: str,
        action_type: str,
        decision: str,
        authorization_outcome: str,
        execution_status: str,
        reason_code: str,
        duration_ms: float = 0.0,
        trace_id: Optional[str] = None,
        model_id: Optional[str] = None,
        transport: str = "internal",
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Appends a new audit record atomically to SQLite."""
        audit_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        # Sanitize details before storing
        safe_details = redact_sensitive_dict(details or {})
        details_json = json.dumps(safe_details, ensure_ascii=False)

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO audit_events (
                        timestamp, audit_id, task_id, user_id, session_id,
                        tool_name, action_type, decision, authorization_outcome,
                        execution_status, reason_code, duration_ms, trace_id,
                        model_id, transport, redacted_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        now_utc,
                        audit_id,
                        task_id,
                        user_id,
                        session_id,
                        tool_name,
                        action_type,
                        decision,
                        authorization_outcome,
                        execution_status,
                        reason_code,
                        float(duration_ms),
                        trace_id or "",
                        model_id or "",
                        transport,
                        details_json,
                    ),
                )
            return audit_id
        except Exception as exc:
            logger.error("Failed to write audit event to SQLite: %s", exc)
            # Fail closed or raise depending on policy; logging must never silently disappear
            return ""

    def query_events(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Queries persistent audit events for verification and inspection."""
        conn = self._get_connection()
        query = "SELECT * FROM audit_events WHERE 1=1"
        params: List[Any] = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if tool_name:
            query += " AND tool_name = ?"
            params.append(tool_name)
        if decision:
            query += " AND decision = ?"
            params.append(decision)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()

        events: List[Dict[str, Any]] = []
        for r in rows:
            events.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "audit_id": r["audit_id"],
                "task_id": r["task_id"],
                "user_id": r["user_id"],
                "session_id": r["session_id"],
                "tool_name": r["tool_name"],
                "action_type": r["action_type"],
                "decision": r["decision"],
                "authorization_outcome": r["authorization_outcome"],
                "execution_status": r["execution_status"],
                "reason_code": r["reason_code"],
                "duration_ms": r["duration_ms"],
                "trace_id": r["trace_id"],
                "model_id": r["model_id"],
                "transport": r["transport"],
                "redacted_details": json.loads(r["redacted_details"]),
            })
        return events

    def close(self) -> None:
        """Closes connection cleanly."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None

    @classmethod
    def get_default_logger(cls) -> "AuditLogger":
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance
