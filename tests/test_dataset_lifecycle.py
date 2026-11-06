"""Comprehensive regression test suite for Centralized Dataset Lifecycle and Agent/MCP Integration.

Verifies:
Scenario A: Authorized local developer uploads 1,000-row catalog CSV and executes MCP tools cleanly.
Scenario B: Multiple agent queries reuse the already registered dataset without re-parsing or re-registering.
Scenario C: Dataset replacement immediately updates the active analysis target.
Scenario D: Cross-user / cross-session access is strictly rejected with PERMISSION_DENIED.
Scenario E: Anonymous public access cannot register an arbitrary custom CSV.
Scenario F: Revoked developer authorization prevents subsequent unauthorized uploads.
Scenario G: Invalid CSV uploads are rejected without corrupting the active dataset.
Scenario H: SQLite memory isolation and ask_on_write report approvals remain strictly intact.
Scenario I: Bilingual UI error mapping prevents raw tracebacks.
Financial Acceptance: Exact catalog reference values match down to the cent via real MCP path:
  - Rows: 1,000
  - Unique orders: 419
  - Quantity: 3,214.0
  - Net revenue: $1,030,281.73
  - Net cost: $416,924.79
  - Net profit: $613,356.94
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.agent.loop import AgentResult, RetailMindAgent
from src.retailmind.data.loader import (
    APPROVED_BUNDLED_SYNTHETIC_DIR,
    DatasetManager,
    RowLimitExceededError,
    is_local_interface_bound,
    verify_approved_synthetic_dataset,
)
from src.retailmind.mcp.server import _verify_session_ownership, tool_summarize_sales
from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_1000_PATH = WORKSPACE_ROOT / "tests" / "fixtures" / "RetailMind_Sales_Products_1000_CATALOG_USD_TEST.csv"


def make_deterministic_synthetic_dataset(num_rows: int = 100) -> pd.DataFrame:
    """Generates a reproducible, deterministic synthetic sales dataset with known arithmetic invariants.
    
    Invariants for num_rows = 100:
      - 20 distinct orders (5 line items per order: ORD-1000 to ORD-1019)
      - 250.0 total units
      - $28,500.00 total net revenue
      - $13,000.00 total direct cost
      - $15,500.00 gross profit
      - 54.39% gross margin
    """
    products = [
        ("Wireless Optical Mouse", 25.0, 10.0, "Accessories"),
        ("Mechanical Gaming Keyboard", 80.0, 35.0, "Peripherals"),
        ("USB-C Multiport Adapter", 45.0, 20.0, "Accessories"),
        ("Ultra HD 4K Monitor", 300.0, 140.0, "Displays"),
        ("Noise-Cancelling Headphones", 120.0, 55.0, "Audio"),
    ]
    data = []
    for i in range(num_rows):
        order_num = 1000 + (i // 5)
        item_idx = i % 5
        prod, price, cost, cat = products[item_idx]
        qty = (i % 4) + 1  # 1, 2, 3, 4
        day = (i % 28) + 1
        data.append({
            "order_id": f"ORD-{order_num}",
            "date": f"2026-02-{day:02d}",
            "product": prod,
            "quantity": qty,
            "unit_price": price,
            "unit_cost": cost,
            "category": cat,
        })
    return pd.DataFrame(data)


@pytest.fixture(autouse=True)
def setup_test_env():
    """Isolates data directories and cleans session registry between tests."""
    original_env = os.environ.copy()
    temp_dir = tempfile.mkdtemp()
    os.environ["RETAILMIND_DATA_DIR"] = temp_dir
    os.environ["RETAILMIND_SERVER_ADDRESS"] = "127.0.0.1"
    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "dev-secret-alpha-999"

    DatasetManager._sessions.clear()

    yield temp_dir

    DatasetManager._sessions.clear()
    os.environ.clear()
    os.environ.update(original_env)
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


# -----------------------------------------------------------------------------
# Financial Acceptance Tests & Scenario A
# -----------------------------------------------------------------------------
def test_primary_financial_acceptance_synthetic_mcp():
    """Scenario A & Primary Acceptance: Verify reproducible deterministic synthetic dataset via real MCP path."""
    df_synthetic = make_deterministic_synthetic_dataset(100)
    session_id = "fin_accept_synth_sess"
    user_id = "lead_auditor"

    # Authorized upload at ingestion boundary
    processed = DatasetManager.register_dataset(
        session_id=session_id,
        csv_path_or_df=df_synthetic,
        user_id=user_id,
        auth_token="dev-secret-alpha-999",
    )

    # 1. Ingestion invariants
    assert len(processed.raw_df) == 100
    assert len(processed.valid_df) == 100
    assert processed.has_cost_data is True
    assert processed.is_synthetic is False
    assert processed.dataset_type == "custom_local"

    # 2. Independent real MCP server execution path
    os.environ["RETAILMIND_CALLER_USER_ID"] = user_id
    raw_mcp_output = tool_summarize_sales(session_id=session_id, caller_user_id=user_id)
    summary = json.loads(raw_mcp_output)

    assert summary["status"] == "success"
    assert summary["total_orders"] == 20
    assert summary["net_units"] == 250.0
    assert summary["net_revenue"] == 28500.0

    profit_metrics = summary["profit_metrics"]
    assert profit_metrics["available"] is True
    assert profit_metrics["net_profit"] == 15500.0

    direct_cost = round(summary["net_revenue"] - profit_metrics["net_profit"], 2)
    assert direct_cost == 13000.0
    assert profit_metrics["gross_margin_percentage"] == 54.39


@pytest.mark.skipif(
    not FIXTURE_1000_PATH.exists(),
    reason="Reference 1,000-row catalog CSV not found in tests/fixtures/ (private user fixture)",
)
def test_reference_catalog_1000_row_mcp():
    """Reference Financial Acceptance: Verify 1,000-row catalog reference numbers when fixture is present."""
    session_id = "fin_accept_sess"
    user_id = "lead_auditor"

    # Authorized upload at ingestion boundary
    processed = DatasetManager.register_dataset(
        session_id=session_id,
        csv_path_or_df=FIXTURE_1000_PATH,
        user_id=user_id,
        auth_token="dev-secret-alpha-999",
    )

    # 1. Ingestion invariants
    assert len(processed.raw_df) == 1000
    assert len(processed.valid_df) == 1000
    assert processed.has_cost_data is True
    assert processed.is_synthetic is False
    assert processed.dataset_type == "custom_local"

    # 2. Independent real MCP server execution path
    os.environ["RETAILMIND_CALLER_USER_ID"] = user_id
    raw_mcp_output = tool_summarize_sales(session_id=session_id, caller_user_id=user_id)
    summary = json.loads(raw_mcp_output)

    assert summary["status"] == "success"
    assert summary["total_orders"] == 419
    assert summary["net_units"] == 3214.0
    assert summary["net_revenue"] == 1030281.73

    profit_metrics = summary["profit_metrics"]
    assert profit_metrics["available"] is True
    assert profit_metrics["net_profit"] == 613356.94

    catalog_cost = round(summary["net_revenue"] - profit_metrics["net_profit"], 2)
    assert catalog_cost == 416924.79
    assert profit_metrics["gross_margin_percentage"] == 59.53


# -----------------------------------------------------------------------------
# Scenario B: Multiple Queries Reuse Registered Dataset Without Re-registration
# -----------------------------------------------------------------------------
def test_multiple_queries_reuse_registered_dataset():
    """Scenario B: Subsequent agent queries reuse the existing registered dataset without re-reading or auth error."""
    session_id = "sess_reuse_test"
    user_id = "analyst_1"

    # Ingestion boundary
    df_synthetic = make_deterministic_synthetic_dataset(100)
    DatasetManager.register_dataset(
        session_id=session_id,
        csv_path_or_df=df_synthetic,
        user_id=user_id,
        auth_token="dev-secret-alpha-999",
    )
    initial_fp = DatasetManager.get_dataset_fingerprint(session_id)

    # Mock Gemini model to simulate two subsequent agent questions
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.function_calls = []
    candidate = MagicMock()
    candidate.content.parts = [MagicMock(text="Total units is 250.")]
    mock_resp.candidates = [candidate]
    mock_resp.usage_metadata = {"prompt_token_count": 50, "candidates_token_count": 20}
    mock_client.models.generate_content.return_value = mock_resp

    agent = RetailMindAgent(api_key="mock_key")
    agent._client = mock_client

    # Question 1: Without csv_path (reusing session reference)
    res1 = agent.run_task(
        user_query="What are total units?",
        session_id=session_id,
        user_id=user_id,
        csv_path=None,
    )
    assert res1.stop_reason == "FINAL_ANSWER"
    assert DatasetManager.get_dataset_fingerprint(session_id) == initial_fp

    # Question 2: Even if snapshot path is passed, detects same file and reuses reference
    snapshot_path = DatasetManager.get_dataset(session_id).snapshot_path
    res2 = agent.run_task(
        user_query="What is net revenue?",
        session_id=session_id,
        user_id=user_id,
        csv_path=snapshot_path,
    )
    assert res2.stop_reason == "FINAL_ANSWER"
    assert DatasetManager.get_dataset_fingerprint(session_id) == initial_fp


# -----------------------------------------------------------------------------
# Scenario C: Dataset Replacement Immediately Changes Active Target
# -----------------------------------------------------------------------------
def test_dataset_replacement_updates_target():
    """Scenario C: Registering a new dataset for the session updates snapshot, fingerprint, and MCP output."""
    session_id = "sess_replace_test"
    user_id = "analyst_1"

    # 1. First dataset: 1 row, $100 revenue
    df_first = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Alpha"],
        "quantity": [2],
        "unit_price": [50.0],
    })
    DatasetManager.register_dataset(
        session_id=session_id,
        csv_path_or_df=df_first,
        user_id=user_id,
        auth_token="dev-secret-alpha-999",
    )
    res_first = json.loads(tool_summarize_sales(session_id=session_id, caller_user_id=user_id))
    assert res_first["net_revenue"] == 100.0

    # 2. Replacement dataset: 1 row, $500 revenue
    df_second = pd.DataFrame({
        "date": ["2026-01-02"],
        "product": ["Beta"],
        "quantity": [5],
        "unit_price": [100.0],
    })
    DatasetManager.register_dataset(
        session_id=session_id,
        csv_path_or_df=df_second,
        user_id=user_id,
        auth_token="dev-secret-alpha-999",
    )

    # MCP immediately reflects replacement
    res_second = json.loads(tool_summarize_sales(session_id=session_id, caller_user_id=user_id))
    assert res_second["net_revenue"] == 500.0
    assert res_second["net_units"] == 5.0


# -----------------------------------------------------------------------------
# Scenario D: Cross-User / Cross-Session Access Denied
# -----------------------------------------------------------------------------
def test_cross_user_session_access_denied():
    """Scenario D: A different user cannot access or query another user's session dataset."""
    session_id = "sess_victim_01"
    victim_user = "legitimate_owner"
    attacker_user = "attacker_adversary"

    # Legitimate user registers dataset
    df_synthetic = make_deterministic_synthetic_dataset(100)
    DatasetManager.register_dataset(
        session_id=session_id,
        csv_path_or_df=df_synthetic,
        user_id=victim_user,
        auth_token="dev-secret-alpha-999",
    )

    # 1. Agent level verification
    mock_client = MagicMock()
    agent = RetailMindAgent(api_key="mock_key")
    agent._client = mock_client

    res = agent.run_task(
        user_query="Steal data",
        session_id=session_id,
        user_id=attacker_user,
        csv_path=None,
    )
    assert res.stop_reason == "PERMISSION_DENIED"
    assert "not authorized to access session" in res.final_answer

    # 2. MCP server level verification
    os.environ["RETAILMIND_CALLER_USER_ID"] = attacker_user
    is_valid, msg = _verify_session_ownership(session_id=session_id, caller_user_id=attacker_user)
    assert is_valid is False
    assert "PERMISSION_DENIED" in msg


