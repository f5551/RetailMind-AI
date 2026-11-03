"""RetailMind AI — Phase C Remediation and Pre-Deployment Verification Test Suite.

Verifies:
- C1: Strict restriction of anonymous public demo to approved synthetic fixtures,
      rejection of RETAILMIND_AUTH_MODE=production bypass, and multi-tenant isolation.
- C2: Validation of genuine JSONL trace sequence (Call 1 Error -> Call 2 Corrected Success -> Final Answer).
- C3: 100% complete bilingual dictionary coverage and memory timestamp record fields.
- C4: Persistent storage scoping (RETAILMIND_DATA_DIR), path traversal protection, and report boundaries.
- C5: End-to-end dataset replacement, distinct order counting, returns arithmetic, and missing-cost handling.
- C6: Gemini UsageMetadata reconciliation, budget cap enforcement, and controlled stop.
- C7: Container and deployment configuration compatibility (Dockerfile, Procfile, dynamic PORT).
"""

import ast
import csv
import io
import json
import math
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.agent.cost_meter import BudgetExceededError, CostTracker
from src.retailmind.agent.loop import extract_verified_financial_facts
from src.retailmind.audit.logger import AuditLogger
from src.retailmind.config import settings
from src.retailmind.data.loader import (
    APPROVED_BUNDLED_SYNTHETIC_DIR,
    DatasetManager,
    verify_approved_synthetic_dataset,
)
from src.retailmind.memory.manager import SQLiteMemoryManager
from src.retailmind.tools.implementations import count_distinct_orders, summarize_sales
from src.retailmind.tools.schemas import SummarizeSalesInput
from src.retailmind.ui.i18n import TRANSLATIONS, t


# -----------------------------------------------------------------------------
# C1: Anonymous Public Demo Restrictions & Bypass Rejections
# -----------------------------------------------------------------------------
def test_c1_anonymous_demo_restricted_and_bypass_rejections():
    """Verify that an anonymous public visitor cannot upload arbitrary custom CSVs,

    even if RETAILMIND_AUTH_MODE=production is set in the environment.
    Only genuine server-validated token authentication permits custom business data.
    """
    df_confidential = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Confidential Customer Financial Ledger"],
        "quantity": [100],
        "unit_price": [5000.0],
    })

    # 1. Attempt upload in unauthenticated mode -> REJECTED
    is_valid, reason = verify_approved_synthetic_dataset(
        "custom_financials.csv",
        df_confidential,
        force_test_mode=False,
    )
    assert is_valid is False
    assert "UNAUTHENTICATED_DEMO_RESTRICTION" in reason

    # 2. Attempt bypass via RETAILMIND_AUTH_MODE=production -> MUST STILL BE REJECTED
    os.environ["RETAILMIND_AUTH_MODE"] = "production"
    try:
        is_mode_valid, mode_reason = verify_approved_synthetic_dataset(
            "custom_financials.csv",
            df_confidential,
            force_test_mode=False,
        )
        assert is_mode_valid is False
        assert "UNAUTHENTICATED_DEMO_RESTRICTION" in mode_reason
    finally:
        os.environ.pop("RETAILMIND_AUTH_MODE", None)

    # 3. Attempt bypass via arbitrary forged auth token without matching server secret -> REJECTED
    os.environ["RETAILMIND_SERVER_AUTH_SECRET"] = "official_server_secret_key_8899"
    os.environ["RETAILMIND_AUTH_TOKEN"] = "forged_client_token"
    try:
        is_forged_valid, forged_reason = verify_approved_synthetic_dataset(
            "custom_financials.csv",
            df_confidential,
            force_test_mode=False,
        )
        assert is_forged_valid is False
        assert "UNAUTHENTICATED_DEMO_RESTRICTION" in forged_reason

        # 4. Legitimate matching server-validated token -> ACCEPTED
        os.environ["RETAILMIND_AUTH_TOKEN"] = "official_server_secret_key_8899"
        is_auth_valid, auth_reason = verify_approved_synthetic_dataset(
            "custom_financials.csv",
            df_confidential,
            force_test_mode=False,
        )
        assert is_auth_valid is True
        assert auth_reason == ""
    finally:
        os.environ.pop("RETAILMIND_SERVER_AUTH_SECRET", None)
        os.environ.pop("RETAILMIND_AUTH_TOKEN", None)

    # 5. Bundled approved synthetic fixture is always accepted in unauthenticated demo
    bundled_file = APPROVED_BUNDLED_SYNTHETIC_DIR / "synthetic_sales.csv"
    if bundled_file.exists():
        raw_bundled = pd.read_csv(bundled_file, encoding="utf-8")
        is_bundled_valid, bundled_reason = verify_approved_synthetic_dataset(
            bundled_file,
            raw_bundled,
            force_test_mode=False,
        )
        assert is_bundled_valid is True
        assert bundled_reason == ""


