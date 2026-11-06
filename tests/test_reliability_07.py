"""RetailMind AI — Reliability & SQLite Persistence Test Suite (Task 07).

Tests:
1. Agent component re-instantiation and verified financial memory recovery.
2. Complete separate process restart persistence (process 1 -> exit -> process 2).
3. Impact of REL-01 @property dynamic evaluation on storage path stability during a session.
4. Database corruption handling (file corruption -> explicit failure, zero false recovery).
5. AuditLogger & AuthorizationService persistence across component restarts.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.audit.logger import AuditLogger
from src.retailmind.config import settings
from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def restore_environment():
    """Ensures environment variables are strictly restored after each test."""
    orig_data_dir = os.environ.get("RETAILMIND_DATA_DIR")
    orig_reports_dir = os.environ.get("RETAILMIND_REPORTS_DIR")
    orig_sqlite_name = os.environ.get("SQLITE_DB_NAME")
    yield
    if orig_data_dir is not None:
        os.environ["RETAILMIND_DATA_DIR"] = orig_data_dir
    else:
        os.environ.pop("RETAILMIND_DATA_DIR", None)

    if orig_reports_dir is not None:
        os.environ["RETAILMIND_REPORTS_DIR"] = orig_reports_dir
    else:
        os.environ.pop("RETAILMIND_REPORTS_DIR", None)

    if orig_sqlite_name is not None:
        os.environ["SQLITE_DB_NAME"] = orig_sqlite_name
    else:
        os.environ.pop("SQLITE_DB_NAME", None)


# -----------------------------------------------------------------------------
# Test 1: Verified Fact Storage & Agent Re-instantiation Recovery
# -----------------------------------------------------------------------------
def test_agent_memory_reinstantiation_recovery(tmp_path: Path):
    """Example 1: Saving a verified fact, destroying the component, and creating a new agent component.
    The new component must successfully retrieve the verified fact.
    """
    db_file = tmp_path / "agent_memory.db"
    user_id = "merchant_101"
    session_id = "sess_turn_1"
    dataset_fp = "sha256_synthetic_sales_hash_abc"

    # Turn 1: Component 1 records a verified financial fact
    agent_mem_1 = SQLiteMemoryManager(db_path=db_file)
    saved = agent_mem_1.record_task_memory(
        user_id=user_id,
        session_id=session_id,
        task_id="task_turn_1",
        query="What is total sales and profit?",
        dataset_fingerprint=dataset_fp,
        summary="Verified Revenue is $2,945.00 and Net Profit is $1,525.50 across 15 orders.",
        task_status="SUCCESS",
        is_verified=True,
        tool_calls=[{"name": "summarize_sales", "result": {"net_revenue": 2945.0, "net_profit": 1525.5}}],
    )
    assert saved is True, "Failed to persist verified fact in component 1"

    # Close component 1 (simulating teardown / end of turn)
    agent_mem_1.close()
    del agent_mem_1

    # Turn 2: Completely new agent component created for subsequent turn
    agent_mem_2 = SQLiteMemoryManager(db_path=db_file)
    recalled = agent_mem_2.retrieve_relevant_context(
        user_id=user_id,
        dataset_fingerprint=dataset_fp,
    )

    assert len(recalled) == 1, "New agent component failed to recall past verified fact"
    assert "Revenue is $2,945.00 and Net Profit is $1,525.50" in recalled[0]["summary"]
    assert recalled[0]["task_id"] == "task_turn_1"

    # Formatted prompt injection test
    prompt_snippet = agent_mem_2.format_memory_for_prompt(user_id=user_id, dataset_fingerprint=dataset_fp)
    assert "HISTORICAL ANALYTICAL CONTEXT" in prompt_snippet
    assert "Verified Revenue is $2,945.00" in prompt_snippet

    agent_mem_2.close()


# -----------------------------------------------------------------------------
# Test 2: Complete Process Restart Persistence
# -----------------------------------------------------------------------------
def test_full_process_restart_persistence(tmp_path: Path):
    """Subprocess 1 writes verified memory to SQLite and terminates.
    Subprocess 2 opens the same SQLite file in a fresh Python runtime and reads it.
    """
    db_file = tmp_path / "proc_restart.db"
    user_id = "merchant_proc_1"
    dataset_fp = "dataset_fp_proc_restart_test"
    verified_fact = "Revenue=$2,945.00; Margin=51.8%."

    # Process 1: Write and exit
    p1_code = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{WORKSPACE_ROOT}")
from src.retailmind.memory.manager import SQLiteMemoryManager

mm = SQLiteMemoryManager(db_path=Path(r"{db_file}"))
ok = mm.record_task_memory(
    user_id="{user_id}",
    session_id="sess_p1",
    task_id="t_p1",
    query="Summarize sales",
    dataset_fingerprint="{dataset_fp}",
    summary="{verified_fact}",
    task_status="SUCCESS",
    is_verified=True,
)
mm.close()
print(f"P1_STATUS:{{ok}}")
sys.exit(0)
"""
    p1 = subprocess.run([sys.executable, "-c", p1_code], capture_output=True, text=True, timeout=15)
    assert p1.returncode == 0
    assert "P1_STATUS:True" in p1.stdout

    # Process 2: Read from fresh Python process
    p2_code = f"""
import sys, json
from pathlib import Path
sys.path.insert(0, r"{WORKSPACE_ROOT}")
from src.retailmind.memory.manager import SQLiteMemoryManager

mm = SQLiteMemoryManager(db_path=Path(r"{db_file}"))
records = mm.retrieve_relevant_context(user_id="{user_id}", dataset_fingerprint="{dataset_fp}")
mm.close()
output = {{
    "count": len(records),
    "summary": records[0]["summary"] if records else ""
}}
print(f"P2_DATA:{{json.dumps(output)}}")
sys.exit(0)
"""
    p2 = subprocess.run([sys.executable, "-c", p2_code], capture_output=True, text=True, timeout=15)
    assert p2.returncode == 0

    parsed = None
    for line in p2.stdout.splitlines():
        if line.startswith("P2_DATA:"):
            parsed = json.loads(line.replace("P2_DATA:", ""))
            break

    assert parsed is not None
    assert parsed["count"] == 1
    assert parsed["summary"] == verified_fact