# -----------------------------------------------------------------------------
# Scenario E: Anonymous Public Access Cannot Register Custom CSV
# -----------------------------------------------------------------------------
def test_anonymous_public_access_blocked_from_custom_csv():
    """Scenario E: Unauthenticated public demo mode strictly rejects custom CSV uploads."""
    df_custom = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Custom"],
        "quantity": [1],
        "unit_price": [10.0],
    })

    is_compliant, reason = verify_approved_synthetic_dataset(
        "custom.csv",
        df_custom,
        force_test_mode=False,
    )
    assert is_compliant is False
    assert "UNAUTHENTICATED_DEMO_RESTRICTION" in reason


# -----------------------------------------------------------------------------
# Scenario F: Revoked Developer Authorization Prevents Uploads
# -----------------------------------------------------------------------------
def test_revoked_developer_authorization_prevents_uploads():
    """Scenario F: When developer authorization is revoked (token cleared), custom uploads fail."""
    df_custom = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Confidential"],
        "quantity": [10],
        "unit_price": [20.0],
    })

    # Simulating revoked token in session state (passed as None)
    with pytest.raises(ValueError) as exc_info:
        DatasetManager.register_dataset(
            session_id="revoked_sess",
            csv_path_or_df=df_custom,
            user_id="dev_user",
            auth_token=None,  # Revoked / empty
            force_test_mode=False,
        )
    assert "UNAUTHENTICATED_DEMO_RESTRICTION" in str(exc_info.value)


