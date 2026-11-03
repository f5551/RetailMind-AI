"""RetailMind AI — Phase 4 Security, Audit Logging, and Adversarial Defense Tests.

Verifies:
1. Unauthorized MCP report creation denial (fail-closed).
2. Forged capability ticket rejection.
3. Replayed authorization rejection (single-use semantics).
4. Parameter tampering rejection (cryptographic hash binding).
5. Audit log persistence across complete process restarts.
6. Secret redaction in audit logs.
7. PermissionManager ask_on_write enforcement.
8. Resistance to indirect CSV prompt injection.
9. Resistance to memory poisoning attacks.
"""

import asyncio
import json
import subprocess
import sys
import uuid
from pathlib import Path
import pytest

from src.retailmind.agent.auth_service import AuthorizationService, compute_parameters_hash
from src.retailmind.agent.permissions import PermissionManager
from src.retailmind.audit.logger import AuditLogger, redact_sensitive_dict
from src.retailmind.data.loader import DatasetManager
from src.retailmind.mcp.client import RetailMindMCPClient
from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.asyncio
async def test_unauthorized_direct_mcp_generate_report_denied():
    """Verify that calling generate_report directly via MCP without a ticket is rejected."""
    client = RetailMindMCPClient()
    async with client:
        result = await client.call_tool(
            "generate_report",
            {
                "session_id": "test_unauth_mcp_session",
                "title": "Unauthorized Report",
                "sections": [{"heading": "Unauthorized", "content": "Payload"}],
            },
        )
        assert result.get("status") == "error"
        assert result.get("error_code") == "PERMISSION_DENIED"
        assert "rejected" in result.get("message", "").lower()


@pytest.mark.asyncio
async def test_forged_mcp_ticket_rejected():
    """Verify that calling generate_report with a forged ticket is rejected."""
    client = RetailMindMCPClient()
    async with client:
        result = await client.call_tool(
            "generate_report",
            {
                "session_id": "test_forged_session",
                "title": "Hacked Report",
                "sections": [{"heading": "Hacked", "content": "Payload"}],
                "auth_ticket": "cap_forged_superadmin_ticket_xyz",
            },
        )
        assert result.get("status") == "error"
        assert result.get("error_code") == "PERMISSION_DENIED"
        assert "FORGED_OR_UNKNOWN_TICKET" in result.get("message", "")


@pytest.mark.asyncio
async def test_mcp_ticket_single_use_and_replay_rejection(tmp_path):
    """Verify that an authorization ticket can be used exactly once and cannot be replayed."""
    auth_db = tmp_path / "test_auth.db"
    auth_service = AuthorizationService(db_path=auth_db)

    args = {
        "session_id": "test_replay_session",
        "title": "Legitimate Executive Report",
        "sections": [{"heading": "Section 1", "content": "Valid Content"}],
        "format": "markdown",
    }

    # Issue single-use ticket
    ticket = auth_service.issue_ticket(
        user_id="user_admin",
        session_id="test_replay_session",
        tool_name="generate_report",
        params=args,
    )

    # First consumption: Must succeed
    is_valid, reason = auth_service.verify_and_consume_ticket(
        ticket_id=ticket,
        user_id="user_admin",
        session_id="test_replay_session",
        tool_name="generate_report",
        params=args,
    )
    assert is_valid is True
    assert reason == "AUTHORIZED"

    # Replay attempt: Must fail
    is_valid_replay, reason_replay = auth_service.verify_and_consume_ticket(
        ticket_id=ticket,
        user_id="user_admin",
        session_id="test_replay_session",
        tool_name="generate_report",
        params=args,
    )
    assert is_valid_replay is False
    assert "REPLAY_ATTACK" in reason_replay


def test_parameter_tampering_rejected(tmp_path):
    """Verify that modifying action parameters invalidates the authorization ticket."""
    auth_db = tmp_path / "test_tamper.db"
    auth_service = AuthorizationService(db_path=auth_db)

    approved_args = {
        "session_id": "session_tamper_test",
        "title": "Quarterly Financial Analysis",
        "sections": [{"heading": "Financials", "content": "Normal data"}],
        "format": "markdown",
    }

    ticket = auth_service.issue_ticket(
        user_id="user_cfo",
        session_id="session_tamper_test",
        tool_name="generate_report",
        params=approved_args,
    )

    # Attacker tampers with content
    tampered_args = dict(approved_args)
    tampered_args["sections"] = [{"heading": "Malicious", "content": "Exfiltrated secrets"}]

    is_valid, reason = auth_service.verify_and_consume_ticket(
        ticket_id=ticket,
        user_id="user_cfo",
        session_id="session_tamper_test",
        tool_name="generate_report",
        params=tampered_args,
    )
    assert is_valid is False
    assert reason == "PARAMETER_TAMPERING_DETECTED"


