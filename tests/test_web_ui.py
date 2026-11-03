"""RetailMind AI — Phase 5 Web UI, Dashboard & Deployment Verification Tests.

Verifies:
1. Streamlit application syntax, imports, and compilation.
2. Real KPI and business metrics computation from dataset.
3. Live agent invocation from application via MCP stdio.
4. Human approval and write authorization workflow.
5. Persistent memory explorer integration.
6. Security audit trail inspection.
7. Deployment configuration files validity (Procfile, railway.json, Dockerfile).
"""

import asyncio
import json
import py_compile
import sys
from pathlib import Path
import pytest

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.agent.loop import RetailMindAgent
from src.retailmind.audit.logger import AuditLogger
from src.retailmind.data.loader import DatasetManager
from src.retailmind.mcp.client import RetailMindMCPClient
from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_streamlit_app_compiles_and_syntax_valid():
    """Verify that app.py compiles cleanly with zero syntax errors."""
    app_path = WORKSPACE_ROOT / "app.py"
    assert app_path.exists()
    # Compiles bytecode; raises PyCompileError on syntax error
    py_compile.compile(str(app_path), doraise=True)


def test_app_dataset_loading_and_kpi_computation():
    """Verify data ingestion and KPI computation logic used in the UI."""
    sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    session_id = "test_ui_kpi_session"

    processed = DatasetManager.register_dataset(session_id, sample_csv)
    assert len(processed.raw_df) == 15
    assert len(processed.valid_df) == 15
    assert bool(processed.has_cost_data) is True

    df = processed.valid_df
    net_revenue = float(df["line_revenue"].sum())
    total_units = float(df["quantity"].sum())
    net_profit = float(df["line_profit"].sum())
    margin_pct = (net_profit / net_revenue) * 100.0

    assert net_revenue == 2945.0
    assert total_units == 87.0
    assert net_profit == 1525.5
    assert round(margin_pct, 1) == 51.8


@pytest.mark.asyncio
async def test_app_mcp_agent_invocation_integration():
    """Verify that invoking the agent from the UI executes through MCP cleanly."""
    sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    session_id = "test_ui_agent_mcp_session"

    agent = RetailMindAgent(execution_transport="mcp")
    query = "What is our net revenue and total units sold?"

    res = agent.run_task(
        user_query=query,
        session_id=session_id,
        user_id="ui_tester",
        csv_path=sample_csv,
    )

    assert res.stop_reason == "FINAL_ANSWER"
    assert res.execution_transport == "mcp"
    assert res.turns_executed >= 1
    assert "2,945" in res.final_answer or "2945" in res.final_answer


@pytest.mark.asyncio
async def test_app_approval_workflow_generates_report(tmp_path):
    """Verify the UI approval workflow: host issues ticket, MCP server validates and writes report."""
    session_id = "test_ui_approval_session"
    user_id = "ui_manager"

    sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    DatasetManager.register_dataset(session_id, sample_csv)

    auth_service = AuthorizationService.get_default_service()
    report_args = {
        "session_id": session_id,
        "title": "Streamlit UI Approved Report",
        "sections": [{"heading": "Summary", "content": "Net revenue $2,945.00"}],
        "format": "markdown",
    }

    # Simulate UI user clicking "Approve"
    ticket = auth_service.issue_ticket(
        user_id=user_id,
        session_id=session_id,
        tool_name="generate_report",
        params=report_args,
    )

    client = RetailMindMCPClient()
    async with client:
        call_args = dict(report_args, auth_ticket=ticket)
        result = await client.call_tool("generate_report", call_args)

        assert result.get("status") == "success"
        report_file = Path(result.get("file_path"))
        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert "Streamlit UI Approved Report" in content
        assert "Net revenue $2,945.00" in content


def test_app_persistent_memory_retrieval():
    """Verify persistent memory explorer retrieves findings for active dataset fingerprint."""
    mem = SQLiteMemoryManager()
    session_id = "test_ui_mem_session"
    fingerprint = "fp_ui_test_12345"

    mem.record_task_memory(
        user_id="ui_user_1",
        session_id=session_id,
        task_id="task_ui_1",
        query="Quarterly revenue query",
        dataset_fingerprint=fingerprint,
        summary="Verified net revenue of $2,945.00 across 15 orders.",
        task_status="SUCCESS",
        is_verified=True,
    )

    recalled = mem.retrieve_relevant_context(user_id="ui_user_1", dataset_fingerprint=fingerprint)
    assert len(recalled) >= 1
    assert "2,945.00" in recalled[0]["summary"]


def test_app_audit_trail_retrieval():
    """Verify audit trail retrieves logged security and execution events."""
    logger = AuditLogger.get_default_logger()
    audit_id = logger.log_event(
        task_id="audit_ui_test",
        user_id="ui_auditor",
        session_id="session_ui_audit",
        tool_name="summarize_sales",
        action_type="READ",
        decision="ALLOWED",
        authorization_outcome="READ_ONLY_AUTHORIZED",
        execution_status="SUCCESS",
        reason_code="UI_READ_EXECUTION",
    )
    assert audit_id != ""

    events = logger.query_events(user_id="ui_auditor", session_id="session_ui_audit")
    assert len(events) >= 1
    assert events[0]["tool_name"] == "summarize_sales"


def test_deployment_configuration_files_validity():
    """Verify Procfile, railway.json, and Dockerfile are properly configured for production deployment."""
    # 1. Procfile
    procfile = WORKSPACE_ROOT / "Procfile"
    assert procfile.exists()
    proc_text = procfile.read_text(encoding="utf-8")
    assert "streamlit run app.py" in proc_text
    assert "--server.port=$PORT" in proc_text
    assert "--server.address=0.0.0.0" in proc_text
    assert "--server.headless=true" in proc_text

    # 2. railway.json
    railway_file = WORKSPACE_ROOT / "railway.json"
    assert railway_file.exists()
    data = json.loads(railway_file.read_text(encoding="utf-8"))
    assert data["build"]["builder"] == "NIXPACKS"
    assert "streamlit run app.py" in data["deploy"]["startCommand"]
    assert "/_stcore/health" in data["deploy"]["healthcheckPath"]

    # 3. Dockerfile
    dockerfile = WORKSPACE_ROOT / "Dockerfile"
    assert dockerfile.exists()
    dock_text = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.11-slim" in dock_text
    assert "streamlit" in dock_text
    assert "EXPOSE 8501" in dock_text
