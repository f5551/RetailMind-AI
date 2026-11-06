"""RetailMind AI — Verification 03: Comprehensive 8-Tool MCP Test Suite.

Tests all eight official MCP tools one by one through the REAL MCP Client and Server:
1. inspect_dataset
2. validate_dataset
3. summarize_sales
4. rank_products
5. compare_periods
6. detect_anomalies
7. segment_sales
8. generate_report (Write action with capability ticket)

For each tool:
- Tests registration on the real MCP server.
- Tests execution with valid arguments against synthetic sales CSV.
- Tests correctness of returned financial/analytical values.
- Tests structured error handling with invalid/malformed arguments.
"""

from pathlib import Path
import json
import pytest

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.data.loader import DatasetManager
from src.retailmind.mcp.client import EXPECTED_TOOLS, RetailMindMCPClient

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def test_setup():
    session_id = "mcp_verify_03_session"
    user_id = "mcp_verify_user"
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    assert csv_path.exists(), f"Synthetic dataset not found at {csv_path}"

    DatasetManager.register_dataset(session_id, csv_path, user_id=user_id)
    return {"session_id": session_id, "user_id": user_id, "csv_path": csv_path}


@pytest.mark.asyncio
async def test_tool_1_inspect_dataset(test_setup):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        # 1. Valid Execution
        obs = await client.call_tool("inspect_dataset", {"session_id": session_id, "sample_size": 3})
        assert obs.get("status") == "success"
        assert obs.get("total_rows") == 15
        assert len(obs.get("columns", [])) == 8
        assert "date" in obs.get("columns")
        assert "unit_price" in obs.get("columns")
        assert obs.get("date_range", {}).get("start_date") == "2026-01-05"
        assert obs.get("date_range", {}).get("end_date") == "2026-02-28"
        assert len(obs.get("sample_rows", [])) == 3

        # 2. Invalid Input: Nonexistent session
        err_obs = await client.call_tool("inspect_dataset", {"session_id": "nonexistent_sess_123"})
        assert err_obs.get("status") == "error"
        assert "No dataset found" in err_obs.get("message")


@pytest.mark.asyncio
async def test_tool_2_validate_dataset(test_setup):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        # 1. Valid Execution
        obs = await client.call_tool("validate_dataset", {"session_id": session_id})
        assert obs.get("status") == "success"
        assert obs.get("is_valid") is True
        assert obs.get("total_rows") == 15
        assert obs.get("valid_rows") == 15
        assert obs.get("quarantined_rows") == 0
        assert obs.get("has_cost_data") is True

        # 2. Invalid Input: Nonexistent session
        err_obs = await client.call_tool("validate_dataset", {"session_id": "nonexistent_sess_456"})
        assert err_obs.get("status") == "error"
        assert "No dataset found" in err_obs.get("message")


@pytest.mark.asyncio
async def test_tool_3_summarize_sales(test_setup):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        # 1. Valid Execution
        obs = await client.call_tool("summarize_sales", {"session_id": session_id})
        assert obs.get("status") == "success"
        assert obs.get("total_orders") == 15
        assert obs.get("net_units") == 87.0
        assert obs.get("net_revenue") == 2945.0
        assert obs.get("currency") == "USD"
        assert obs.get("profit_metrics", {}).get("available") is True
        assert obs.get("profit_metrics", {}).get("net_profit") == 1525.5
        assert obs.get("profit_metrics", {}).get("gross_margin_percentage") == 51.8

        # 2. Invalid Input: Nonexistent session
        err_obs = await client.call_tool("summarize_sales", {"session_id": "nonexistent_sess_789"})
        assert err_obs.get("status") == "error"
        assert "No dataset found" in err_obs.get("message")


@pytest.mark.asyncio
async def test_tool_4_rank_products(test_setup):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        # 1. Valid Execution
        obs = await client.call_tool("rank_products", {"session_id": session_id, "metric": "revenue", "top_n": 3})
        assert obs.get("status") == "success"
        assert obs.get("metric") == "revenue"
        rankings = obs.get("rankings", [])
        assert len(rankings) == 3
        # Top 1 product is USB-C Hub with $640.0 revenue (32 units)
        assert rankings[0]["product"] == "USB-C Hub"
        assert rankings[0]["net_revenue"] == 640.0
        assert rankings[0]["units"] == 32.0

        # 2. Invalid Input: Unsupported metric
        err_obs = await client.call_tool("rank_products", {"session_id": session_id, "metric": "nonexistent_metric"})
        assert err_obs.get("status") == "error"
        assert err_obs.get("error_code") == "INVALID_ARGUMENTS"