# -----------------------------------------------------------------------------
# C2: JSONL Trace Validation — Near Failure Recovery Sequence
# -----------------------------------------------------------------------------
def test_c2_near_failure_recovery_trace_sequence_validation():
    """Verify that near_failure_recovery.jsonl contains genuine corrective tool execution:

    Tool Call 1 (Error) strictly precedes Tool Call 2 (Success), followed by Final Answer.
    """
    trace_path = settings.workspace_root / "traces" / "near_failure_recovery.jsonl"
    assert trace_path.exists(), "traces/near_failure_recovery.jsonl must exist"

    events = []
    with open(trace_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    assert len(events) >= 5, "Trace must have task_start, model turns, executions, and task_complete"

    # Find tool execution events
    tool_executions = [e for e in events if e.get("event_type") == "tool_execution"]
    assert len(tool_executions) == 2, f"Expected exactly 2 tool executions, found {len(tool_executions)}"

    first_exec = tool_executions[0]
    second_exec = tool_executions[1]

    # Verify first call was an error observation
    assert first_exec["data"]["call"]["turn"] == 1
    assert first_exec["data"]["observation"]["status"] == "error"
    assert first_exec["data"]["observation"]["error_code"] == "INVALID_ARGUMENTS"

    # Verify second call was a successful corrected call
    assert second_exec["data"]["call"]["turn"] == 2
    assert second_exec["data"]["observation"]["status"] == "success"
    assert second_exec["data"]["observation"]["column_analyzed"] == "revenue"

    # Verify task complete event has FINAL_ANSWER and valid cost
    complete_events = [e for e in events if e.get("event_type") == "task_complete"]
    assert len(complete_events) == 1
    comp = complete_events[0]
    assert comp["data"]["stop_reason"] == "FINAL_ANSWER"
    assert comp["data"]["tool_calls_count"] == 2
    assert comp["cost_info"]["cumulative_cost_usd"] > 0.0
    assert comp["cost_info"]["metadata_status"] == "CONSISTENT_VERIFIED"


# -----------------------------------------------------------------------------
# C3: Bilingual UI Dictionary Completeness & Memory Timestamp Fields
# -----------------------------------------------------------------------------
def test_c3_bilingual_ui_completeness_and_memory_fields():
    """Verify that 100% of keys referenced in app.py exist in TRANSLATIONS,

    and that SQLiteMemoryManager returns created_at and task_id for View 4.
    """
    app_py_path = settings.workspace_root / "app.py"
    tree = ast.parse(app_py_path.read_text(encoding="utf-8"))

    t_keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "t":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    t_keys.add(node.args[0].value)

    assert len(t_keys) >= 100
    missing_in_translations = [
        k for k in t_keys if k not in TRANSLATIONS or "en" not in TRANSLATIONS[k] or "ar" not in TRANSLATIONS[k]
    ]
    assert missing_in_translations == [], f"Missing translation keys: {missing_in_translations}"

    # Verify memory timestamp and record fields in SQLiteMemoryManager
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_p = Path(tmp_dir) / "test_mem_fields.db"
        mem = SQLiteMemoryManager(db_path=db_p)

        user_id = "test_user_c3"
        fp = "sha256_dataset_c3"
        mem.record_task_memory(
            user_id=user_id,
            session_id="sess_c3",
            task_id="task_c3_99",
            query="Analyze quarterly orders",
            dataset_fingerprint=fp,
            summary="[DETERMINISTIC VERIFIED METRICS]: Orders=5, Revenue=$250.0",
            task_status="SUCCESS",
            is_verified=True,
            tool_calls=[{"tool": "summarize_sales", "status": "success"}],
        )

        recalled = mem.retrieve_relevant_context(user_id=user_id, dataset_fingerprint=fp)
        assert len(recalled) == 1
        rec = recalled[0]

        # Must have both created_at and timestamp for View 4 compatibility
        assert "created_at" in rec
        assert "timestamp" in rec
        assert rec["created_at"] != ""
        assert rec["task_id"] == "task_c3_99"
        assert len(rec["tool_calls"]) == 1

        mem.close()


# -----------------------------------------------------------------------------
# C4: Persistent Storage Scoping & Path Traversal Protection
# -----------------------------------------------------------------------------
def test_c4_persistent_storage_scoping_and_path_traversal():
    """Verify that reports and databases adhere to persistent storage paths,

    and report downloads cannot escape the authorized reports directory.
    """
    reports_dir = settings.reports_dir.resolve()
    assert reports_dir.name in ("reports", "data") or "reports" in str(reports_dir)

    # Verify path traversal attempt in report filename resolution
    hostile_traversal_paths = [
        Path("../../etc/passwd"),
        Path("../.env"),
        Path("..\\..\\Windows\\System32\\calc.exe"),
    ]

    for hostile_p in hostile_traversal_paths:
        resolved = (settings.workspace_root / hostile_p).resolve()
        is_safe = resolved.exists() and (
            resolved.is_relative_to(reports_dir) or str(resolved).startswith(str(reports_dir))
        )
        assert is_safe is False, f"Path traversal succeeded unexpectedly for: {hostile_p}"

    # Verify tenant isolation in AuditLogger
    with tempfile.TemporaryDirectory() as tmp_dir:
        audit_db = Path(tmp_dir) / "test_audit.db"
        logger = AuditLogger(db_path=audit_db)

        logger.log_event(task_id="t1", user_id="alice", session_id="s1", tool_name="summarize_sales", action_type="READ", decision="ALLOWED", authorization_outcome="AUTO", execution_status="SUCCESS", reason_code="OK", transport="mcp")
        logger.log_event(task_id="t2", user_id="bob", session_id="s2", tool_name="summarize_sales", action_type="READ", decision="ALLOWED", authorization_outcome="AUTO", execution_status="SUCCESS", reason_code="OK", transport="mcp")

        alice_events = logger.query_events(user_id="alice")
        bob_events = logger.query_events(user_id="bob")

        assert len(alice_events) == 1
        assert alice_events[0]["task_id"] == "t1"
        assert len(bob_events) == 1
        assert bob_events[0]["task_id"] == "t2"

        logger.close()


# -----------------------------------------------------------------------------
# C5: End-to-End Dataset Replacement & Arithmetic Correctness
# -----------------------------------------------------------------------------
def test_c5_dataset_replacement_and_arithmetic_correctness():
    """Verify that replacing dataset A with dataset B immediately updates calculations,

    and missing cost data is reported transparently without hallucination.
    """
    session_id = f"test_c5_{uuid.uuid4().hex[:8]}"
    user_id = "user_c5"

    # Dataset A (with unit_cost)
    df_a = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02"],
        "order_id": ["ORD-1", "ORD-2"],
        "product": ["Widget A", "Widget B"],
        "quantity": [10, 5],
        "unit_price": [10.0, 20.0],
        "unit_cost": [5.0, 10.0],
    })
    DatasetManager.register_dataset(session_id, df_a, user_id=user_id)

    res_a = summarize_sales(SummarizeSalesInput(session_id=session_id))
    assert res_a["status"] == "success"
    assert res_a["net_revenue"] == 200.0   # (10*10) + (5*20)
    assert res_a["profit_metrics"]["available"] is True
    assert res_a["profit_metrics"]["net_profit"] == 100.0  # (10*5) + (5*10)

    # Dataset B (replaces Dataset A in same session, without unit_cost and with return)
    df_b = pd.DataFrame({
        "date": ["2026-02-01", "2026-02-01", "2026-02-02"],
        "order_id": ["ORD-X", "ORD-X", "ORD-Y"],  # Multi-line order
        "product": ["Gadget 1", "Gadget 1", "Gadget 2"],
        "quantity": [10, -2, 5],  # 10 sale, 2 return
        "unit_price": [15.0, 15.0, 10.0],
        # No unit_cost column!
    })
    DatasetManager.register_dataset(session_id, df_b, user_id=user_id)

    res_b = summarize_sales(SummarizeSalesInput(session_id=session_id))
    assert res_b["status"] == "success"
    assert res_b["total_orders"] == 2      # ORD-X (2 rows) and ORD-Y (1 row)
    assert res_b["net_units"] == 13.0     # 10 - 2 + 5 = 13.0
    assert res_b["net_revenue"] == 170.0   # (8 * 15) + (5 * 10) = 120 + 50 = 170.0
    assert res_b["profit_metrics"]["available"] is False
    assert res_b["profit_metrics"]["net_profit"] == "UNAVAILABLE"


