"""RetailMind AI — Regression Test Suite: 50,000 Row Limit & Dataset Isolation Integrity.

Verifies:
1. Valid 50,000-row dataset is accepted without error.
2. Rejected 50,001-row dataset raises RowLimitExceededError with accurate row count.
3. Rejected upload never replaces or mutates active session dataset, snapshot, or registry.
4. Rejected upload never pollutes or alters SQLite analytical memory.
5. UI i18n translation keys exist and interpolate correctly in English and Arabic.
"""

from pathlib import Path
import pandas as pd
import pytest

from src.retailmind.data.loader import (
    DatasetManager,
    RowLimitExceededError,
)
from src.retailmind.memory.manager import SQLiteMemoryManager
from src.retailmind.ui.i18n import TRANSLATIONS, t


@pytest.fixture
def synthetic_50k_df() -> pd.DataFrame:
    """Generates a synthetic DataFrame with exactly 50,000 valid rows."""
    n = 50000
    return pd.DataFrame({
        "date": ["2026-01-15"] * n,
        "product": ["Wireless Mouse"] * n,
        "quantity": [1] * n,
        "unit_price": [25.0] * n,
        "unit_cost": [12.5] * n,
        "category": ["Electronics"] * n,
        "region": ["North"] * n,
        "order_id": [f"ORD-{i:06d}" for i in range(n)],
    })


@pytest.fixture
def synthetic_50001_df() -> pd.DataFrame:
    """Generates a synthetic DataFrame with exactly 50,001 rows (exceeding limit by 1)."""
    n = 50001
    return pd.DataFrame({
        "date": ["2026-01-15"] * n,
        "product": ["Wireless Mouse"] * n,
        "quantity": [1] * n,
        "unit_price": [25.0] * n,
        "unit_cost": [12.5] * n,
        "category": ["Electronics"] * n,
        "region": ["North"] * n,
        "order_id": [f"ORD-{i:06d}" for i in range(n)],
    })


def test_row_limit_exact_50000_rows_accepted(synthetic_50k_df):
    """Test 1: Verify that a valid dataset with exactly 50,000 rows is accepted."""
    session_id = "test_sess_50000_valid"
    user_id = "user_test_50k"

    processed = DatasetManager.register_dataset(session_id, synthetic_50k_df, user_id=user_id)

    assert processed is not None
    assert len(processed.raw_df) == 50000
    assert len(processed.valid_df) == 50000
    assert len(processed.quarantined_df) == 0
    assert processed.snapshot_path is not None
    assert Path(processed.snapshot_path).exists()

    # Verify retrieval from cache and cross-process registry
    retrieved = DatasetManager.get_dataset(session_id)
    assert len(retrieved.raw_df) == 50000
    assert retrieved.fingerprint == processed.fingerprint


def test_row_limit_50001_rows_rejected_with_custom_exception(synthetic_50001_df):
    """Test 2: Verify that a dataset with 50,001 rows is rejected with RowLimitExceededError."""
    session_id = "test_sess_50001_rejected"
    user_id = "user_test_50001"

    with pytest.raises(RowLimitExceededError) as exc_info:
        DatasetManager.register_dataset(session_id, synthetic_50001_df, user_id=user_id)

    err = exc_info.value
    assert isinstance(err, ValueError)
    assert err.row_count == 50001
    assert err.limit == 50000
    assert "50,000" in str(err)
    assert "50,001" in str(err)

    # Verify that session was NEVER registered in DatasetManager
    assert session_id not in DatasetManager._sessions
    entry = DatasetManager._load_registry_entry(session_id)
    assert entry is None


def test_rejected_upload_never_modifies_active_dataset_or_registry(synthetic_50001_df):
    """Test 3: Confirm that a rejected upload NEVER replaces or mutates the active dataset."""
    session_id = "test_sess_active_dataset_protection"
    user_id = "user_active_protection"

    # Step A: Register initial valid dataset (15 rows)
    initial_csv = Path(__file__).resolve().parent.parent / "sample_data" / "synthetic_sales.csv"
    initial_processed = DatasetManager.register_dataset(session_id, initial_csv, user_id=user_id)
    initial_fp = initial_processed.fingerprint
    initial_snapshot_path = Path(initial_processed.snapshot_path)
    initial_snapshot_bytes = initial_snapshot_path.read_bytes()
    initial_registry = DatasetManager._load_registry_entry(session_id)

    assert len(initial_processed.raw_df) == 15

    # Step B: Attempt to upload 50,001-row dataset to the same session
    with pytest.raises(RowLimitExceededError):
        DatasetManager.register_dataset(session_id, synthetic_50001_df, user_id=user_id)

    # Step C: Verify active dataset remains 100% identical and uncorrupted
    active_dataset = DatasetManager.get_dataset(session_id)
    assert len(active_dataset.raw_df) == 15
    assert len(active_dataset.valid_df) == 15
    assert active_dataset.fingerprint == initial_fp

    # Step D: Verify snapshot file on disk was not overwritten
    current_snapshot_bytes = initial_snapshot_path.read_bytes()
    assert current_snapshot_bytes == initial_snapshot_bytes

    # Step E: Verify registry entry was not modified
    current_registry = DatasetManager._load_registry_entry(session_id)
    assert current_registry["fingerprint"] == initial_registry["fingerprint"]
    assert current_registry["updated_at"] == initial_registry["updated_at"]