# -----------------------------------------------------------------------------
# Test 3: Path Stability and Analysis of @property Impact in config.py
# -----------------------------------------------------------------------------
def test_path_stability_during_session_and_property_impact(tmp_path: Path):
    """Example 2: Audits storage path behavior when environment variables are modified mid-session.
    
    Findings to audit:
    1. During normal steady-state operation without env mutation:
       All instances of SQLiteMemoryManager() bind to the exact same database path.
    2. If RETAILMIND_DATA_DIR is mutated dynamically mid-session:
       Existing managers maintain their open file handle to the initial path.
       NEW managers instantiated after the mutation resolve to the updated path via @property.
    """
    initial_dir = tmp_path / "initial_data"
    initial_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RETAILMIND_DATA_DIR"] = str(initial_dir)

    # 1. First manager instantiated
    mm1 = SQLiteMemoryManager()
    initial_db_path = mm1.db_path
    assert initial_db_path.parent == initial_dir.resolve()
    assert initial_db_path == settings.sqlite_db_path

    # Record data in mm1
    mm1.record_task_memory(
        user_id="user_path_test",
        session_id="sess_1",
        task_id="t_init",
        query="Path test query",
        dataset_fingerprint="fp_path_test",
        summary="Stored in initial path.",
        task_status="SUCCESS",
        is_verified=True,
    )

    # 2. Mid-session environment mutation test
    mutated_dir = tmp_path / "mutated_data"
    mutated_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RETAILMIND_DATA_DIR"] = str(mutated_dir)

    # An existing manager instance still retains its initialized path
    assert mm1.db_path.parent == initial_dir.resolve()

    # However, settings.sqlite_db_path now dynamically reflects the new path due to @property
    assert settings.sqlite_db_path.parent == mutated_dir.resolve()

    # A NEW manager instantiated after the mid-session mutation binds to the NEW path
    mm2 = SQLiteMemoryManager()
    assert mm2.db_path.parent == mutated_dir.resolve()
    assert mm2.db_path != mm1.db_path

    # Verify mm2 does not see data stored in mm1's database (path divergence detected)
    recalled_in_mm2 = mm2.retrieve_relevant_context(user_id="user_path_test", dataset_fingerprint="fp_path_test")
    assert len(recalled_in_mm2) == 0, "mm2 unexpectedly saw data from mm1 across distinct database files!"

    mm1.close()
    mm2.close()


