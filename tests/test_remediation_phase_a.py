"""RetailMind AI — Phase A Remediation Regression Test Suite.

Verifies fixes for the four critical defects identified in the independent audit:
- FIX A1 (RM-01): Uploaded CSV / DataFrame synchronization with MCP subprocess.
- FIX A2 (RM-02): Multi-tenant isolation for user identities, audit logs, and memories.
- FIX A3 (RM-03): Session ownership enforcement and cross-tenant access denial across all 8 tools.
- FIX A4 (RM-04): Non-finite numeric quarantine (NaN/Inf) while preserving legitimate negative return quantities.
"""

import asyncio
import io
import math
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import pytest

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.audit.logger import AuditLogger
from src.retailmind.config import settings
from src.retailmind.data.loader import DatasetManager
from src.retailmind.mcp.client import RetailMindMCPClient
from src.retailmind.memory.manager import SQLiteMemoryManager
from src.retailmind.tools.registry import dispatch_tool_call


# -----------------------------------------------------------------------------
# FIX A1 (RM-01): Uploaded CSV / DataFrame Cross-Process Synchronization
# -----------------------------------------------------------------------------
def test_a1_uploaded_dataframe_synced_to_mcp_subprocess():
    """Verify that an in-memory uploaded DataFrame is persisted and accessible

    by the standalone MCP subprocess over stdio transport.
    """
    session_id = f"test_a1_{uuid.uuid4().hex[:8]}"
    user_id = f"user_{uuid.uuid4().hex[:8]}"

    # 1. Dataset A: Small sales (Total revenue: 10 * 1.0 = $10.00)
    df_a = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Item Alpha"],
        "quantity": [10],
        "unit_price": [1.0],
        "category": ["A"],
        "region": ["North"],
    })
    DatasetManager.register_dataset(session_id, df_a, user_id=user_id)

    # 2. Overwrite / update session with Dataset B (Total revenue: 5 * 199.8 = $999.00)
    df_b = pd.DataFrame({
        "date": ["2026-02-01"],
        "product": ["Item Beta"],
        "quantity": [5],
        "unit_price": [199.8],
        "category": ["B"],
        "region": ["South"],
    })
    processed_b = DatasetManager.register_dataset(session_id, df_b, user_id=user_id)
    assert processed_b.snapshot_path is not None
    assert Path(processed_b.snapshot_path).exists()

    # 3. Query through MCP client (spawns separate Python subprocess)
    async def query_mcp():
        client = RetailMindMCPClient(caller_user_id=user_id)
        async with client:
            obs = await client.call_tool("summarize_sales", {"session_id": session_id})
            return obs

    mcp_result = asyncio.run(query_mcp())

    assert mcp_result.get("status") == "success"
    # Net revenue must match Dataset B ($999.00), not Dataset A ($10.00)
    assert mcp_result["net_revenue"] == 999.0
    assert mcp_result["net_units"] == 5


def test_a1_direct_upload_without_previous_dataset():
    """Verify that uploading a DataFrame directly without prior registrations

    works immediately across processes.
    """
    session_id = f"test_a1_direct_{uuid.uuid4().hex[:8]}"
    user_id = f"user_{uuid.uuid4().hex[:8]}"

    df = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Widget Prime"],
        "quantity": [20],
        "unit_price": [15.5],
    })
    DatasetManager.register_dataset(session_id, df, user_id=user_id)

    async def query_mcp():
        client = RetailMindMCPClient(caller_user_id=user_id)
        async with client:
            return await client.call_tool("summarize_sales", {"session_id": session_id})

    res = asyncio.run(query_mcp())
    assert res.get("status") == "success"
    assert res["net_revenue"] == 310.0
    assert res["net_units"] == 20


