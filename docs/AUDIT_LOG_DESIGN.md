# RetailMind AI — Audit Logging Architecture and Specification

## 1. Objectives and Compliance

The RetailMind AI audit logging subsystem (`src/retailmind/audit/`) provides durable, append-only, tamper-evident recording of all agent transactions, security events, permission evaluations, and tool executions.

Key compliance requirements satisfied:
1. **Traceability:** Every decision (allowed, denied, error, blocked) is tied to a specific `task_id`, `session_id`, and `user_id`.
2. **Credential & Privacy Hygiene:** Zero API keys, authorization capability tokens, or unredacted customer data are ever persisted to the audit log.
3. **Immutability & Durability:** Stored in a dedicated SQLite database (`data/audit.db`) using Write-Ahead Logging (`WAL` mode) and synchronous disk commits. Survives process and host restarts.
4. **Independent Audit Querying:** Exposed via structured Python query APIs for compliance audits, automated test verification, and administrative review.

---

## 2. Audit Event Schema

```sql
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                -- ISO-8601 UTC timestamp
    audit_id TEXT NOT NULL UNIQUE,          -- Unique UUID per audit event
    task_id TEXT NOT NULL,                  -- Agent task identifier
    user_id TEXT NOT NULL,                  -- Active authenticated user identifier
    session_id TEXT NOT NULL,               -- Active session identifier
    tool_name TEXT NOT NULL,                -- Target tool (e.g. summarize_sales, generate_report)
    action_type TEXT NOT NULL,              -- Action classification (READ, WRITE, SECURITY, SYSTEM)
    decision TEXT NOT NULL,                 -- Enforcement decision (ALLOWED, DENIED, ERROR, BLOCKED)
    authorization_outcome TEXT NOT NULL,    -- Detailed auth outcome (e.g. APPROVED_BY_HUMAN_CALLBACK, REJECTED_NO_HUMAN_APPROVAL)
    execution_status TEXT NOT NULL,         -- Tool execution status (SUCCESS, FAILED, BLOCKED)
    reason_code TEXT NOT NULL,              -- Controlled reason code
    duration_ms REAL NOT NULL DEFAULT 0.0,  -- Execution duration in milliseconds
    trace_id TEXT,                          -- Corresponding JSONL trace reference
    model_id TEXT,                          -- Model used (e.g. gemini-3.1-flash-lite)
    transport TEXT NOT NULL DEFAULT 'mcp',  -- Transport channel (mcp or internal)
    redacted_details TEXT NOT NULL DEFAULT '{}' -- JSON dictionary of sanitized parameters
);

CREATE INDEX IF NOT EXISTS idx_audit_user_session ON audit_events (user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events (timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_decision ON audit_events (decision);
```

---

## 3. Redaction and Sanitization Rules

Before any event is committed, `redact_sensitive_dict()` enforces:
1. **Secret Pattern Masking:** Any key matching `api_key`, `token`, `secret`, `password`, `auth`, `ticket`, or `credential` is replaced with `"[REDACTED_SECRET]"`.
2. **Length Limiting:** Any string value exceeding 500 characters is truncated with an explicit marker: `"... [TRUNCATED_N_CHARS]"` to prevent raw CSV dataset dumps into the audit log.
3. **Structured Non-Executable Format:** Stored as validated JSON text.

---

## 4. Reason Codes Reference

| Reason Code | Action Type | Decision | Description |
|---|---|---|---|
| `READ_ONLY_POLICY_AUTO` | `READ` | `ALLOWED` | Read-only analysis tool executed automatically under `ask_on_write` policy. |
| `ASK_ON_WRITE_APPROVAL_REQUIRED` | `WRITE` | `DENIED` | Write tool (`generate_report`) was requested by model without human confirmation. |
| `EXTERNAL_APPROVAL_VALIDATED` | `WRITE` | `ALLOWED` | Human user explicitly confirmed approval; capability ticket verified and consumed. |
| `FORGED_OR_UNKNOWN_TICKET` | `WRITE` | `DENIED` | Direct MCP tool invocation supplied invalid or fabricated authorization ticket. |
| `REPLAY_ATTACK_TICKET_ALREADY_CONSUMED` | `WRITE` | `DENIED` | Re-use of an already consumed authorization ticket was blocked. |
| `PARAMETER_TAMPERING_DETECTED` | `WRITE` | `DENIED` | Arguments did not match the cryptographic hash bound to the authorization ticket. |
| `HOSTILE_INJECTION_DETECTED` | `SECURITY` | `BLOCKED` | Adversarial injection pattern identified in input data or query. |

---

## 5. Storage Limitations and Operational Notes

- **Local Storage Scope:** The audit trail resides in `data/audit.db` on local disk. While robust against process restarts, crashes, and application errors, it does not guarantee cryptographic non-repudiation against an operating system administrator with root filesystem access.
- **Production Recommendation:** In a production cloud deployment (e.g. Railway/Render), attach a durable persistent volume mount to `/data` or stream audit events asynchronously to an external SIEM (e.g., Google Cloud Logging / Datadog).