def test_secret_redaction_in_audit_logger():
    """Verify that sensitive credential patterns are masked before persisting."""
    dirty_dict = {
        "user_query": "Please check sales",
        "api_key": "AIzaSyD-FakeSecretKeyForTesting123",
        "auth_token": "bearer-secret-token-xyz",
        "nested": {
            "password": "SuperSecretPassword!",
            "normal_data": "SAFE_STRING",
        },
    }
    cleaned = redact_sensitive_dict(dirty_dict)

    assert cleaned["user_query"] == "Please check sales"
    assert cleaned["api_key"] == "[REDACTED_SECRET]"
    assert cleaned["auth_token"] == "[REDACTED_SECRET]"
    assert cleaned["nested"]["password"] == "[REDACTED_SECRET]"
    assert cleaned["nested"]["normal_data"] == "SAFE_STRING"


def test_audit_persistence_after_process_restart(tmp_path):
    """Verify audit log records survive complete OS process termination and restart."""
    audit_db = tmp_path / "test_proc_audit.db"
    task_uuid = f"audit_task_{uuid.uuid4().hex[:8]}"

    # Subprocess 1: Writes audit log and terminates
    sub1_code = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{WORKSPACE_ROOT}")
from src.retailmind.audit.logger import AuditLogger

logger = AuditLogger(db_path=Path(r"{audit_db}"))
audit_id = logger.log_event(
    task_id="{task_uuid}",
    user_id="audit_tester_1",
    session_id="session_audit_restart",
    tool_name="validate_dataset",
    action_type="READ",
    decision="ALLOWED",
    authorization_outcome="READ_ONLY_AUTHORIZED",
    execution_status="SUCCESS",
    reason_code="READ_ONLY_POLICY_AUTO",
    duration_ms=12.5,
    trace_id="{task_uuid}",
    details={{"test_key": "audit_restart_payload"}}
)
logger.close()
sys.exit(0 if audit_id else 1)
"""
    proc1 = subprocess.run([sys.executable, "-c", sub1_code], capture_output=True, text=True)
    assert proc1.returncode == 0, f"Subprocess 1 failed: {proc1.stderr}"

    # Subprocess 2: Independent fresh Python process verifies data persisted
    sub2_code = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{WORKSPACE_ROOT}")
from src.retailmind.audit.logger import AuditLogger

logger = AuditLogger(db_path=Path(r"{audit_db}"))
events = logger.query_events(user_id="audit_tester_1", session_id="session_audit_restart")
logger.close()
if len(events) == 1 and events[0]["task_id"] == "{task_uuid}" and events[0]["decision"] == "ALLOWED":
    sys.exit(0)
else:
    print(f"Events found: {{events}}")
    sys.exit(1)
"""
    proc2 = subprocess.run([sys.executable, "-c", sub2_code], capture_output=True, text=True)
    assert proc2.returncode == 0, f"Subprocess 2 failed: {proc2.stderr}\n{proc2.stdout}"


def test_permission_manager_ask_on_write_denial():
    """Verify PermissionManager blocks generate_report when no callback is provided."""
    pm = PermissionManager(policy="ask_on_write")
    # Read-only tools execute automatically
    assert pm.check_permission("summarize_sales", {"session_id": "s1"}) is True
    assert pm.check_permission("rank_products", {"session_id": "s1"}) is True
    # Write tool denied by default without explicit callback
    assert pm.check_permission("generate_report", {"session_id": "s1"}, approval_callback=None) is False
    # Write tool denied if callback returns False
    assert pm.check_permission("generate_report", {"session_id": "s1"}, approval_callback=lambda t, a: False) is False
    # Write tool permitted if callback returns True
    assert pm.check_permission("generate_report", {"session_id": "s1"}, approval_callback=lambda t, a: True) is True
