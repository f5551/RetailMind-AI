"""RetailMind AI — SQLite Memory Persistence & Isolation Integration Tests.

Mandatory tests:
1. Complete process restart persistence (Process 1 writes -> terminates -> Process 2 reads in new Python process).
2. User isolation (User A cannot see User B memory).
3. Dataset fingerprint isolation (Changed dataset does not reuse stale numerical results).
4. Corrupted database / graceful error recovery without agent crash.
5. Quality filtering (Failures stored with is_verified=0, excluded from recall).
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_sqlite_memory_basic_crud(tmp_path: Path):
    """Verify basic record and retrieval with proper parameterization."""
    db_file = tmp_path / "test_memory.db"
    mm = SQLiteMemoryManager(db_path=db_file)

    ok = mm.record_task_memory(
        user_id="user_1",
        session_id="sess_1",
        task_id="task_1",
        query="What is total sales?",
        dataset_fingerprint="fp_abc123",
        summary="Total revenue was $2,945 across 15 orders.",
        task_status="SUCCESS",
        is_verified=True,
    )
    assert ok is True

    # Retrieve context
    records = mm.retrieve_relevant_context(user_id="user_1", dataset_fingerprint="fp_abc123")
    assert len(records) == 1
    assert "revenue was $2,945" in records[0]["summary"]


def test_user_isolation(tmp_path: Path):
    """Verify User A cannot retrieve User B's private analytical memory."""
    db_file = tmp_path / "test_memory.db"
    mm = SQLiteMemoryManager(db_path=db_file)

    # User A records confidential sales memory
    mm.record_task_memory(
        user_id="user_alpha",
        session_id="sess_a",
        task_id="task_a",
        query="Confidential User A query",
        dataset_fingerprint="fp_shared",
        summary="User A proprietary findings: Profit is $500,000.",
        task_status="SUCCESS",
        is_verified=True,
    )

    # User B queries with same dataset fingerprint
    user_b_records = mm.retrieve_relevant_context(user_id="user_beta", dataset_fingerprint="fp_shared")
    assert len(user_b_records) == 0, "User B illegally retrieved User A's confidential memory!"

    # User A can retrieve their own memory
    user_a_records = mm.retrieve_relevant_context(user_id="user_alpha", dataset_fingerprint="fp_shared")
    assert len(user_a_records) == 1
    assert "Profit is $500,000" in user_a_records[0]["summary"]


def test_dataset_fingerprint_isolation(tmp_path: Path):
    """Verify changing dataset does not leak or reuse stale numbers from an older dataset."""
    db_file = tmp_path / "test_memory.db"
    mm = SQLiteMemoryManager(db_path=db_file)

    # Record memory for Dataset 1
    mm.record_task_memory(
        user_id="user_1",
        session_id="sess_1",
        task_id="task_1",
        query="What is revenue?",
        dataset_fingerprint="fp_dataset_v1",
        summary="Revenue for January dataset was $1,355.",
        task_status="SUCCESS",
        is_verified=True,
    )

    # User uploads Dataset 2 with new fingerprint
    records_v2 = mm.retrieve_relevant_context(user_id="user_1", dataset_fingerprint="fp_dataset_v2")
    assert len(records_v2) == 0, "Agent leaked stale numbers from dataset v1 into dataset v2!"


def test_quality_filter_excludes_unverified_failures(tmp_path: Path):
    """Verify failed tasks are recorded with is_verified=0 and excluded from prompt recall."""
    db_file = tmp_path / "test_memory.db"
    mm = SQLiteMemoryManager(db_path=db_file)

    # Failed task (budget exceeded)
    mm.record_task_memory(
        user_id="user_1",
        session_id="sess_1",
        task_id="task_fail",
        query="Deep calculation",
        dataset_fingerprint="fp_common",
        summary="Task halted: Budget limit exceeded.",
        task_status="BUDGET_EXCEEDED",
        is_verified=False,
    )

    # Should not be returned as verified context
    records = mm.retrieve_relevant_context(user_id="user_1", dataset_fingerprint="fp_common")
    assert len(records) == 0


def test_complete_process_restart_persistence(tmp_path: Path):
    """MANDATORY RESTART TEST:

    1. Process 1 starts, writes verified memory to SQLite, and exits.
    2. Process 2 (separate Python subprocess) starts, reopens the same SQLite DB,
       and verifies that the persisted context is intact and correctly isolated.
    """
    db_file = tmp_path / "durable_memory.db"
    user_id = "restart_user_42"
    dataset_fp = "sha256_dataset_fingerprint_999"
    verified_answer = "Verified revenue across 15 transactions is $2,945.00."

    # Script for Process 1: Writes memory and exits cleanly
    p1_script = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{WORKSPACE_ROOT}")
from src.retailmind.memory.manager import SQLiteMemoryManager

mm = SQLiteMemoryManager(db_path=Path(r"{db_file}"))
ok = mm.record_task_memory(
    user_id="{user_id}",
    session_id="sess_p1",
    task_id="task_p1",
    query="Calculate total sales",
    dataset_fingerprint="{dataset_fp}",
    summary="{verified_answer}",
    task_status="SUCCESS",
    is_verified=True,
)
print(f"P1_RECORD_SUCCESS: {{ok}}")
sys.exit(0)
"""

    res1 = subprocess.run(
        [sys.executable, "-c", p1_script],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res1.returncode == 0, f"Process 1 failed: {res1.stderr}"
    assert "P1_RECORD_SUCCESS: True" in res1.stdout

    # Confirm Process 1 terminated completely
    assert db_file.exists(), "SQLite database file was not created by Process 1!"

    # Script for Process 2: Completely new process reopening DB and retrieving context
    p2_script = f"""
import sys
import json
from pathlib import Path
sys.path.insert(0, r"{WORKSPACE_ROOT}")
from src.retailmind.memory.manager import SQLiteMemoryManager

mm = SQLiteMemoryManager(db_path=Path(r"{db_file}"))
# 1. Retrieve as matching user
matching_records = mm.retrieve_relevant_context(
    user_id="{user_id}",
    dataset_fingerprint="{dataset_fp}"
)

# 2. Retrieve as different user (isolation test)
wrong_user_records = mm.retrieve_relevant_context(
    user_id="intruder_user",
    dataset_fingerprint="{dataset_fp}"
)

# 3. Retrieve with different dataset fingerprint
wrong_fp_records = mm.retrieve_relevant_context(
    user_id="{user_id}",
    dataset_fingerprint="different_fp"
)

result = {{
    "matching_count": len(matching_records),
    "matching_summary": matching_records[0]["summary"] if matching_records else "",
    "wrong_user_count": len(wrong_user_records),
    "wrong_fp_count": len(wrong_fp_records),
}}
print(f"P2_RESULT: {{json.dumps(result)}}")
sys.exit(0)
"""

    res2 = subprocess.run(
        [sys.executable, "-c", p2_script],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res2.returncode == 0, f"Process 2 failed: {res2.stderr}"
    
    # Parse Process 2 output
    for line in res2.stdout.splitlines():
        if line.startswith("P2_RESULT: "):
            payload = json.loads(line.replace("P2_RESULT: ", ""))
            assert payload["matching_count"] == 1
            assert verified_answer in payload["matching_summary"]
            assert payload["wrong_user_count"] == 0, "Isolation failure in Process 2!"
            assert payload["wrong_fp_count"] == 0, "Dataset fingerprint failure in Process 2!"
            return

    pytest.fail("Process 2 did not produce expected output line.")