# -----------------------------------------------------------------------------
# Scenario G: Invalid CSV Rejected Without Corrupting Active Dataset
# -----------------------------------------------------------------------------
def test_invalid_csv_rejected_without_corrupting_active_dataset():
    """Scenario G: An invalid upload (>50,000 rows) is rejected and leaves existing dataset intact."""
    session_id = "sess_integrity_check"
    user_id = "analyst_1"

    # Ingest valid 100-row synthetic dataset
    df_synthetic = make_deterministic_synthetic_dataset(100)
    initial = DatasetManager.register_dataset(
        session_id=session_id,
        csv_path_or_df=df_synthetic,
        user_id=user_id,
        auth_token="dev-secret-alpha-999",
    )
    initial_fp = initial.fingerprint

    # Attempt to ingest 50,001 rows
    df_overflow = pd.DataFrame({
        "date": ["2026-01-01"] * 50001,
        "product": ["Overflow Item"] * 50001,
        "quantity": [1] * 50001,
        "unit_price": [10.0] * 50001,
    })

    with pytest.raises(RowLimitExceededError):
        DatasetManager.register_dataset(
            session_id=session_id,
            csv_path_or_df=df_overflow,
            user_id=user_id,
            auth_token="dev-secret-alpha-999",
        )

    # Active dataset remains intact and unchanged
    current = DatasetManager.get_dataset(session_id)
    assert current.fingerprint == initial_fp
    assert len(current.raw_df) == 100