# -----------------------------------------------------------------------------
# FIX A2 (RM-02): Multi-Tenant User Isolation (Audit Logs & Memories)
# -----------------------------------------------------------------------------
def test_a2_multi_tenant_audit_and_memory_isolation():
    """Verify that User 1 and User 2 have strictly partitioned audit logs

    and persistent SQLite memories.
    """
    user_1 = f"tenant_1_{uuid.uuid4().hex[:8]}"
    user_2 = f"tenant_2_{uuid.uuid4().hex[:8]}"
    session_1 = f"sess_1_{uuid.uuid4().hex[:8]}"
    session_2 = f"sess_2_{uuid.uuid4().hex[:8]}"

    audit_logger = AuditLogger.get_default_logger()
    memory_manager = SQLiteMemoryManager()

    # User 1 logs audit events
    audit_logger.log_event(
        task_id="task_u1_a",
        user_id=user_1,
        session_id=session_1,
        tool_name="summarize_sales",
        action_type="READ",
        decision="ALLOWED",
        authorization_outcome="AUTHORIZED",
        execution_status="SUCCESS",
        reason_code="TEST_USER_1",
    )
    # User 2 logs audit events
    audit_logger.log_event(
        task_id="task_u2_b",
        user_id=user_2,
        session_id=session_2,
        tool_name="rank_products",
        action_type="READ",
        decision="ALLOWED",
        authorization_outcome="AUTHORIZED",
        execution_status="SUCCESS",
        reason_code="TEST_USER_2",
    )

    # Query filtered by user_id
    u1_events = audit_logger.query_events(user_id=user_1)
    u2_events = audit_logger.query_events(user_id=user_2)

    assert len(u1_events) >= 1
    assert all(e["user_id"] == user_1 for e in u1_events)
    assert not any(e["user_id"] == user_2 for e in u1_events)

    assert len(u2_events) >= 1
    assert all(e["user_id"] == user_2 for e in u2_events)
    assert not any(e["user_id"] == user_1 for e in u2_events)

    # User 1 records memory
    fp = "fingerprint_shared_schema"
    memory_manager.record_task_memory(
        user_id=user_1,
        session_id=session_1,
        task_id="mem_task_1",
        query="What is User 1 revenue?",
        dataset_fingerprint=fp,
        summary="User 1 private revenue is $5,000.",
        task_status="SUCCESS",
        is_verified=True,
    )

    # User 2 attempts to retrieve memory for the same dataset
    u2_memories = memory_manager.retrieve_relevant_context(user_id=user_2, dataset_fingerprint=fp)
    assert len(u2_memories) == 0

    # User 1 can retrieve their memory
    u1_memories = memory_manager.retrieve_relevant_context(user_id=user_1, dataset_fingerprint=fp)
    assert len(u1_memories) == 1
    assert "User 1 private revenue" in u1_memories[0]["summary"]


# -----------------------------------------------------------------------------
# FIX A3 (RM-03): Cross-Tenant Tool Execution Denial Across All 8 Tools
# -----------------------------------------------------------------------------
def test_a3_cross_tenant_denial_across_all_8_tools_direct_dispatcher():
    """Verify that User A cannot execute any of the 8 tools against User B's session

    via the direct dispatcher.
    """
    user_a = f"alice_{uuid.uuid4().hex[:6]}"
    user_b = f"bob_{uuid.uuid4().hex[:6]}"
    session_b = f"sess_bob_{uuid.uuid4().hex[:6]}"

    df_b = pd.DataFrame({
        "date": ["2026-01-01", "2026-02-01"],
        "product": ["Secret Product B", "Secret Product B2"],
        "quantity": [10, 20],
        "unit_price": [100.0, 50.0],
        "unit_cost": [40.0, 20.0],
        "category": ["Confidential", "Confidential"],
        "region": ["HQ", "HQ"],
    })
    DatasetManager.register_dataset(session_b, df_b, user_id=user_b)

    tools_to_test = [
        ("inspect_dataset", {"session_id": session_b}),
        ("validate_dataset", {"session_id": session_b}),
        ("summarize_sales", {"session_id": session_b}),
        ("rank_products", {"session_id": session_b, "by": "revenue", "limit": 5}),
        (
            "compare_periods",
            {
                "session_id": session_b,
                "period_a_start": "2026-01-01",
                "period_a_end": "2026-01-15",
                "period_b_start": "2026-02-01",
                "period_b_end": "2026-02-15",
            },
        ),
        ("detect_anomalies", {"session_id": session_b}),
        ("segment_sales", {"session_id": session_b, "dimension": "category"}),
        ("generate_report", {"session_id": session_b, "title": "Infiltrated Report", "sections": ["Summary"]}),
    ]

    for tool_name, args in tools_to_test:
        # User A calls tool targeting Bob's session
        res = dispatch_tool_call(tool_name, args, is_approved=True, caller_user_id=user_a)
        assert res.get("status") == "error", f"Tool {tool_name} was not rejected for unauthorized caller!"
        assert res.get("error_code") == "PERMISSION_DENIED", f"Tool {tool_name} returned wrong error code: {res}"
        assert f"Access to session '{session_b}' is not authorized for caller '{user_a}'" in res.get("message", "")


