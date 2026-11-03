"""RetailMind AI — Official MCP Server.

Provides a real Model Context Protocol (MCP) server using the official Python MCP SDK v2.
Exposes exactly the eight approved CSV sales analytics tools:
1. inspect_dataset
2. validate_dataset
3. summarize_sales
4. rank_products
5. compare_periods
6. detect_anomalies
7. segment_sales
8. generate_report

Runs independently and communicates via official MCP stdio transport.
Reuses validated deterministic Python business logic from src.retailmind.tools.implementations.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server import MCPServer
from src.retailmind.tools.registry import dispatch_tool_call

logger = logging.getLogger("retailmind.mcp.server")

# Create official MCP server instance
server = MCPServer(name="retailmind-sales-server", version="1.0.0")


def _safe_dispatch(tool_name: str, args: Dict[str, Any]) -> str:
    """Dispatches tool call safely, sanitizing exceptions to prevent path or secret leaks."""
    try:
        result = dispatch_tool_call(tool_name, args)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        err_msg = str(exc)
        # Redact raw file paths if present in message
        if "C:\\" in err_msg or "/home" in err_msg or "\\" in err_msg:
            err_msg = "A dataset access or calculation error occurred."
        return json.dumps({"status": "error", "message": err_msg, "tool": tool_name})


@server.tool(
    name="inspect_dataset",
    description="Returns row count, column inventory, detected types, date range, and preview sample rows for an active session.",
)
def tool_inspect_dataset(session_id: str, sample_size: int = 3) -> str:
    return _safe_dispatch("inspect_dataset", {"session_id": session_id, "sample_size": sample_size})


@server.tool(
    name="validate_dataset",
    description="Audits CSV data against contract rules, returns quarantined rows count, issues, and profit availability.",
)
def tool_validate_dataset(session_id: str) -> str:
    return _safe_dispatch("validate_dataset", {"session_id": session_id})


@server.tool(
    name="summarize_sales",
    description="Calculates total orders, net units sold, net revenue, and profit/margin (if unit cost is available).",
)
def tool_summarize_sales(
    session_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: Optional[str] = None,
) -> str:
    return _safe_dispatch(
        "summarize_sales",
        {"session_id": session_id, "start_date": start_date, "end_date": end_date, "group_by": group_by},
    )


@server.tool(
    name="rank_products",
    description="Ranks top or bottom products by revenue, units sold, or profit with revenue share percentages.",
)
def tool_rank_products(
    session_id: str,
    metric: str = "revenue",
    top_n: int = 5,
    ascending: bool = False,
) -> str:
    return _safe_dispatch(
        "rank_products",
        {"session_id": session_id, "metric": metric, "top_n": top_n, "ascending": ascending},
    )


@server.tool(
    name="compare_periods",
    description="Compares revenue and volume variance between two calendar date ranges.",
)
def tool_compare_periods(
    session_id: str,
    period_a: Dict[str, Any],
    period_b: Dict[str, Any],
) -> str:
    return _safe_dispatch(
        "compare_periods",
        {"session_id": session_id, "period_a": period_a, "period_b": period_b},
    )


@server.tool(
    name="detect_anomalies",
    description="Detects statistical transaction outliers in revenue or quantity using zscore or iqr methods.",
)
def tool_detect_anomalies(
    session_id: str,
    column: str = "revenue",
    method: str = "zscore",
    threshold: float = 2.5,
) -> str:
    return _safe_dispatch(
        "detect_anomalies",
        {"session_id": session_id, "column": column, "method": method, "threshold": threshold},
    )


@server.tool(
    name="segment_sales",
    description="Aggregates sales metrics broken down by category or region dimensions.",
)
def tool_segment_sales(
    session_id: str,
    dimension: str = "category",
    secondary_dimension: Optional[str] = None,
) -> str:
    return _safe_dispatch(
        "segment_sales",
        {"session_id": session_id, "dimension": dimension, "secondary_dimension": secondary_dimension},
    )


@server.tool(
    name="generate_report",
    description="Generates and exports an executive sales report. WRITE ACTION: Requires explicit human authorization.",
)
def tool_generate_report(
    session_id: str,
    title: str,
    sections: List[Dict[str, Any]],
    format: str = "markdown",
    approval_token: Optional[str] = None,
) -> str:
    return _safe_dispatch(
        "generate_report",
        {
            "session_id": session_id,
            "title": title,
            "sections": sections,
            "format": format,
            "approval_token": approval_token,
        },
    )


def main():
    """Runs the MCP server over stdio transport."""
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