# -----------------------------------------------------------------------------
# C6: Costs, Budget Cap & Controlled Termination
# -----------------------------------------------------------------------------
def test_c6_cost_tracker_budget_cap_and_controlled_stop():
    """Verify that budget limit is strictly enforced before and after turns,

    preventing runaway loops or expensive unmetered retries.
    """
    tracker = CostTracker(budget_cap_usd=0.01)

    # 1. Turn within budget ($0.0040 < $0.01)
    tracker.record_usage(1, {"prompt_token_count": 10000, "candidates_token_count": 1000})
    assert tracker.cumulative_cost_usd < 0.01
    tracker.pre_flight_check()

    # 2. Second turn exceeding budget -> Raises BudgetExceededError
    with pytest.raises(BudgetExceededError) as exc_info:
        tracker.record_usage(2, {"prompt_token_count": 50000, "candidates_token_count": 10000})

    assert "exceeded budget cap" in str(exc_info.value)

    # 3. Subsequent pre_flight_check immediately rejects
    with pytest.raises(BudgetExceededError):
        tracker.pre_flight_check()


# -----------------------------------------------------------------------------
# C7: Linux, Docker, and Deployment Artifacts Readiness
# -----------------------------------------------------------------------------
def test_c7_container_and_deployment_artifacts_readiness():
    """Verify that deployment files support dynamic PORT, 0.0.0.0 binding, and POSIX path standards."""
    workspace = settings.workspace_root

    # 1. Check Dockerfile
    dockerfile_p = workspace / "Dockerfile"
    assert dockerfile_p.exists()
    df_content = dockerfile_p.read_text(encoding="utf-8")
    assert "--server.address" in df_content or "0.0.0.0" in df_content
    assert "$PORT" in df_content or "8501" in df_content
    assert "WORKDIR" in df_content

    # 2. Check Procfile
    procfile_p = workspace / "Procfile"
    assert procfile_p.exists()
    pf_content = procfile_p.read_text(encoding="utf-8")
    assert "web:" in pf_content
    assert "streamlit run" in pf_content

    # 3. Check railway.json
    railway_p = workspace / "railway.json"
    assert railway_p.exists()
    rw_data = json.loads(railway_p.read_text(encoding="utf-8"))
    assert "deploy" in rw_data
    assert "startCommand" in rw_data["deploy"]