def test_a3_cross_tenant_denial_mcp_subprocess():
    """Verify that User A cannot execute tools against User B's session

    over the real MCP subprocess.
    """
    user_a = f"alice_{uuid.uuid4().hex[:6]}"
    user_b = f"bob_{uuid.uuid4().hex[:6]}"
    session_b = f"sess_bob_mcp_{uuid.uuid4().hex[:6]}"

    df_b = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Vault Asset"],
        "quantity": [1],
        "unit_price": [1000.0],
    })
    DatasetManager.register_dataset(session_b, df_b, user_id=user_b)

    async def query_mcp_cross_tenant():
        # MCP client running as Alice
        client = RetailMindMCPClient(caller_user_id=user_a)
        async with client:
            return await client.call_tool("summarize_sales", {"session_id": session_b})

    res = asyncio.run(query_mcp_cross_tenant())
    assert res.get("status") == "error"
    assert res.get("error_code") == "PERMISSION_DENIED"
    assert f"Access to session '{session_b}' is not authorized for caller '{user_a}'" in res.get("message", "")


# -----------------------------------------------------------------------------
# FIX A4 (RM-04): Non-Finite Numeric Quarantine & Math Integrity
# -----------------------------------------------------------------------------
def test_a4_quarantine_nan_and_infinity_preserving_negative_returns():
    """Verify that NaN, Infinity, and -Infinity values in quantity, unit_price,

    and unit_cost are quarantined under NON_FINITE_NUMERIC, while legitimate
    negative return quantities (e.g. -2) are preserved in valid_df.
    """
    session_id = f"sess_a4_{uuid.uuid4().hex[:6]}"
    user_id = f"user_{uuid.uuid4().hex[:6]}"

    csv_data = """date,product,quantity,unit_price,unit_cost
2026-01-01,Valid Normal,10,25.00,10.00
2026-01-02,Valid Return,-2,25.00,10.00
2026-01-03,Bad Price NaN,5,NaN,10.00
2026-01-04,Bad Price Inf,5,Infinity,10.00
2026-01-05,Bad Price NegInf,5,-Infinity,10.00
2026-01-06,Bad Quantity NaN,NaN,25.00,10.00
2026-01-07,Bad Quantity Inf,Infinity,25.00,10.00
2026-01-08,Bad Cost NegInf,4,20.00,-Infinity
2026-01-09,Bad Cost Inf,4,20.00,Infinity
2026-01-10,Valid Other,3,15.00,5.00
"""
    raw_df = pd.read_csv(io.StringIO(csv_data))
    processed = DatasetManager.register_dataset(session_id, raw_df, user_id=user_id)

    # 1. Check valid rows count: exactly 3 rows (Valid Normal, Valid Return, Valid Other)
    assert len(processed.valid_df) == 3, f"Expected 3 valid rows, got {len(processed.valid_df)}"

    # 2. Check quarantined rows count: exactly 7 bad rows
    assert len(processed.quarantined_df) == 7, f"Expected 7 quarantined rows, got {len(processed.quarantined_df)}"

    # 3. Check quarantine reason codes
    reasons = {issue.issue_type for issue in processed.issues}
    assert "NON_FINITE_NUMERIC" in reasons

    # 4. Check that Valid Return is preserved in valid_df
    return_row = processed.valid_df[processed.valid_df["product"] == "Valid Return"]
    assert len(return_row) == 1
    assert return_row.iloc[0]["quantity"] == -2
    assert return_row.iloc[0]["line_revenue"] == -50.0  # -2 * 25.00
    assert return_row.iloc[0]["line_profit"] == -30.0   # -50 - (-2 * 10)

    # 5. Check calculation results in summarize_sales
    summary = dispatch_tool_call("summarize_sales", {"session_id": session_id}, caller_user_id=user_id)
    assert summary["status"] == "success"
    # Net units: 10 + (-2) + 3 = 11
    assert summary["net_units"] == 11
    # Net revenue: 250.00 + (-50.00) + 45.00 = 245.00
    assert summary["net_revenue"] == 245.0
    # Net profit: 150.00 + (-30.00) + 30.00 = 150.00
    assert summary["profit_metrics"]["net_profit"] == 150.0
    # All values must be finite floats
    assert math.isfinite(summary["net_revenue"])
    assert math.isfinite(summary["profit_metrics"]["net_profit"])
    assert math.isfinite(summary["profit_metrics"]["gross_margin_percentage"])
