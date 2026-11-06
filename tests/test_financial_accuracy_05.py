"""RetailMind AI — Financial Accuracy & Mathematical Integrity Test Suite (Task 05).

Provides rigorous, independent ground-truth verification of:
1. Net Revenue, Total Cost, Net Profit, Gross Margin on synthetic_sales.csv.
2. Multi-unit orders and distinct order counting (3 units != 3 orders).
3. Multi-line orders sharing identical order_id.
4. Dynamic/differing transaction prices (no catalog override).
5. Missing cost data policy (net_profit and gross_margin strictly UNAVAILABLE).
6. Period comparison variance (deltas, growth percentages).
7. Zero-baseline previous period (no growth percentage hallucinated).
8. Return transactions with negative quantities.
9. Dashboard compute_period_metrics parity with MCP tool calculations.
10. Edge case comparison: missing order_id handling.
"""

from pathlib import Path
import math
import pytest
import pandas as pd

from src.retailmind.data.loader import DatasetManager, ProcessedDataset
from src.retailmind.tools.registry import dispatch_tool_call
from src.retailmind.tools.implementations import count_distinct_orders
from app import compute_period_metrics


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Ensures test session datasets are isolated and cleaned up."""
    yield
    for sess in ["fin_sess_baseline", "fin_sess_no_cost", "fin_sess_multi_unit", "fin_sess_zero_base", "fin_sess_returns"]:
        DatasetManager.clear_session(sess)


# -----------------------------------------------------------------------------
# Test 1: Ground Truth vs summarize_sales on synthetic_sales.csv
# -----------------------------------------------------------------------------
def test_financial_accuracy_synthetic_sales_baseline():
    """Verify exact revenue, cost, profit, margin, units, orders on bundled synthetic_sales.csv."""
    csv_path = Path("sample_data/synthetic_sales.csv")
    assert csv_path.exists()

    # Independent ground truth via pure Pandas
    df_raw = pd.read_csv(csv_path)
    expected_orders = int(df_raw["order_id"].nunique())
    expected_units = float(df_raw["quantity"].sum())
    expected_rev = float((df_raw["quantity"] * df_raw["unit_price"]).sum())
    expected_cost = float((df_raw["quantity"] * df_raw["unit_cost"]).sum())
    expected_profit = round(expected_rev - expected_cost, 2)
    expected_margin = round((expected_profit / expected_rev) * 100.0, 2)

    assert expected_orders == 15
    assert expected_units == 87.0
    assert abs(expected_rev - 2945.00) < 1e-4
    assert abs(expected_cost - 1419.50) < 1e-4
    assert abs(expected_profit - 1525.50) < 1e-4
    assert abs(expected_margin - 51.80) < 1e-4

    # Register in DatasetManager
    session_id = "fin_sess_baseline"
    DatasetManager.register_dataset(session_id, csv_path, force_test_mode=True)

    # Call MCP summarize_sales
    mcp_res = dispatch_tool_call("summarize_sales", {"session_id": session_id})
    assert mcp_res["status"] == "success"
    assert mcp_res["total_orders"] == expected_orders
    assert mcp_res["net_units"] == expected_units
    assert mcp_res["net_revenue"] == round(expected_rev, 2)
    assert mcp_res["profit_metrics"]["available"] is True
    assert mcp_res["profit_metrics"]["net_profit"] == expected_profit
    assert mcp_res["profit_metrics"]["gross_margin_percentage"] == expected_margin

    # Verify Dashboard compute_period_metrics parity
    ds = DatasetManager.get_dataset(session_id)
    dash_metrics = compute_period_metrics(ds.valid_df, has_cost=ds.has_cost_data)
    assert dash_metrics["total_orders"] == expected_orders
    assert dash_metrics["total_units"] == int(expected_units)
    assert round(dash_metrics["net_revenue"], 2) == round(expected_rev, 2)
    assert round(dash_metrics["net_profit"], 2) == expected_profit
    assert round(dash_metrics["margin_pct"], 2) == expected_margin
    assert round(dash_metrics["total_cost"], 2) == round(expected_cost, 2)


# -----------------------------------------------------------------------------
# Test 2: Order with 3 units must NOT be counted as 3 orders
# -----------------------------------------------------------------------------
def test_distinct_order_counting_multi_unit_single_row(tmp_path: Path):
    """An order with 3 units in 1 row must be counted as 1 order and 3 units."""
    csv_file = tmp_path / "single_row_3units.csv"
    csv_file.write_text(
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-501,2026-01-10,Wireless Mouse,Electronics,3,25.00,10.00,North\n",
        encoding="utf-8",
    )
    session_id = "fin_sess_multi_unit"
    DatasetManager.register_dataset(session_id, csv_file, force_test_mode=True)

    res = dispatch_tool_call("summarize_sales", {"session_id": session_id})
    assert res["status"] == "success"
    assert res["total_orders"] == 1, "Order with 3 units must count as exactly 1 order"
    assert res["net_units"] == 3.0, "Net units must equal 3.0"
    assert res["net_revenue"] == 75.00
    assert res["profit_metrics"]["net_profit"] == 45.00


def test_distinct_order_counting_multi_line_same_order_id(tmp_path: Path):
    """An order with 3 separate line items sharing the same order_id must count as 1 order."""
    csv_file = tmp_path / "multi_line_same_order.csv"
    csv_file.write_text(
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-777,2026-01-10,Wireless Mouse,Electronics,1,25.00,10.00,North\n"
        "ORD-777,2026-01-10,USB Cable,Accessories,2,10.00,4.00,North\n"
        "ORD-777,2026-01-10,Laptop Stand,Accessories,1,30.00,15.00,North\n",
        encoding="utf-8",
    )
    session_id = "fin_sess_multi_unit"
    DatasetManager.register_dataset(session_id, csv_file, force_test_mode=True)

    res = dispatch_tool_call("summarize_sales", {"session_id": session_id})
    assert res["status"] == "success"
    assert res["total_orders"] == 1, "Three lines sharing ORD-777 must count as 1 distinct order"
    assert res["net_units"] == 4.0, "Total units = 1 + 2 + 1 = 4"
    assert res["net_revenue"] == 75.00, "Total revenue = 25 + 20 + 30 = 75"
    assert res["profit_metrics"]["net_profit"] == 42.00, "Total profit = 15 + 12 + 15 = 42"

    # Dashboard parity check
    ds = DatasetManager.get_dataset(session_id)
    dash = compute_period_metrics(ds.valid_df, has_cost=ds.has_cost_data)
    assert dash["total_orders"] == 1
    assert dash["total_units"] == 4
    assert dash["net_revenue"] == 75.00
    assert dash["net_profit"] == 42.00


# -----------------------------------------------------------------------------
# Test 3: Actual Transaction Price (Different price than catalog)
# -----------------------------------------------------------------------------
def test_transaction_price_used_over_catalog(tmp_path: Path):
    """Verify revenue uses actual transaction row unit_price, not catalog/fixed price."""
    csv_file = tmp_path / "variable_prices.csv"
    # Same product 'Wireless Mouse' sold at 3 different prices (normal $25, promo $15, surge $35)
    csv_file.write_text(
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-1,2026-01-05,Wireless Mouse,Electronics,2,25.00,10.00,North\n"
        "ORD-2,2026-01-06,Wireless Mouse,Electronics,4,15.00,10.00,South\n"
        "ORD-3,2026-01-07,Wireless Mouse,Electronics,1,35.00,10.00,East\n",
        encoding="utf-8",
    )
    session_id = "fin_sess_multi_unit"
    DatasetManager.register_dataset(session_id, csv_file, force_test_mode=True)

    res = dispatch_tool_call("summarize_sales", {"session_id": session_id})
    assert res["status"] == "success"
    # Expected: (2*25) + (4*15) + (1*35) = 50 + 60 + 35 = 145.00
    assert res["net_revenue"] == 145.00
    assert res["net_units"] == 7.0
    # Cost: (2*10) + (4*10) + (1*10) = 70.00
    # Profit: 145 - 70 = 75.00
    assert res["profit_metrics"]["net_profit"] == 75.00


# -----------------------------------------------------------------------------
# Test 4: Missing Cost Data -> Profit Strictly UNAVAILABLE
# -----------------------------------------------------------------------------
def test_missing_cost_data_policy():
    """Verify profit metrics are strictly UNAVAILABLE when unit_cost is missing."""
    csv_path = Path("sample_data/synthetic_sales_no_cost.csv")
    assert csv_path.exists()

    session_id = "fin_sess_no_cost"
    DatasetManager.register_dataset(session_id, csv_path, force_test_mode=True)

    res = dispatch_tool_call("summarize_sales", {"session_id": session_id})
    assert res["status"] == "success"
    assert res["profit_metrics"]["available"] is False
    assert res["profit_metrics"]["net_profit"] == "UNAVAILABLE"
    assert res["profit_metrics"]["gross_margin_percentage"] == "UNAVAILABLE"
    assert "unit_cost column is missing or incomplete" in res["profit_metrics"]["reason"]

    # Rank products by profit must return structured error
    err_res = dispatch_tool_call("rank_products", {"session_id": session_id, "metric": "profit"})
    assert err_res["status"] == "error"
    assert "Cannot rank by profit: unit_cost data is UNAVAILABLE" in err_res["message"]

    # Dashboard parity: net_profit and margin_pct must be None
    ds = DatasetManager.get_dataset(session_id)
    dash = compute_period_metrics(ds.valid_df, has_cost=ds.has_cost_data)
    assert dash["net_profit"] is None
    assert dash["margin_pct"] is None
    assert dash["total_cost"] is None


# -----------------------------------------------------------------------------
# Test 5: Period Comparison with Zero Baseline Revenue
# -----------------------------------------------------------------------------
def test_period_comparison_zero_previous_revenue(tmp_path: Path):
    """When Period A has $0.00 revenue, revenue_growth_percentage must be None and status UNDEFINED_PREVIOUS_PERIOD_ZERO."""
    csv_file = tmp_path / "zero_base_comparison.csv"
    csv_file.write_text(
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-01,2026-02-05,Wireless Mouse,Electronics,5,20.00,10.00,North\n"
        "ORD-02,2026-02-10,USB-C Hub,Accessories,2,50.00,20.00,South\n",
        encoding="utf-8",
    )
    session_id = "fin_sess_zero_base"
    DatasetManager.register_dataset(session_id, csv_file, force_test_mode=True)

    # Period A has NO sales (Jan 2026), Period B has sales (Feb 2026)
    res = dispatch_tool_call(
        "compare_periods",
        {
            "session_id": session_id,
            "period_a": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "period_b": {"start_date": "2026-02-01", "end_date": "2026-02-28"},
        },
    )
    assert res["status"] == "success"
    assert res["period_a"]["net_revenue"] == 0.0
    assert res["period_a"]["orders_count"] == 0
    assert res["period_b"]["net_revenue"] == 200.0
    assert res["variance"]["revenue_delta"] == 200.0
    assert res["variance"]["revenue_growth_percentage"] is None, "Growth from zero must NOT be a calculated percentage"
    assert res["variance"]["revenue_growth_status"] == "UNDEFINED_PREVIOUS_PERIOD_ZERO"
    assert res["variance"]["units_growth_status"] == "UNDEFINED_PREVIOUS_PERIOD_ZERO"


# -----------------------------------------------------------------------------
# Test 6: Returns and Negative Quantities
# -----------------------------------------------------------------------------
def test_returns_and_negative_quantities(tmp_path: Path):
    """Verify returns (quantity < 0) reduce net units, net revenue, total cost, and net profit."""
    csv_file = tmp_path / "returns_sales.csv"
    csv_file.write_text(
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-101,2026-01-05,Headphones,Audio,4,50.00,20.00,North\n"
        "ORD-102,2026-01-10,Headphones,Audio,-1,50.00,20.00,North\n",  # Return of 1 unit
        encoding="utf-8",
    )
    session_id = "fin_sess_returns"
    DatasetManager.register_dataset(session_id, csv_file, force_test_mode=True)

    res = dispatch_tool_call("summarize_sales", {"session_id": session_id})
    assert res["status"] == "success"
    assert res["total_orders"] == 2
    assert res["net_units"] == 3.0  # 4 - 1 = 3
    assert res["net_revenue"] == 150.00  # (4*50) - (1*50) = 150
    # Cost: (4*20) - (1*20) = 60
    # Profit: 150 - 60 = 90
    assert res["profit_metrics"]["net_profit"] == 90.00
    # Gross Margin: (90 / 150) * 100 = 60.0%
    assert res["profit_metrics"]["gross_margin_percentage"] == 60.00

    # Dashboard parity check
    ds = DatasetManager.get_dataset(session_id)
    dash = compute_period_metrics(ds.valid_df, has_cost=ds.has_cost_data)
    assert dash["total_units"] == 3
    assert dash["net_revenue"] == 150.00
    assert dash["net_profit"] == 90.00
    assert dash["total_cost"] == 60.00
    assert dash["margin_pct"] == 60.00


# -----------------------------------------------------------------------------
# Test 7: Period Comparison on synthetic_sales.csv (Jan vs Feb 2026)
# -----------------------------------------------------------------------------
def test_period_comparison_jan_vs_feb_synthetic_sales():
    """Verify period comparison deltas on synthetic_sales.csv."""
    csv_path = Path("sample_data/synthetic_sales.csv")
    session_id = "fin_sess_baseline"
    DatasetManager.register_dataset(session_id, csv_path, force_test_mode=True)

    res = dispatch_tool_call(
        "compare_periods",
        {
            "session_id": session_id,
            "period_a": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "period_b": {"start_date": "2026-02-01", "end_date": "2026-02-28"},
        },
    )
    assert res["status"] == "success"
    assert res["period_a"]["net_revenue"] == 1355.00
    assert res["period_a"]["net_units"] == 39.0
    assert res["period_a"]["orders_count"] == 8

    assert res["period_b"]["net_revenue"] == 1590.00
    assert res["period_b"]["net_units"] == 48.0
    assert res["period_b"]["orders_count"] == 7

    assert res["variance"]["revenue_delta"] == 235.00
    assert res["variance"]["revenue_growth_percentage"] == 17.34
    assert res["variance"]["revenue_growth_status"] == "CALCULATED"

    assert res["variance"]["units_delta"] == 9.0
    assert res["variance"]["units_growth_percentage"] == 23.08
    assert res["variance"]["units_growth_status"] == "CALCULATED"


# -----------------------------------------------------------------------------
# Test 8: Product Ranking and Exact Revenue Share
# -----------------------------------------------------------------------------
def test_product_ranking_and_revenue_share():
    """Verify rank_products correctly calculates revenue and revenue share percentage."""
    csv_path = Path("sample_data/synthetic_sales.csv")
    session_id = "fin_sess_baseline"
    DatasetManager.register_dataset(session_id, csv_path, force_test_mode=True)

    res = dispatch_tool_call("rank_products", {"session_id": session_id, "metric": "revenue", "top_n": 10})
    assert res["status"] == "success"
    assert len(res["rankings"]) == 6  # 6 distinct products in synthetic_sales.csv

    # Top product is USB-C Hub: (10*20 + 15*20 + 7*20) = 200 + 300 + 140 = 640.00
    # Share: 640 / 2945 * 100 = 21.73%
    top = res["rankings"][0]
    assert top["product"] == "USB-C Hub"
    assert top["net_revenue"] == 640.00
    assert top["revenue_share_percentage"] == 21.73

    # Total sum of shares should round to 100.0%
    total_share = sum(r["revenue_share_percentage"] for r in res["rankings"])
    assert abs(total_share - 100.0) < 0.2  # Rounding tolerance for 6 items


# -----------------------------------------------------------------------------
# Test 9: Edge Case Analysis & Fix FIN-01 - Missing order_id Parity
# -----------------------------------------------------------------------------
def test_missing_order_id_edge_case(tmp_path: Path):
    """Audits distinct order counting when rows have missing/blank order_ids.
    
    Both MCP count_distinct_orders and Dashboard compute_period_metrics treat
    missing order_ids as separate transactions, ensuring exact parity.
    """
    csv_file = tmp_path / "missing_order_id.csv"
    csv_file.write_text(
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-001,2026-01-01,Product A,Cat,1,10.00,5.00,North\n"
        "ORD-001,2026-01-01,Product B,Cat,2,15.00,5.00,North\n"
        ",2026-01-02,Product C,Cat,1,20.00,10.00,North\n"  # missing order_id
        ",2026-01-03,Product D,Cat,1,25.00,10.00,North\n",  # missing order_id
        encoding="utf-8",
    )
    df = pd.read_csv(csv_file)
    
    # MCP calculation
    mcp_orders = count_distinct_orders(df)
    # Expected in MCP: 1 distinct named (ORD-001) + 2 missing = 3 orders
    assert mcp_orders == 3

    # Dashboard calculation in app.py
    dash_metrics = compute_period_metrics(df, has_cost=False)
    assert dash_metrics["total_orders"] == 3
    assert dash_metrics["total_orders"] == mcp_orders


def test_fin_01_order_id_counting_rules_and_mcp_dashboard_parity(tmp_path: Path):
    """Explicitly verifies the 3 FIN-01 requirement rules:
    1. Duplicate order_id -> counted as 1 single order.
    2. Two rows with different order_ids -> counted as 2 orders.
    3. Row without order_id -> counted as distinct transaction under shared policy,
       with Dashboard and MCP matching identically.
    """
    session_id = "fin_sess_order_id_parity"
    csv_file = tmp_path / "fin_01_rules.csv"
    csv_file.write_text(
        "order_id,date,product,category,quantity,unit_price,unit_cost,region\n"
        "ORD-AAA,2026-01-01,Item 1,Electronics,1,10.00,5.00,North\n"
        "ORD-AAA,2026-01-01,Item 2,Electronics,2,20.00,10.00,North\n"  # Duplicate ORD-AAA (Rule 1: 1 order)
        "ORD-BBB,2026-01-02,Item 3,Accessories,1,15.00,5.00,South\n"   # Distinct ORD-BBB (Rule 2: 2 orders so far)
        ",2026-01-03,Item 4,Accessories,1,30.00,10.00,East\n"          # Missing order_id 1 (Rule 3: +1)
        ",2026-01-04,Item 5,Accessories,3,25.00,12.00,West\n",         # Missing order_id 2 (Rule 3: +1)
        encoding="utf-8",
    )

    DatasetManager.register_dataset(session_id, csv_file, force_test_mode=True)
    dataset = DatasetManager.get_dataset(session_id)

    # 1. Direct count_distinct_orders assertion
    # Named: ORD-AAA, ORD-BBB = 2. Missing: 2. Total = 4 distinct orders.
    assert count_distinct_orders(dataset.valid_df) == 4

    # 2. MCP summarize_sales assertion
    mcp_res = dispatch_tool_call("summarize_sales", {"session_id": session_id})
    assert mcp_res["status"] == "success"
    assert mcp_res["total_orders"] == 4
    assert mcp_res["net_units"] == 8.0  # 1 + 2 + 1 + 1 + 3

    # 3. Dashboard compute_period_metrics assertion
    dash_metrics = compute_period_metrics(dataset.valid_df, has_cost=dataset.has_cost_data)
    assert dash_metrics["total_orders"] == 4
    assert dash_metrics["total_units"] == 8

    # 4. Strict parity between MCP tool and Dashboard
    assert dash_metrics["total_orders"] == mcp_res["total_orders"]
    assert dash_metrics["net_revenue"] == mcp_res["net_revenue"]

    DatasetManager.clear_session(session_id)

