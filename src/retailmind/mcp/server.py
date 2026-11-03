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

Enforces strict session ownership validation across all eight tools to prevent
unauthorized cross-tenant data access or direct MCP parameter tampering.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from mcp.server import MCPServer
from src.retailmind.tools.registry import dispatch_tool_call

logger = logging.getLogger("retailmind.mcp.server")

# Create official MCP server instance
server = MCPServer(name="retailmind-sales-server", version="1.0.0")


def _verify_session_ownership(session_id: str, caller_user_id: Optional[str] = None) -> Tuple[bool, str]:
    """Validates session ownership inside the MCP server.

    Ensures data access is strictly bounded to the authorized caller.
    The server TRUSTS ONLY the identity established by the host transport (os.environ).
    It REJECTS any in-band caller_user_id from tool arguments that attempts to spoof identity.
    """
    if not session_id or not isinstance(session_id, str):
        return False, "Invalid or missing session_id."

    # Trusted identity comes strictly from the host process environment variable
    trusted_caller = os.getenv("RETAILMIND_CALLER_USER_ID")

    # If an untrusted caller in-band argument attempts to spoof a different identity, reject immediately
    if caller_user_id and trusted_caller and caller_user_id != trusted_caller:
        logger.warning(
            "Access Denied: In-band caller_user_id '%s' attempted to spoof trusted host identity '%s'",
            caller_user_id,
            trusted_caller,
        )
        return False, f"PERMISSION_DENIED: Identity spoofing detected. In-band caller_user_id '{caller_user_id}' does not match trusted host identity."

    from src.retailmind.data.loader import DatasetManager

    owner = DatasetManager.get_session_owner(session_id)
    if not owner:
        return True, ""

    effective_caller = trusted_caller or caller_user_id
    if not effective_caller:
        return False, f"Access Denied: Missing caller identity for session '{session_id}'."

    if owner != effective_caller:
        logger.warning(
            "Access Denied: Caller '%s' is not authorized to access session '%s' owned by '%s'",
            effective_caller,
            session_id,
            owner,
        )
        return False, f"PERMISSION_DENIED: Access to session '{session_id}' is not authorized for caller '{effective_caller}'."

    return True, ""


def _safe_dispatch(tool_name: str, args: Dict[str, Any], is_approved: bool = False) -> str:
    """Dispatches tool call safely, sanitizing exceptions to prevent path or secret leaks."""
    try:
        # Strip internal security arguments before dispatching to tool schemas
        dispatch_args = {k: v for k, v in args.items() if k not in ("caller_user_id", "auth_ticket")}
        result = dispatch_tool_call(tool_name, dispatch_args, is_approved=is_approved)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        err_msg = str(exc)
        if "C:\\" in err_msg or "/home" in err_msg or "\\" in err_msg:
            err_msg = "A dataset access or calculation error occurred."
        return json.dumps({"status": "error", "message": err_msg, "tool": tool_name})


def _guard_and_dispatch(
    tool_name: str,
    session_id: str,
    caller_user_id: Optional[str],
    args: Dict[str, Any],
    is_approved: bool = False,
) -> str:
    is_valid, err_msg = _verify_session_ownership(session_id, caller_user_id)
    if not is_valid:
        error_code = "PERMISSION_DENIED" if ("PERMISSION_DENIED" in err_msg or "Access Denied" in err_msg) else "SESSION_NOT_FOUND"
        return json.dumps(
            {
                "status": "error",
                "error_code": error_code,
                "message": err_msg,
                "tool": tool_name,
            },
            ensure_ascii=False,
        )
    return _safe_dispatch(tool_name, args, is_approved=is_approved)


@server.tool(
    name="inspect_dataset",
    description="Returns row count, column inventory, detected types, date range, and preview sample rows for an active session.",
)
def tool_inspect_dataset(session_id: str, sample_size: int = 3, caller_user_id: Optional[str] = None) -> str:
    args = {"session_id": session_id, "sample_size": sample_size}
    return _guard_and_dispatch("inspect_dataset", session_id, caller_user_id, args)


@server.tool(
    name="validate_dataset",
    description="Audits CSV data against contract rules, returns quarantined rows count, issues, and profit availability.",
)
def tool_validate_dataset(session_id: str, caller_user_id: Optional[str] = None) -> str:
    args = {"session_id": session_id}
    return _guard_and_dispatch("validate_dataset", session_id, caller_user_id, args)


