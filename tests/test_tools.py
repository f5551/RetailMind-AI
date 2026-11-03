"""Tests for RetailMind AI Analytical Tools and CSV Ingestion."""

from pathlib import Path
import pytest
import pandas as pd

from src.retailmind.data.loader import DatasetManager, sanitize_cell_value
from src.retailmind.tools.registry import dispatch_tool_call


@pytest.fixture
def sample_csv_path(tmp_path: Path) -> Path:
    """Creates a temporary valid synthetic CSV dataset."""
    csv_file = tmp_path / "sales.csv"
    data = (
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-01,2026-01-05,Wireless Mouse,Electronics,5,20.00,10.00,North\n"
        "ORD-02,2026-01-10,Mechanical Keyboard,Electronics,2,100.00,50.00,South\n"
        "ORD-03,2026-01-15,USB-C Hub,Accessories,10,15.00,5.00,North\n"
        "ORD-04,2026-01-20,Wireless Mouse,Electronics,-1,20.00,10.00,North\n"  # Return
        "ORD-05,2026-02-05,Gaming Headset,Electronics,4,50.00,25.00,South\n"
    )
    csv_file.write_text(data, encoding="utf-8")
    return csv_file


@pytest.fixture
def session_dataset(sample_csv_path: Path) -> str:
    """Registers dataset in DatasetManager under session 'test_sess'."""
    session_id = "test_sess"
    DatasetManager.register_dataset(session_id, sample_csv_path)
    return session_id


def test_formula_sanitization():
    """Verify formula injection characters are prepended with an apostrophe, while numbers are preserved."""
    assert sanitize_cell_value("=1+1") == "'=1+1"
    assert sanitize_cell_value("+cmd|") == "'+cmd|"
    assert sanitize_cell_value("-cmd|calc") == "'-cmd|calc"
    assert sanitize_cell_value("-50") == "-50"  # Valid negative number
    assert sanitize_cell_value("@SUM") == "'@SUM"
    assert sanitize_cell_value("Normal Text") == "Normal Text"


def test_tool_inspect_dataset(session_dataset: str):
    res = dispatch_tool_call("inspect_dataset", {"session_id": session_dataset, "sample_size": 2})
    assert res["status"] == "success"
    assert res["total_rows"] == 5
    assert "product" in res["columns"]
    assert len(res["sample_rows"]) == 2


def test_tool_validate_dataset(session_dataset: str):
    res = dispatch_tool_call("validate_dataset", {"session_id": session_dataset})
    assert res["status"] == "success"
    assert res["is_valid"] is True
    assert res["valid_rows"] == 5
    assert res["quarantined_rows"] == 0
    assert res["has_cost_data"] is True


def test_tool_summarize_sales(session_dataset: str):
    # Total revenue: (5*20) + (2*100) + (10*15) + (-1*20) + (4*50) = 100 + 200 + 150 - 20 + 200 = 630
    # Net units: 5 + 2 + 10 - 1 + 4 = 20
    # Net profit: (5*10) + (2*50) + (10*10) + (-1*10) + (4*25) = 50 + 100 + 100 - 10 + 100 = 340
    res = dispatch_tool_call("summarize_sales", {"session_id": session_dataset})
    assert res["status"] == "success"
    assert res["net_revenue"] == 630.0
    assert res["net_units"] == 20.0
    assert res["profit_metrics"]["available"] is True
    assert res["profit_metrics"]["net_profit"] == 340.0


def test_tool_summarize_sales_without_cost(tmp_path: Path):
    """Verify profit is UNAVAILABLE when unit_cost is missing."""
    csv_file = tmp_path / "no_cost.csv"
    csv_file.write_text(
        "order_id,date,product,quantity,unit_price\n"
        "ORD-01,2026-01-05,Mouse,2,25.00\n",
        encoding="utf-8",
    )
    DatasetManager.register_dataset("sess_no_cost", csv_file)
    res = dispatch_tool_call("summarize_sales", {"session_id": "sess_no_cost"})
    assert res["profit_metrics"]["available"] is False
    assert res["profit_metrics"]["net_profit"] == "UNAVAILABLE"
    assert res["profit_metrics"]["gross_margin_percentage"] == "UNAVAILABLE"


def test_tool_rank_products(session_dataset: str):
    # Product revenues:
    # Keyboard: 200.0 (share 200/630 = 31.75%)
    # Headset: 200.0 (share 200/630 = 31.75%)
    # USB-C Hub: 150.0 (share 150/630 = 23.81%)
    # Mouse: 80.0 (net 4 units, share 80/630 = 12.7%)
    res = dispatch_tool_call("rank_products", {"session_id": session_dataset, "top_n": 3})
    assert res["status"] == "success"
    assert len(res["rankings"]) == 3
    assert res["rankings"][0]["rank"] == 1
    assert res["rankings"][0]["net_revenue"] == 200.0


def test_tool_compare_periods(session_dataset: str):
    res = dispatch_tool_call(
        "compare_periods",
        {
            "session_id": session_dataset,
            "period_a": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "period_b": {"start_date": "2026-02-01", "end_date": "2026-02-28"},
        },
    )
    assert res["status"] == "success"
    assert res["period_a"]["net_revenue"] == 430.0  # 100 + 200 + 150 - 20
    assert res["period_b"]["net_revenue"] == 200.0
    assert res["variance"]["revenue_delta"] == -230.0


def test_tool_detect_anomalies(session_dataset: str):
    res = dispatch_tool_call("detect_anomalies", {"session_id": session_dataset, "method": "zscore", "threshold": 1.5})
    assert res["status"] == "success"
    assert "anomalies" in res


def test_tool_segment_sales(session_dataset: str):
    res = dispatch_tool_call("segment_sales", {"session_id": session_dataset, "dimension": "region"})
    assert res["status"] == "success"
    assert len(res["segments"]) == 2  # North and South
    names = [s["name"] for s in res["segments"]]
    assert "North" in names
    assert "South" in names


def test_tool_generate_report_denial(session_dataset: str):
    """WRITE ACTION without approval must be blocked."""
    res = dispatch_tool_call(
        "generate_report",
        {
            "session_id": session_dataset,
            "title": "Unauthorized Report",
            "sections": [{"heading": "Summary", "content": "Test text"}],
        },
        is_approved=False,
    )
    assert res["status"] == "approval_required"
    assert res["error_code"] == "PERMISSION_DENIED_PENDING_APPROVAL"


def test_tool_generate_report_approval(session_dataset: str):
    """WRITE ACTION with approval must succeed and write file."""
    res = dispatch_tool_call(
        "generate_report",
        {
            "session_id": session_dataset,
            "title": "Approved Executive Report",
            "sections": [
                {
                    "heading": "Overview",
                    "content": "Executive quarterly findings.",
                    "table_data": [{"Metric": "Net Revenue", "Value": "$630.00"}],
                }
            ],
        },
        is_approved=True,
    )
    assert res["status"] == "success"
    assert res["approval_status"] == "APPROVED"
    assert Path(res["file_path"]).exists()