# -----------------------------------------------------------------------------
# Test 4: Database Corruption Handling (No False Recovery)
# -----------------------------------------------------------------------------
def test_corrupted_database_handling(tmp_path: Path):
    """Example 3: Corrupt database -> Must fail clearly/gracefully without claiming successful recovery."""
    corrupt_db_file = tmp_path / "corrupt.db"
    # Write non-SQLite garbage bytes
    corrupt_db_file.write_bytes(b"THIS_IS_CORRUPTED_BINARY_TRASH_NOT_A_VALID_SQLITE_DATABASE_HEADER\x00\xff\xfe\x01\x02\x03")

    mm = SQLiteMemoryManager(db_path=corrupt_db_file)

    # 1. Attempting to record to corrupted database must return False (failure cleanly communicated)
    record_status = mm.record_task_memory(
        user_id="user_corrupt_test",
        session_id="sess_corrupt",
        task_id="task_corrupt",
        query="Query on corrupted DB",
        dataset_fingerprint="fp_corrupt",
        summary="Should not be stored",
        task_status="SUCCESS",
        is_verified=True,
    )
    assert record_status is False, "record_task_memory must return False when SQLite file is corrupted"

    # 2. Attempting to retrieve from corrupted database must return [] (empty list, not false data or crash)
    retrieved = mm.retrieve_relevant_context(
        user_id="user_corrupt_test",
        dataset_fingerprint="fp_corrupt",
    )
    assert retrieved == [], "retrieve_relevant_context must return empty list on corrupted database"

    # 3. Format for prompt must return empty string
    prompt_str = mm.format_memory_for_prompt(
        user_id="user_corrupt_test",
        dataset_fingerprint="fp_corrupt",
    )
    assert prompt_str == "", "format_memory_for_prompt must return empty string on corrupted database"

    mm.close()


# -----------------------------------------------------------------------------
# Test 5: Audit Logger & Authorization Service Persistence
# -----------------------------------------------------------------------------
def test_audit_logger_and_auth_persistence_across_components(tmp_path: Path):
    """Verifies that AuditLogger and AuthorizationService also durably persist events across instance lifecycles."""
    audit_db = tmp_path / "audit_test.db"
    auth_db = tmp_path / "auth_test.db"

    # 1. AuditLogger persistence
    logger1 = AuditLogger(db_path=audit_db)
    logger1.log_event(
        task_id="task_rel_01",
        user_id="audit_user_1",
        session_id="sess_audit",
        tool_name="summarize_sales",
        action_type="READ",
        decision="ALLOWED",
        authorization_outcome="AUTO",
        execution_status="SUCCESS",
        reason_code="OK",
        transport="mcp",
    )
    logger1.close()

    # Reopen in new AuditLogger component
    logger2 = AuditLogger(db_path=audit_db)
    events = logger2.query_events(user_id="audit_user_1", limit=10)
    assert len(events) == 1
    assert events[0]["tool_name"] == "summarize_sales"
    assert events[0]["task_id"] == "task_rel_01"
    logger2.close()

    # 2. AuthorizationService persistence
    auth1 = AuthorizationService(db_path=auth_db)
    ticket_id = auth1.issue_ticket(
        user_id="auth_user_1",
        session_id="sess_auth",
        tool_name="generate_report",
        params={"title": "Test Report"},
    )
    auth1.close()

    # Reopen in new AuthorizationService component
    auth2 = AuthorizationService(db_path=auth_db)
    is_valid, reason = auth2.verify_and_consume_ticket(
        ticket_id=ticket_id,
        user_id="auth_user_1",
        session_id="sess_auth",
        tool_name="generate_report",
        params={"title": "Test Report"},
    )
    assert is_valid is True, f"Failed to consume ticket in new component: {reason}"
    auth2.close()
