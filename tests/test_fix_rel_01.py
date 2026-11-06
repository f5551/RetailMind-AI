"""RetailMind AI — Regression Test Suite for Fix REL-01.

Validates report generation behavior with:
1. Default internal reports directory within project workspace.
2. Authorized external data and reports directory outside workspace root.
3. Strict rejection of unauthorized output paths outside the approved directory.
4. Human-in-the-loop authorization enforcement (missing/invalid ticket rejection vs valid ticket success).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.config import settings
from src.retailmind.data.loader import DatasetManager
from src.retailmind.mcp.server import tool_generate_report
from src.retailmind.tools.registry import dispatch_tool_call


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Restores environment variables after each test."""
    original_data_dir = os.environ.get("RETAILMIND_DATA_DIR")
    original_reports_dir = os.environ.get("RETAILMIND_REPORTS_DIR")
    original_caller = os.environ.get("RETAILMIND_CALLER_USER_ID")
    yield
    if original_data_dir is not None:
        os.environ["RETAILMIND_DATA_DIR"] = original_data_dir
    else:
        os.environ.pop("RETAILMIND_DATA_DIR", None)

    if original_reports_dir is not None:
        os.environ["RETAILMIND_REPORTS_DIR"] = original_reports_dir
    else:
        os.environ.pop("RETAILMIND_REPORTS_DIR", None)

    if original_caller is not None:
        os.environ["RETAILMIND_CALLER_USER_ID"] = original_caller
    else:
        os.environ.pop("RETAILMIND_CALLER_USER_ID", None)


def test_1_generate_report_internal_workspace_directory():
    """Example 1: Internal project directory -> Export succeeds with relative file_path."""
    os.environ.pop("RETAILMIND_DATA_DIR", None)
    os.environ.pop("RETAILMIND_REPORTS_DIR", None)

    args = {
        "session_id": "sess_internal_rel",
        "title": "Internal Scope Report",
        "sections": [
            {
                "heading": "Summary",
                "content": "Quarterly sales figures.",
                "table_data": [{"Metric": "Revenue", "Value": "$10,000"}],
            }
        ],
        "format": "markdown",
    }

    res = dispatch_tool_call("generate_report", args, is_approved=True)
    assert res["status"] == "success"
    assert res["approval_status"] == "APPROVED"
    assert "reports" in res["file_path"]

    # Must be relative to workspace root
    full_path = settings.workspace_root / res["file_path"]
    assert full_path.exists()
    assert "# Internal Scope Report" in full_path.read_text(encoding="utf-8")

    # Cleanup generated test report
    full_path.unlink(missing_ok=True)


def test_2_generate_report_external_authorized_directory():
    """Example 2: External authorized data directory -> Export succeeds in approved external dir."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        external_path = Path(tmp_dir).resolve()
        os.environ["RETAILMIND_DATA_DIR"] = str(external_path)
        os.environ["RETAILMIND_REPORTS_DIR"] = str(external_path / "reports")

        assert settings.reports_dir == (external_path / "reports")

        args = {
            "session_id": "sess_external_rel",
            "title": "External Volume Report",
            "sections": [
                {
                    "heading": "Operations",
                    "content": "Data stored on external persistent volume.",
                    "table_data": [{"Storage": "Persistent Volume", "Status": "Active"}],
                }
            ],
            "format": "markdown",
        }

        res = dispatch_tool_call("generate_report", args, is_approved=True)
        assert res["status"] == "success", f"generate_report failed unexpectedly: {res}"
        assert res["approval_status"] == "APPROVED"

        # The returned path must be absolute and point within external reports dir
        report_file = Path(res["file_path"])
        assert report_file.exists()
        assert report_file.is_relative_to(external_path / "reports")
        assert "# External Volume Report" in report_file.read_text(encoding="utf-8")


def test_3_generate_report_csv_format_external_directory():
    """Example 2 (CSV): External authorized directory with CSV format export."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        external_path = Path(tmp_dir).resolve()
        os.environ["RETAILMIND_DATA_DIR"] = str(external_path)
        os.environ["RETAILMIND_REPORTS_DIR"] = str(external_path / "reports")

        args = {
            "session_id": "sess_csv_rel",
            "title": "External CSV Export",
            "sections": [
                {
                    "heading": "Sales Breakdown",
                    "content": "Tabular export data.",
                    "table_data": [{"Item": "Widget A", "Revenue": "500.00"}],
                }
            ],
            "format": "csv",
        }

        res = dispatch_tool_call("generate_report", args, is_approved=True)
        assert res["status"] == "success"
        assert res["format"] == "csv"

        report_file = Path(res["file_path"])
        assert report_file.exists()
        assert report_file.name.endswith(".csv")
        assert report_file.is_relative_to(external_path / "reports")


def test_4_unauthorized_approval_ticket_rejection():
    """Example 4: Missing or invalid approval ticket -> Execution strictly rejected."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "auth.db"
        auth_service = AuthorizationService(db_path=db_path)
        AuthorizationService._default_instance = auth_service
        session_id = "sess_auth_test"
        sections = [{"heading": "Audit", "content": "Sensitive business content"}]

        try:
            # 1. Direct dispatch without approval must return approval_required
            direct_res = dispatch_tool_call(
                "generate_report",
                {
                    "session_id": session_id,
                    "title": "Unapproved Report",
                    "sections": sections,
                    "format": "markdown",
                },
                is_approved=False,
            )
            assert direct_res["status"] == "approval_required"
            assert direct_res["error_code"] == "PERMISSION_DENIED_PENDING_APPROVAL"

            # 2. MCP Server call without auth_ticket must be rejected
            os.environ["RETAILMIND_CALLER_USER_ID"] = "user_rel_01"
            mcp_res_raw = tool_generate_report(
                session_id=session_id,
                title="MCP Unapproved Report",
                sections=sections,
                format="markdown",
                auth_ticket=None,
                caller_user_id="user_rel_01",
            )
            mcp_res = json.loads(mcp_res_raw)
            assert mcp_res["status"] == "error"
            assert mcp_res["error_code"] == "PERMISSION_DENIED"
            assert mcp_res["approval_status"] == "DENIED"

            # 3. MCP Server call with forged ticket must be rejected
            forged_res_raw = tool_generate_report(
                session_id=session_id,
                title="MCP Forged Ticket Report",
                sections=sections,
                format="markdown",
                auth_ticket="TICKET-FAKE-12345",
                caller_user_id="user_rel_01",
            )
            forged_res = json.loads(forged_res_raw)
            assert forged_res["status"] == "error"
            assert forged_res["error_code"] == "PERMISSION_DENIED"

            # 4. MCP Server call with legitimate issued ticket must SUCCEED
            valid_args = {
                "session_id": session_id,
                "title": "Legitimate Approved Report",
                "sections": sections,
                "format": "markdown",
            }
            ticket_str = auth_service.issue_ticket(
                user_id="user_rel_01",
                session_id=session_id,
                tool_name="generate_report",
                params=valid_args,
            )

            valid_res_raw = tool_generate_report(
                session_id=session_id,
                title="Legitimate Approved Report",
                sections=sections,
                format="markdown",
                auth_ticket=ticket_str,
                caller_user_id="user_rel_01",
            )
            valid_res = json.loads(valid_res_raw)
            assert valid_res["status"] == "success"
            assert valid_res["approval_status"] == "APPROVED"
            assert Path(valid_res["file_path"]).exists()

            # Cleanup
            Path(valid_res["file_path"]).unlink(missing_ok=True)
        finally:
            auth_service.close()
            AuthorizationService._default_instance = None