def test_rejected_upload_never_modifies_sqlite_memory(tmp_path, synthetic_50001_df):
    """Test 4: Confirm that SQLite analytical memory is completely untouched by a rejected upload."""
    db_file = tmp_path / "memory_isolation_test.db"
    mem_mgr = SQLiteMemoryManager(db_path=db_file)

    user_id = "user_mem_test"
    session_id = "sess_mem_test"
    active_fp = "active_fingerprint_abc123"

    # Save a verified analytical memory finding
    mem_mgr.record_task_memory(
        user_id=user_id,
        session_id=session_id,
        task_id="task_mem_001",
        query="What was our total net revenue?",
        dataset_fingerprint=active_fp,
        summary="Total net revenue was $2,945.00 across 15 orders.",
        task_status="SUCCESS",
        is_verified=True,
        tool_calls=[{"name": "summarize_sales", "status": "success"}],
    )

    # Verify memory exists
    records_before = mem_mgr.retrieve_relevant_context(user_id=user_id, dataset_fingerprint=active_fp)
    assert len(records_before) == 1

    # Attempt to upload 50,001-row dataset
    with pytest.raises(RowLimitExceededError):
        DatasetManager.register_dataset(session_id, synthetic_50001_df, user_id=user_id)

    # Verify memory records are completely unchanged
    records_after = mem_mgr.retrieve_relevant_context(user_id=user_id, dataset_fingerprint=active_fp)
    assert len(records_after) == 1
    assert records_after[0]["task_id"] == "task_mem_001"

    # Query with any dummy fingerprint should return 0
    records_other = mem_mgr.retrieve_relevant_context(user_id=user_id, dataset_fingerprint="unknown_rejected_fp")
    assert len(records_other) == 0

    mem_mgr.close()


def test_bilingual_row_limit_and_active_dataset_ui_keys():
    """Test 5: Verify all new UI keys for row limits and active dataset exist and format correctly."""
    required_keys = [
        "audit_summary_active_title",
        "active_dataset_banner",
        "warn_upload_failed_active_retained",
        "err_row_limit_title",
        "err_row_limit_desc",
        "err_row_limit_guidance",
        "err_row_limit_active_note",
    ]

    for key in required_keys:
        assert key in TRANSLATIONS, f"Missing translation key: {key}"
        assert "en" in TRANSLATIONS[key], f"Missing English for {key}"
        assert "ar" in TRANSLATIONS[key], f"Missing Arabic for {key}"
        assert len(TRANSLATIONS[key]["en"]) > 0
        assert len(TRANSLATIONS[key]["ar"]) > 0

    # Test parameter interpolation in English and Arabic
    en_desc = t("err_row_limit_desc", "en", name="Sales.csv", rows=55000)
    ar_desc = t("err_row_limit_desc", "ar", name="Sales.csv", rows=55000)
    assert "Sales.csv" in en_desc and "55,000" in en_desc and "50,000" in en_desc
    assert "Sales.csv" in ar_desc and "55,000" in ar_desc and "50,000" in ar_desc

    en_warn = t("warn_upload_failed_active_retained", "en", rejected="Sales.csv", active="synthetic_sales.csv", rows=15)
    ar_warn = t("warn_upload_failed_active_retained", "ar", rejected="Sales.csv", active="synthetic_sales.csv", rows=15)
    assert "Sales.csv" in en_warn and "synthetic_sales.csv" in en_warn
    assert "Sales.csv" in ar_warn and "synthetic_sales.csv" in ar_warn

    en_banner = t("active_dataset_banner", "en", name="synthetic_sales.csv", rows=15)
    ar_banner = t("active_dataset_banner", "ar", name="synthetic_sales.csv", rows=15)
    assert "synthetic_sales.csv" in en_banner and "15" in en_banner
    assert "synthetic_sales.csv" in ar_banner and "15" in ar_banner