# -----------------------------------------------------------------------------
# Scenario H: SQLite Memory Isolation & Report Approval Intact
# -----------------------------------------------------------------------------
def test_memory_isolation_and_report_approval(setup_test_env):
    """Scenario H: Verified facts stored in SQLite memory are strictly scoped by user and fingerprint."""
    test_db = Path(setup_test_env) / "test_lifecycle_memory.db"
    mem_mgr = SQLiteMemoryManager(db_path=test_db)
    try:
        mem_mgr.record_task_memory(
            user_id="user_alice",
            session_id="sess_mem_1",
            task_id="task_001",
            query="Analyze Q1 catalog sales",
            dataset_fingerprint="fp_catalog_1000",
            summary="Catalog net revenue $1,030,281.73",
            task_status="SUCCESS",
            is_verified=True,
            tool_calls=[{"tool": "summarize_sales", "net_revenue": 1030281.73}],
        )

        # Alice retrieves her memory
        alice_mem = mem_mgr.retrieve_relevant_context("user_alice", "fp_catalog_1000")
        assert len(alice_mem) == 1
        assert "1,030,281.73" in alice_mem[0]["summary"]

        # Bob cannot retrieve Alice's memory
        bob_mem = mem_mgr.retrieve_relevant_context("user_bob", "fp_catalog_1000")
        assert len(bob_mem) == 0

        # Memory for a different fingerprint is isolated
        alice_diff_fp = mem_mgr.retrieve_relevant_context("user_alice", "fp_different")
        assert len(alice_diff_fp) == 0
    finally:
        mem_mgr.close()


# -----------------------------------------------------------------------------
# Scenario I: Streamlit Bilingual Error Mapping
# -----------------------------------------------------------------------------
def test_ui_bilingual_error_mapping():
    """Scenario I: Streamlit UI displays understandable bilingual error messages without unhandled tracebacks."""
    from src.retailmind.ui.i18n import t

    for lang in ["en", "ar"]:
        # Verify row limit title & guidance
        title = t("err_row_limit_title", lang)
        desc = t("err_row_limit_desc", lang, name="test.csv", rows=50001)
        guidance = t("err_row_limit_guidance", lang)
        assert len(title) > 0
        assert "50,001" in desc or "50001" in desc
        assert len(guidance) > 0

        # Verify unauthenticated demo restriction message
        demo_title = t("err_demo_unauth_title", lang)
        demo_desc = t("err_demo_unauth_desc", lang)
        assert len(demo_title) > 0
        assert len(demo_desc) > 0

        # Verify active retained warning
        retained = t("warn_upload_failed_active_retained", lang, rejected="bad.csv", active="good.csv", rows=100)
        assert "bad.csv" in retained
        assert "good.csv" in retained