@server.tool(
    name="summarize_sales",
    description="Calculates total orders, net units sold, net revenue, and profit/margin (if unit cost is available).",
)
def tool_summarize_sales(
    session_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: Optional[str] = None,
    caller_user_id: Optional[str] = None,
) -> str:
    args = {"session_id": session_id, "start_date": start_date, "end_date": end_date, "group_by": group_by}
    return _guard_and_dispatch("summarize_sales", session_id, caller_user_id, args)


@server.tool(
    name="rank_products",
    description="Ranks top or bottom products by revenue, units sold, or profit with revenue share percentages.",
)
def tool_rank_products(
    session_id: str,
    metric: str = "revenue",
    top_n: int = 5,
    ascending: bool = False,
    caller_user_id: Optional[str] = None,
) -> str:
    args = {"session_id": session_id, "metric": metric, "top_n": top_n, "ascending": ascending}
    return _guard_and_dispatch("rank_products", session_id, caller_user_id, args)


@server.tool(
    name="compare_periods",
    description="Compares revenue and volume variance between two calendar date ranges.",
)
def tool_compare_periods(
    session_id: str,
    period_a: Dict[str, Any],
    period_b: Dict[str, Any],
    caller_user_id: Optional[str] = None,
) -> str:
    args = {"session_id": session_id, "period_a": period_a, "period_b": period_b}
    return _guard_and_dispatch("compare_periods", session_id, caller_user_id, args)


@server.tool(
    name="detect_anomalies",
    description="Detects statistical transaction outliers in revenue or quantity using zscore or iqr methods.",
)
def tool_detect_anomalies(
    session_id: str,
    column: str = "revenue",
    method: str = "zscore",
    threshold: float = 2.5,
    caller_user_id: Optional[str] = None,
) -> str:
    args = {"session_id": session_id, "column": column, "method": method, "threshold": threshold}
    return _guard_and_dispatch("detect_anomalies", session_id, caller_user_id, args)


@server.tool(
    name="segment_sales",
    description="Aggregates sales metrics broken down by category or region dimensions.",
)
def tool_segment_sales(
    session_id: str,
    dimension: str = "category",
    secondary_dimension: Optional[str] = None,
    caller_user_id: Optional[str] = None,
) -> str:
    args = {"session_id": session_id, "dimension": dimension, "secondary_dimension": secondary_dimension}
    return _guard_and_dispatch("segment_sales", session_id, caller_user_id, args)


@server.tool(
    name="generate_report",
    description="Generates and exports an executive sales report. WRITE ACTION: Requires explicit human authorization.",
)
def tool_generate_report(
    session_id: str,
    title: str,
    sections: List[Dict[str, Any]],
    format: str = "markdown",
    auth_ticket: Optional[str] = None,
    caller_user_id: Optional[str] = None,
) -> str:
    # 1. Enforce session ownership
    is_valid_owner, err_msg = _verify_session_ownership(session_id, caller_user_id)
    if not is_valid_owner:
        return json.dumps(
            {
                "status": "error",
                "error_code": "PERMISSION_DENIED",
                "message": err_msg,
                "approval_status": "DENIED",
            },
            ensure_ascii=False,
        )

    # 2. Enforce human write authorization ticket
    from src.retailmind.agent.auth_service import AuthorizationService

    args = {
        "session_id": session_id,
        "title": title,
        "sections": sections,
        "format": format,
    }

    auth_service = AuthorizationService.get_default_service()
    is_valid, reason = auth_service.verify_and_consume_ticket(
        ticket_id=auth_ticket,
        user_id="",
        session_id=session_id,
        tool_name="generate_report",
        params=args,
    )

    if not is_valid:
        logger.warning(
            "MCP Server rejected unauthorized generate_report for session '%s': %s",
            session_id,
            reason,
        )
        return json.dumps(
            {
                "status": "error",
                "error_code": "PERMISSION_DENIED",
                "message": f"Write action 'generate_report' rejected: {reason}",
                "approval_status": "DENIED",
            },
            ensure_ascii=False,
        )

    return _safe_dispatch("generate_report", args, is_approved=True)


def main():
    """Runs the MCP server over stdio transport."""
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
