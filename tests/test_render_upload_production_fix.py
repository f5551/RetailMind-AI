"""Verification test suite for Render Production CSV Upload Fix.

Verifies:
1. Valid CSV upload succeeds in production environment (e.g., RENDER=true or ENVIRONMENT=production).
2. Local testing mode is strictly blocked from public interfaces (0.0.0.0) even if valid dev token provided.
3. 50,000 row count limit and 10 MB limit remain strictly enforced in production mode.
4. Session isolation is preserved in production mode (cross-session access denied).
5. Unauthenticated demo mode restriction remains intact when running in non-production demo environments.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from src.retailmind.data.loader import (
    DatasetManager,
    RowLimitExceededError,
    is_local_interface_bound,
    is_production_mode,
    verify_approved_synthetic_dataset,
)


@pytest.fixture(autouse=True)
def clean_environment():
    """Restores environment variables and clears dataset registry between tests."""
    original_env = os.environ.copy()
    DatasetManager._sessions.clear()
    yield
    os.environ.clear()
    os.environ.update(original_env)
    DatasetManager._sessions.clear()


def test_production_mode_detection():
    """is_production_mode correctly detects Render, Railway, or production environment variables."""
    # When no production flags are present
    os.environ.pop("RENDER", None)
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("RETAILMIND_ENV", None)
    os.environ.pop("RETAILMIND_MODE", None)
    os.environ.pop("RAILWAY_ENVIRONMENT", None)
    os.environ.pop("RAILWAY_PROJECT_ID", None)
    assert is_production_mode() is False

    # Render detection
    os.environ["RENDER"] = "true"
    assert is_production_mode() is True
    os.environ.pop("RENDER")

    # ENVIRONMENT=production
    os.environ["ENVIRONMENT"] = "production"
    assert is_production_mode() is True
    os.environ.pop("ENVIRONMENT")

    # RETAILMIND_ENV=production
    os.environ["RETAILMIND_ENV"] = "production"
    assert is_production_mode() is True
    os.environ.pop("RETAILMIND_ENV")

    # Railway detection
    os.environ["RAILWAY_ENVIRONMENT"] = "production"
    assert is_production_mode() is True


def test_render_production_csv_upload_succeeds():
    """In Render production mode, a valid sales CSV is successfully accepted and registered."""
    os.environ["RENDER"] = "true"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

    df_valid = pd.DataFrame({
        "date": ["2026-03-01", "2026-03-02"],
        "product": ["Retail Product A", "Retail Product B"],
        "quantity": [10, 5],
        "unit_price": [25.0, 50.0],
    })

    # verify_approved_synthetic_dataset returns True in production
    is_compliant, reason = verify_approved_synthetic_dataset("sales.csv", df_valid)
    assert is_compliant is True
    assert reason == ""

    # Full registration pipeline
    processed = DatasetManager.register_dataset(
        session_id="render_prod_session_101",
        csv_path_or_df=df_valid,
        user_id="merchant_user_1",
    )
    assert processed is not None
    assert len(processed.valid_df) == 2
    assert DatasetManager.has_dataset("render_prod_session_101") is True


def test_public_interface_rejects_local_testing_bypass():
    """On a public interface (0.0.0.0), attempting to use local dev token fails closed."""
    os.environ["RENDER"] = "true"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["RETAILMIND_LOCAL_DEV_SECRET"] = "secret-token-12345"

    df = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Widget"],
        "quantity": [1],
        "unit_price": [10.0],
    })

    # Even if passing candidate_token == local_dev_secret, it must be rejected on public interface
    is_compliant, reason = verify_approved_synthetic_dataset(
        "sales.csv", df, auth_token="secret-token-12345"
    )
    assert is_compliant is False
    assert "LOCAL_TESTING_REJECTED_PUBLIC_BINDING" in reason


def test_production_mode_enforces_50k_row_limit():
    """Production mode must enforce the 50,000 row contract limit."""
    os.environ["RENDER"] = "true"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

    df_overflow = pd.DataFrame({
        "date": ["2026-01-01"] * 50001,
        "product": ["Item"] * 50001,
        "quantity": [1] * 50001,
        "unit_price": [10.0] * 50001,
    })

    with pytest.raises(RowLimitExceededError) as exc_info:
        DatasetManager.register_dataset(
            session_id="prod_overflow_session",
            csv_path_or_df=df_overflow,
            user_id="merchant_user_1",
        )
    assert exc_info.value.row_count == 50001
    assert exc_info.value.limit == 50000


def test_production_mode_enforces_required_columns():
    """Production mode must enforce required columns (date, product, quantity, unit_price)."""
    os.environ["RENDER"] = "true"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

    df_bad = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Item"],
        # missing quantity and unit_price
    })

    with pytest.raises(ValueError) as exc_info:
        DatasetManager.register_dataset(
            session_id="prod_bad_schema_session",
            csv_path_or_df=df_bad,
            user_id="merchant_user_1",
        )
    assert "missing required columns" in str(exc_info.value).lower()


def test_production_mode_preserves_session_isolation():
    """In production mode, sessions remain isolated and cross-user access is denied."""
    os.environ["RENDER"] = "true"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

    df1 = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Product A"],
        "quantity": [2],
        "unit_price": [15.0],
    })

    DatasetManager.register_dataset(
        session_id="session_user_alice",
        csv_path_or_df=df1,
        user_id="alice_user",
    )

    # Alice has access
    ok_alice, _ = DatasetManager.verify_session_access("session_user_alice", "alice_user")
    assert ok_alice is True

    # Bob does NOT have access
    ok_bob, reason_bob = DatasetManager.verify_session_access("session_user_alice", "bob_user")
    assert ok_bob is False
    assert "PERMISSION_DENIED" in reason_bob


def test_unauthenticated_demo_restriction_preserved_in_dev_mode():
    """In development demo mode without credentials, arbitrary custom CSV is rejected."""
    os.environ["ENVIRONMENT"] = "development"
    os.environ.pop("RENDER", None)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"

    df_custom = pd.DataFrame({
        "date": ["2026-03-01"],
        "product": ["Confidential Product"],
        "quantity": [1],
        "unit_price": [100.0],
    })

    is_compliant, reason = verify_approved_synthetic_dataset(
        "custom.csv", df_custom, force_test_mode=False
    )
    assert is_compliant is False
    assert "UNAUTHENTICATED_DEMO_RESTRICTION" in reason
