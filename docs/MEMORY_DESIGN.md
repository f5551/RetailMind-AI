# RetailMind AI — Persistent SQLite Memory Architecture

## 1. Objectives and Principles

RetailMind AI requires persistent analytical memory to retain verified analytical findings, quality audit results, and user context across session boundaries and complete process terminations.

Key principles enforced by the memory architecture:
1. **Durable Persistence:** Uses SQLite with Write-Ahead Logging (`WAL` mode) and synchronous disk flushing. Survives operating system and process restarts.
2. **User Isolation:** Strict multi-tenant isolation where queries are parameter-bound by `user_id`. One user cannot read or influence another user's analytical context.
3. **Dataset Fingerprint Scoping:** Memories are bound to the SHA-256 hash fingerprint of the active dataset (`dataset_fingerprint`). If a user uploads a new dataset, previous dataset findings do not cross-contaminate.
4. **Quality Filtering:** Unverified failures and malicious injections (`is_verified = 0`) are excluded from memory retrieval so bad outputs never pollute future reasoning.
5. **Bounded Context Injection:** Retrieved memories are injected into the agent prompt with strict length and relevance bounds, avoiding prompt bloat and runaway token consumption.

## 2. Database Schema (`src/retailmind/memory/schema.py`)

The SQLite database schema uses formal schema versioning:

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytical_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    dataset_fingerprint TEXT NOT NULL,
    task_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    key_findings TEXT NOT NULL,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    is_verified INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_memory_user_dataset
    ON analytical_memory (user_id, dataset_fingerprint);

CREATE INDEX IF NOT EXISTS idx_memory_user_session
    ON analytical_memory (user_id, session_id);
```

## 3. Manager API (`src/retailmind/memory/manager.py`)

`SQLiteMemoryManager` provides:
- `save_finding(user_id, session_id, dataset_fingerprint, task_id, query_text, key_findings, metrics, is_verified)`
- `retrieve_relevant_context(user_id, dataset_fingerprint, limit=3)`: Only returns verified memories (`is_verified = 1`) matching `user_id` and `dataset_fingerprint`.
- `format_memory_for_prompt(memories)`: Produces a clean, bounded Markdown context block for system prompt injection.
- `close()`: Closes connection safely.

## 4. Verification Across Process Restarts

To satisfy Capstone requirement `M2`, memory persistence across a complete process shutdown and restart was proven via `tests/test_memory_persistence.py::test_complete_process_restart_persistence`.

The test runs two separate, independent OS subprocesses via `subprocess.run([sys.executable, ...])`:
1. **Subprocess 1 (Write & Die):**
   - Connects to SQLite database.
   - Saves finding: `"Total revenue for Q1 was $2,945.00 with 51.8% gross margin."`
   - Closes database connection.
   - Terminates completely with exit code 0.
2. **Subprocess 2 (Spawn & Read):**
   - Starts in a fresh, isolated Python environment.
   - Connects to the same SQLite database file.
   - Queries `retrieve_relevant_context(user_id="user_proc_test", dataset_fingerprint="abc_fingerprint_123")`.
   - Confirms that the exact finding is recovered with 100% fidelity.
   - Verifies that querying with a different `user_id` returns 0 results (isolation maintained).
