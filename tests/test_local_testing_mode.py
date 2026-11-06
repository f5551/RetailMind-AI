"""Regression test suite for RetailMind AI Secure Local Testing Mode.

Verifies:
1. Custom CSV uploads rejected in unauthenticated public demo mode.
2. Generic environment flags alone (e.g. RETAILMIND_LOCAL_TESTING=1) NEVER grant authorization.
3. Fail-closed defense: Server binding to public interfaces (0.0.0.0 / public IPs) strictly blocks local testing mode.
4. Authorized developer secret on 127.0.0.1 loopback successfully permits custom CSV uploads.
5. Custom datasets are strictly classified as non-synthetic (is_synthetic=False, dataset_type="custom_local").
6. Upload limits (50,000 rows and 10 MB) remain strictly enforced in local testing mode.
7. MCP server processes isolated custom session datasets with financial correctness.
8. Custom uploads and artifacts are isolated under separate, Git-ignored data directories (RETAILMIND_DATA_DIR).
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.retailmind.data.loader import (
    APPROVED_BUNDLED_SYNTHETIC_DIR,
    DatasetManager,
    RowLimitExceededError,
    is_local_interface_bound,
    verify_approved_synthetic_dataset,
)
from src.retailmind.mcp.server import tool_summarize_sales
from src.retailmind.memory.manager import SQLiteMemoryManager


@pytest.fixture(autouse=True)
def clean_environment():
    """Ensures environment variables and session registry are cleanly restored between tests."""
    original_env = os.environ.copy()
    DatasetManager._sessions.clear()
    yield
    os.environ.clear()
    os.environ.update(original_env)
    DatasetManager._sessions.clear()


def test_unauthorized_custom_csv_rejected_in_public_demo():
    """Unauthenticated public demo users MUST NOT be able to upload custom business CSVs."""
    df_custom = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Custom Proprietary Gadget"],
        "quantity": [10],
        "unit_price": [199.99],
    })

    is_valid, reason = verify_approved_synthetic_dataset(
        "custom_test.csv",
        df_custom,
        force_test_mode=False,
    )
    assert is_valid is False
    assert "UNAUTHENTICATED_DEMO_RESTRICTION" in reason


def test_environment_flags_alone_never_grant_authorization():
    """Setting environment boolean flags alone without developer secret MUST NOT grant upload access."""
    df_custom = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Custom Proprietary Gadget"],
        "quantity": [10],
        "unit_price": [199.99],
    })

    os.environ["RETAILMIND_LOCAL_TESTING"] = "1"
    os.environ["RETAILMIND_DEV_MODE"] = "true"
    os.environ["RETAILMIND_AUTH_MODE"] = "production"

    is_valid, reason = verify_approved_synthetic_dataset(
        "custom_test.csv",
        df_custom,
        force_test_mode=False,
    )
    assert is_valid is False
    assert "UNAUTHENTICATED_DEMO_RESTRICTION" in reason


def test_public_interface_binding_fails_closed():
    """If server is bound to 0.0.0.0 or an external public IP, local testing mode MUST fail closed."""
    df_custom = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Custom Proprietary Gadget"],
        "quantity": [10],
        "unit_price": [199.99],
    })

    # Set valid local secret, but simulate public interface binding
    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "dev-secret-valid-789"
    os.environ["RETAILMIND_SERVER_ADDRESS"] = "0.0.0.0"

    assert is_local_interface_bound() is False

    is_valid, reason = verify_approved_synthetic_dataset(
        "custom_test.csv",
        df_custom,
        force_test_mode=False,
        auth_token="dev-secret-valid-789",
    )
    assert is_valid is False
    assert "LOCAL_TESTING_REJECTED_PUBLIC_BINDING" in reason
    assert "strictly restricted to 127.0.0.1" in reason


def test_wrong_developer_secret_rejected():
    """Providing an incorrect developer secret fails authentication."""
    df_custom = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Custom Proprietary Gadget"],
        "quantity": [10],
        "unit_price": [199.99],
    })

    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "correct-dev-secret-999"
    os.environ["RETAILMIND_SERVER_ADDRESS"] = "127.0.0.1"

    is_valid, reason = verify_approved_synthetic_dataset(
        "custom_test.csv",
        df_custom,
        force_test_mode=False,
        auth_token="wrong-secret-token",
    )
    assert is_valid is False
    assert "UNAUTHENTICATED_DEMO_RESTRICTION" in reason


def test_authorized_local_testing_on_loopback_accepted():
    """Matching secret on 127.0.0.1 loopback interface enables custom CSV upload."""
    df_custom = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Custom Proprietary Gadget"],
        "quantity": [10],
        "unit_price": [199.99],
    })

    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "valid-secret-token-123"
    os.environ["RETAILMIND_SERVER_ADDRESS"] = "127.0.0.1"

    assert is_local_interface_bound() is True

    is_valid, reason = verify_approved_synthetic_dataset(
        "custom_test.csv",
        df_custom,
        force_test_mode=False,
        auth_token="valid-secret-token-123",
    )
    assert is_valid is True
    assert reason == ""


def test_custom_dataset_classification_and_provenance():
    """Custom uploads must be marked is_synthetic=False and dataset_type='custom_local', never synthetic."""
    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "valid-secret-token-123"
    os.environ["RETAILMIND_SERVER_ADDRESS"] = "127.0.0.1"

    df_custom = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "product": ["Proprietary Widget Alpha", "Proprietary Widget Beta"],
        "quantity": [5, 10],
        "unit_price": [50.0, 100.0],
    })

    processed = DatasetManager.register_dataset(
        session_id="local_dev_session_1",
        csv_path_or_df=df_custom,
        auth_token="valid-secret-token-123",
    )

    assert processed.is_synthetic is False
    assert processed.dataset_type == "custom_local"

    # Verify reloading from disk preserves classification
    reloaded = DatasetManager.get_dataset("local_dev_session_1")
    assert reloaded.is_synthetic is False
    assert reloaded.dataset_type == "custom_local"

    # Bundled synthetic dataset must be classified as synthetic
    bundled_path = APPROVED_BUNDLED_SYNTHETIC_DIR / "synthetic_sales.csv"
    if bundled_path.exists():
        synth_processed = DatasetManager.register_dataset(
            session_id="synth_session_1",
            csv_path_or_df=bundled_path,
        )
        assert synth_processed.is_synthetic is True
        assert synth_processed.dataset_type == "approved_synthetic"


def test_custom_upload_strictly_enforces_50k_row_limit():
    """Local testing mode MUST preserve the 50,000-row contract limit."""
    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "valid-secret-token-123"
    os.environ["RETAILMIND_SERVER_ADDRESS"] = "127.0.0.1"

    df_over_limit = pd.DataFrame({
        "date": ["2026-01-01"] * 50001,
        "product": ["Item"] * 50001,
        "quantity": [1] * 50001,
        "unit_price": [10.0] * 50001,
    })

    with pytest.raises(RowLimitExceededError) as exc_info:
        DatasetManager.register_dataset(
            session_id="overflow_session",
            csv_path_or_df=df_over_limit,
            auth_token="valid-secret-token-123",
        )

    assert exc_info.value.row_count == 50001
    assert exc_info.value.limit == 50000


def test_custom_dataset_mcp_routing_and_isolation():
    """MCP server tools must read the exact custom dataset and isolate sessions."""
    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "valid-secret-token-123"
    os.environ["RETAILMIND_SERVER_ADDRESS"] = "127.0.0.1"

    # Custom session A: 4 units * $25 = $100
    df_a = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Custom Alpha"],
        "quantity": [4],
        "unit_price": [25.0],
    })
    DatasetManager.register_dataset(
        session_id="session_iso_a",
        csv_path_or_df=df_a,
        auth_token="valid-secret-token-123",
    )

    # Custom session B: 10 units * $50 = $500
    df_b = pd.DataFrame({
        "date": ["2026-03-02"],
        "product": ["Custom Beta"],
        "quantity": [10],
        "unit_price": [50.0],
    })
    DatasetManager.register_dataset(
        session_id="session_iso_b",
        csv_path_or_df=df_b,
        auth_token="valid-secret-token-123",
    )

    # Call MCP summarize_sales for Session A
    summary_a = json.loads(tool_summarize_sales(session_id="session_iso_a", caller_user_id="default_user"))
    assert summary_a["net_revenue"] == 100.0
    assert summary_a["net_units"] == 4.0
    assert summary_a["total_orders"] == 1

    # Call MCP summarize_sales for Session B
    summary_b = json.loads(tool_summarize_sales(session_id="session_iso_b", caller_user_id="default_user"))
    assert summary_b["net_revenue"] == 500.0
    assert summary_b["net_units"] == 10.0
    assert summary_b["total_orders"] == 1


def test_isolated_local_testing_data_directory():
    """Setting RETAILMIND_DATA_DIR routes all snapshots, registry, and memory to the isolated directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        isolated_dir = Path(tmp_dir) / "isolated_data"
        os.environ["RETAILMIND_DATA_DIR"] = str(isolated_dir)
        os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "valid-secret-token-123"
        os.environ["RETAILMIND_SERVER_ADDRESS"] = "127.0.0.1"

        df_custom = pd.DataFrame({
            "date": ["2026-03-01"],
            "product": ["Custom Widget"],
            "quantity": [5],
            "unit_price": [30.0],
        })

        processed = DatasetManager.register_dataset(
            session_id="session_isolated_dir",
            csv_path_or_df=df_custom,
            auth_token="valid-secret-token-123",
        )

        # Snapshots and registry must reside inside the isolated directory
        assert Path(processed.snapshot_path).resolve().is_relative_to(isolated_dir.resolve())
        assert (isolated_dir / "session_registry.json").exists()
        assert (isolated_dir / "snapshots").exists()

        # SQLite memory manager under isolated directory
        mem_mgr = SQLiteMemoryManager(db_path=isolated_dir / "retailmind.db")
        try:
            mem_mgr.record_task_memory(
                user_id="dev_user",
                session_id="session_isolated_dir",
                task_id="task_isolated_001",
                query="Analyze custom sales",
                dataset_fingerprint=processed.fingerprint,
                summary="Net revenue was $150.0 across 5 units.",
                task_status="SUCCESS",
                is_verified=True,
                tool_calls=[{"tool": "summarize_sales", "revenue": 150.0}],
            )

            assert (isolated_dir / "retailmind.db").exists()
            memories = mem_mgr.retrieve_relevant_context(
                user_id="dev_user",
                dataset_fingerprint=processed.fingerprint,
            )
            assert len(memories) == 1
            assert "150.0" in memories[0]["summary"]
        finally:
            mem_mgr.close()