@pytest.mark.asyncio
async def test_tool_5_compare_periods(test_setup):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        # 1. Valid Execution: January vs February 2026
        period_a = {"start_date": "2026-01-01", "end_date": "2026-01-31"}
        period_b = {"start_date": "2026-02-01", "end_date": "2026-02-28"}
        obs = await client.call_tool("compare_periods", {"session_id": session_id, "period_a": period_a, "period_b": period_b})
        assert obs.get("status") == "success"
        assert "period_a" in obs
        assert "period_b" in obs
        assert obs.get("period_a", {}).get("net_revenue") == 1355.0
        assert obs.get("period_b", {}).get("net_revenue") == 1590.0
        assert obs.get("variance", {}).get("revenue_delta") == 235.0
        assert obs.get("variance", {}).get("revenue_growth_percentage") == 17.34

        # 2. Invalid Input: Missing required end_date in period_a
        bad_period_a = {"start_date": "2026-01-01"}  # Missing required 'end_date' field
        err_obs = await client.call_tool("compare_periods", {"session_id": session_id, "period_a": bad_period_a, "period_b": period_b})
        assert err_obs.get("status") == "error"
        assert err_obs.get("error_code") == "INVALID_ARGUMENTS"


@pytest.mark.asyncio
async def test_tool_6_detect_anomalies(test_setup):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        # 1. Valid Execution: Z-score detection on revenue
        obs = await client.call_tool("detect_anomalies", {"session_id": session_id, "column": "revenue", "method": "zscore", "threshold": 2.0})
        assert obs.get("status") == "success"
        assert obs.get("method_used") == "zscore"
        assert obs.get("column_analyzed") == "revenue"
        assert "anomalies_count" in obs

        # 2. Invalid Input: Unsupported method
        err_obs = await client.call_tool("detect_anomalies", {"session_id": session_id, "method": "invalid_method"})
        assert err_obs.get("status") == "error"
        assert err_obs.get("error_code") == "INVALID_ARGUMENTS"


@pytest.mark.asyncio
async def test_tool_7_segment_sales(test_setup):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        # 1. Valid Execution: Category segmentation
        obs = await client.call_tool("segment_sales", {"session_id": session_id, "dimension": "category"})
        assert obs.get("status") == "success"
        assert obs.get("dimension") == "category"
        segments = obs.get("segments", [])
        assert len(segments) == 2
        # Sum of segment revenues must exactly equal total net revenue $2,945.00
        total_seg_revenue = sum(s.get("net_revenue", 0.0) for s in segments)
        assert round(total_seg_revenue, 2) == 2945.00

        # 2. Invalid Input: Dimension not in schema
        err_obs = await client.call_tool("segment_sales", {"session_id": session_id, "dimension": "unsupported_dim"})
        assert err_obs.get("status") == "error"
        assert err_obs.get("error_code") == "INVALID_ARGUMENTS"


@pytest.mark.asyncio
async def test_tool_8_generate_report(test_setup, tmp_path):
    session_id = test_setup["session_id"]
    user_id = test_setup["user_id"]

    client = RetailMindMCPClient(caller_user_id=user_id)
    async with client:
        report_args = {
            "session_id": session_id,
            "title": "MCP Verification Executive Report",
            "sections": [
                {"heading": "Executive Summary", "content": "Net revenue reached $2,945.00 across 15 orders."},
                {"heading": "Product Highlights", "content": "USB-C Hub was the top performer with $640.00."},
            ],
            "format": "markdown",
        }

        # 1. Invalid Input / Authorization Failure: Calling write tool without capability ticket
        unauth_obs = await client.call_tool("generate_report", report_args)
        assert unauth_obs.get("status") == "error"
        assert unauth_obs.get("error_code") == "PERMISSION_DENIED"
        assert unauth_obs.get("approval_status") == "DENIED"

        # 2. Invalid Input: Calling with forged/invalid capability ticket
        forged_args = dict(report_args, auth_ticket="FORGED_TICKET_HASH_123")
        forged_obs = await client.call_tool("generate_report", forged_args)
        assert forged_obs.get("status") == "error"
        assert forged_obs.get("error_code") == "PERMISSION_DENIED"

        # 3. Valid Execution: Calling with genuine single-use capability ticket bound to caller & params
        auth_svc = AuthorizationService.get_default_service()
        ticket = auth_svc.issue_ticket(
            user_id=user_id,
            session_id=session_id,
            tool_name="generate_report",
            params=report_args,
        )

        valid_args = dict(report_args, auth_ticket=ticket)
        obs = await client.call_tool("generate_report", valid_args)
        assert obs.get("status") == "success"
        file_path = Path(obs.get("file_path"))
        assert file_path.exists()
        assert obs.get("file_size_bytes") > 0
        content = file_path.read_text(encoding="utf-8")
        assert "MCP Verification Executive Report" in content
        assert "Net revenue reached $2,945.00" in content

        # 4. Replay Attack Prevention: Ticket cannot be consumed a second time
        replay_obs = await client.call_tool("generate_report", valid_args)
        assert replay_obs.get("status") == "error"
        assert replay_obs.get("error_code") == "PERMISSION_DENIED"
        assert "REPLAY_ATTACK" in replay_obs.get("message") or "ALREADY_CONSUMED" in replay_obs.get("message")
