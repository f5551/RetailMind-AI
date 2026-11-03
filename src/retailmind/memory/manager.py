"""RetailMind AI — Persistent SQLite Memory Manager.

Provides durable episodic memory surviving complete application process restarts.
Enforces strict user isolation, session isolation, and dataset fingerprint association.
Uses parameterized queries, schema versioning, and graceful error recovery.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.retailmind.config import settings
from src.retailmind.memory.schema import (
    CREATE_ANALYTICAL_MEMORY_TABLE,
    CREATE_MEMORY_INDEXES,
    CREATE_SCHEMA_VERSION_TABLE,
    SCHEMA_VERSION,
)

logger = logging.getLogger("retailmind.memory")


class SQLiteMemoryManager:
    """Manages persistent SQLite memory records with user and dataset isolation."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or settings.sqlite_db_path)
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Opens a connection with WAL mode and busy timeout."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _initialize_database(self) -> None:
        """Applies schema migrations idempotently."""
        try:
            with self._get_connection() as conn:
                conn.execute(CREATE_SCHEMA_VERSION_TABLE)
                conn.execute(CREATE_ANALYTICAL_MEMORY_TABLE)
                conn.executescript(CREATE_MEMORY_INDEXES)

                # Check or record schema version
                cur = conn.cursor()
                cur.execute("SELECT MAX(version) FROM schema_version;")
                row = cur.fetchone()
                current_ver = row[0] if row and row[0] is not None else 0
                if current_ver < SCHEMA_VERSION:
                    now_str = datetime.now(timezone.utc).isoformat()
                    cur.execute(
                        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?);",
                        (SCHEMA_VERSION, now_str),
                    )
                conn.commit()
        except Exception as exc:
            logger.error("Failed to initialize SQLite memory schema: %s", exc)

    def record_task_memory(
        self,
        user_id: str,
        session_id: str,
        task_id: str,
        query: str,
        dataset_fingerprint: str,
        summary: str,
        task_status: str,
        is_verified: bool,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Persists task analytical memory to SQLite using parameterized query."""
        if not user_id or not dataset_fingerprint:
            logger.warning("Refusing to record memory: missing user_id or dataset_fingerprint.")
            return False

        now_str = datetime.now(timezone.utc).isoformat()
        tool_calls_json = json.dumps(tool_calls or [])

        sql = """
        INSERT INTO analytical_memory (
            user_id, session_id, task_id, query,
            dataset_fingerprint, verified_summary,
            tool_calls_json, task_status, is_verified, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            user_id,
            session_id,
            task_id,
            query.strip(),
            dataset_fingerprint,
            summary.strip(),
            tool_calls_json,
            task_status,
            1 if is_verified else 0,
            now_str,
        )

        try:
            with self._get_connection() as conn:
                conn.execute(sql, params)
                conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to write analytical memory to SQLite: %s", exc)
            return False

    def retrieve_relevant_context(
        self,
        user_id: str,
        dataset_fingerprint: str,
        limit: int = 3,
        max_chars: int = 1500,
    ) -> List[Dict[str, Any]]:
        """Retrieves bounded historical verified context strictly matching user_id and dataset_fingerprint.
        
        Enforces:
        - Absolute user isolation (user A cannot see user B records).
        - Dataset association (mismatched/changed datasets return zero records).
        - Quality filter (only is_verified=1 and SUCCESS status returned).
        - Bounded context (limits record count and total length).
        """
        if not user_id or not dataset_fingerprint:
            return []

        sql = """
        SELECT query, verified_summary, created_at
        FROM analytical_memory
        WHERE user_id = ?
          AND dataset_fingerprint = ?
          AND is_verified = 1
          AND task_status = 'SUCCESS'
        ORDER BY id DESC
        LIMIT ?;
        """
        memories: List[Dict[str, Any]] = []

        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (user_id, dataset_fingerprint, limit))
                rows = cur.fetchall()

                accumulated_chars = 0
                for r in rows:
                    summary = r["verified_summary"]
                    # Bound individual entry size
                    if len(summary) > 400:
                        summary = summary[:400] + "..."
                    
                    entry = {
                        "query": r["query"],
                        "summary": summary,
                        "timestamp": r["created_at"],
                    }
                    entry_len = len(entry["query"]) + len(entry["summary"])
                    if accumulated_chars + entry_len > max_chars:
                        break
                    accumulated_chars += entry_len
                    memories.append(entry)

        except Exception as exc:
            logger.error("Failed to query SQLite memory: %s", exc)
            return []

        return memories

    def format_memory_for_prompt(
        self,
        user_id: str,
        dataset_fingerprint: str,
        limit: int = 3,
    ) -> str:
        """Formats recalled memory into a concise prompt section."""
        records = self.retrieve_relevant_context(user_id, dataset_fingerprint, limit=limit)
        if not records:
            return ""

        lines = ["\n[PREVIOUS VERIFIED ANALYTICAL CONTEXT FOR THIS USER & DATASET]"]
        for i, rec in enumerate(records, 1):
            lines.append(f"{i}. Question: {rec['query']}")
            lines.append(f"   Verified Finding: {rec['summary']}")
        lines.append("[END OF PREVIOUS CONTEXT — Verify against tools if performing new calculations]\n")
        return "\n".join(lines)
