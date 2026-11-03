"""RetailMind AI — Cryptographic Authorization Service & Capability Tickets.

Provides single-use, time-bound, parameter-bound authorization tickets for write actions.
Enforces fail-closed privilege verification across the host agent loop and MCP server subprocess.
Prevents replay attacks, forged tokens, parameter tampering, and cross-session reuse.
"""

import hashlib
import json
import logging
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("retailmind.auth")


def compute_parameters_hash(params: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of canonicalized JSON tool arguments.

    Strips any internal authorization or ticket metadata before hashing.
    """
    cleaned: Dict[str, Any] = {}
    for k, v in sorted(params.items()):
        if k in ("auth_ticket", "approval_token", "is_approved", "_meta"):
            continue
        cleaned[k] = v

    canonical_json = json.dumps(cleaned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class AuthorizationService:
    """Manages secure, single-use authorization tickets with transactional SQLite backing."""

    _default_instance: Optional["AuthorizationService"] = None

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "auth.db"
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
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
        return self._conn

    def _initialize_db(self) -> None:
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_tickets (
                    ticket_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    params_hash TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    is_used INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tickets_user_session ON auth_tickets (user_id, session_id);"
            )

    def issue_ticket(
        self,
        user_id: str,
        session_id: str,
        tool_name: str,
        params: Dict[str, Any],
        ttl_seconds: float = 60.0,
    ) -> str:
        """Issues a single-use cryptographically random capability ticket bound to action parameters."""
        ticket_id = f"cap_{secrets.token_urlsafe(24)}"
        params_hash = compute_parameters_hash(params)
        now = time.time()
        expires_at = now + ttl_seconds

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO auth_tickets (
                        ticket_id, user_id, session_id, tool_name,
                        params_hash, created_at, expires_at, is_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0);
                    """,
                    (ticket_id, user_id, session_id, tool_name, params_hash, now, expires_at),
                )
            logger.info("Issued authorization ticket '%s' for tool '%s'.", ticket_id[:12], tool_name)
            return ticket_id
        except Exception as exc:
            logger.error("Failed to issue authorization ticket: %s", exc)
            raise RuntimeError(f"Authorization service failed to issue ticket: {exc}") from exc

    def verify_and_consume_ticket(
        self,
        ticket_id: Optional[str],
        user_id: str,
        session_id: str,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """Atomically validates and consumes an authorization ticket.

        Fails closed on missing ticket, replay, expiration, parameter tampering, or mismatch.
        """
        if not ticket_id or not isinstance(ticket_id, str) or not ticket_id.strip():
            return False, "MISSING_AUTHORIZATION_TICKET"

        params_hash = compute_parameters_hash(params)
        now = time.time()

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "SELECT * FROM auth_tickets WHERE ticket_id = ?;",
                    (ticket_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return False, "FORGED_OR_UNKNOWN_TICKET"

                if row["is_used"] == 1:
                    return False, "REPLAY_ATTACK_TICKET_ALREADY_CONSUMED"

                if now > row["expires_at"]:
                    return False, "TICKET_EXPIRED"

                if row["tool_name"] != tool_name:
                    return False, "TOOL_NAME_MISMATCH"

                # Check session binding if provided
                if session_id and row["session_id"] != session_id:
                    return False, "SESSION_ID_MISMATCH"

                # Check user binding if provided
                if user_id and row["user_id"] != user_id:
                    return False, "USER_ID_MISMATCH"

                if row["params_hash"] != params_hash:
                    return False, "PARAMETER_TAMPERING_DETECTED"

                # Atomically consume ticket
                conn.execute(
                    "UPDATE auth_tickets SET is_used = 1 WHERE ticket_id = ?;",
                    (ticket_id,),
                )

            return True, "AUTHORIZED"

        except Exception as exc:
            logger.error("Authorization check failed with exception: %s", exc)
            # Fail closed
            return False, f"AUTHORIZATION_SERVICE_ERROR: {str(exc)}"

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None

    @classmethod
    def get_default_service(cls) -> "AuthorizationService":
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance
