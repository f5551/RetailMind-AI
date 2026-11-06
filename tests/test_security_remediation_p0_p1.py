"""RetailMind AI — Phase 01 Critical Security Remediation (P0/P1) Regression Tests.

Verifies:
1. P0: Rejection of URL-based synthetic agent responses & fake approval injection (mock_agent_view).
2. P1: Capability Ticket fail-closed user identity binding in auth_service and MCP server.
3. P1: Cross-user capability ticket consumption rejection.
4. P1: Rejection of in-band caller_user_id spoofing when host environment identity is absent.
5. P1: Elimination of ambient developer privilege escalation via RETAILMIND_AUTH_TOKEN in UI.
6. P1: Constant-time digest comparison in CSV uploader authorization.
7. P1: Suppression of developer login on public interfaces (403 audit view).
"""

import os
import re
from pathlib import Path
import pytest
import pandas as pd

from src.retailmind.agent.auth_service import AuthorizationService
from src.retailmind.data.loader import DatasetManager
from src.retailmind.mcp.client import RetailMindMCPClient
from src.retailmind.mcp.server import _verify_session_ownership

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_auth_service_rejects_empty_or_mismatched_user_id(tmp_path):
    """P1 Verification: auth_service must fail closed if user_id is empty, missing, or mismatched."""
    auth_db = tmp_path / "test_auth_binding.db"
    auth_service = AuthorizationService(db_path=auth_db)

    args = {
        "session_id": "sess_auth_test_1",
        "title": "Legitimate Title",
        "sections": [{"heading": "Summary", "content": "Content"}],
        "format": "markdown",
    }

    try:
        # Issue ticket for user_alice
        ticket = auth_service.issue_ticket(
            user_id="user_alice",
            session_id="sess_auth_test_1",
            tool_name="generate_report",
            params=args,
        )

        # Attempt 1: Consuming with empty user_id MUST FAIL
        valid_empty, err_empty = auth_service.verify_and_consume_ticket(
            ticket_id=ticket,
            user_id="",
            session_id="sess_auth_test_1",
            tool_name="generate_report",
            params=args,
        )
        assert valid_empty is False
        assert err_empty == "USER_ID_MISMATCH"

        # Attempt 2: Consuming with mismatched user_bob MUST FAIL
        valid_bob, err_bob = auth_service.verify_and_consume_ticket(
            ticket_id=ticket,
            user_id="user_bob",
            session_id="sess_auth_test_1",
            tool_name="generate_report",
            params=args,
        )
        assert valid_bob is False
        assert err_bob == "USER_ID_MISMATCH"

        # Attempt 3: Consuming with legitimate user_alice MUST SUCCEED
        valid_alice, err_alice = auth_service.verify_and_consume_ticket(
            ticket_id=ticket,
            user_id="user_alice",
            session_id="sess_auth_test_1",
            tool_name="generate_report",
            params=args,
        )
        assert valid_alice is True
        assert err_alice == "AUTHORIZED"
    finally:
        auth_service.close()


def test_auth_service_rejects_empty_or_mismatched_session_id(tmp_path):
    """P1 Verification: auth_service must fail closed if session_id is empty, missing, or mismatched."""
    auth_db = tmp_path / "test_auth_sess_binding.db"
    auth_service = AuthorizationService(db_path=auth_db)

    args = {
        "session_id": "sess_legit",
        "title": "Title",
        "sections": [{"heading": "H", "content": "C"}],
        "format": "markdown",
    }

    try:
        ticket = auth_service.issue_ticket(
            user_id="user_cfo",
            session_id="sess_legit",
            tool_name="generate_report",
            params=args,
        )

        # Empty session_id must fail
        valid_empty, err_empty = auth_service.verify_and_consume_ticket(
            ticket_id=ticket,
            user_id="user_cfo",
            session_id="",
            tool_name="generate_report",
            params=args,
        )
        assert valid_empty is False
        assert err_empty == "SESSION_ID_MISMATCH"

        # Mismatched session_id must fail
        valid_other, err_other = auth_service.verify_and_consume_ticket(
            ticket_id=ticket,
            user_id="user_cfo",
            session_id="sess_other",
            tool_name="generate_report",
            params=args,
        )
        assert valid_other is False
        assert err_other == "SESSION_ID_MISMATCH"
    finally:
        auth_service.close()


@pytest.mark.asyncio
async def test_mcp_generate_report_rejects_cross_user_ticket_consumption():
    """P1 Verification: MCP server must reject ticket consumption if caller is not the ticket owner."""
    session_id = "test_cross_user_mcp_session"
    user_alice = "user_merchant_alice"
    user_attacker = "user_attacker_mallory"

    sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    DatasetManager.register_dataset(session_id, sample_csv, user_id=user_alice)

    auth_service = AuthorizationService.get_default_service()
    report_args = {
        "session_id": session_id,
        "title": "Alice Confidential Report",
        "sections": [{"heading": "Sales", "content": "Confidential figures"}],
        "format": "markdown",
    }

    # Ticket issued specifically to user_alice
    ticket = auth_service.issue_ticket(
        user_id=user_alice,
        session_id=session_id,
        tool_name="generate_report",
        params=report_args,
    )

    # Mallory connects to MCP client with her own identity
    client = RetailMindMCPClient(caller_user_id=user_attacker)
    async with client:
        call_args = dict(report_args, auth_ticket=ticket)
        result = await client.call_tool("generate_report", call_args)

        # Must be rejected because caller identity (mallory) != ticket owner (alice) and != session owner (alice)
        assert result.get("status") == "error"
        assert result.get("error_code") == "PERMISSION_DENIED"


def test_mcp_rejects_untrusted_caller_spoofing_without_host_identity():
    """P1 Verification: When RETAILMIND_CALLER_USER_ID is not in the environment,
    an untrusted client argument must NOT be permitted to access an owned session."""
    session_id = "sess_owned_merchant_xyz"
    legitimate_owner = "user_merchant_xyz"

    df_sample = pd.DataFrame({
        "date": ["2026-01-01"],
        "product": ["Item"],
        "quantity": [1],
        "unit_price": [10.0],
    })
    DatasetManager.register_dataset(session_id, df_sample, user_id=legitimate_owner)

    # Ensure host environment identity is completely absent and strict host auth is enforced
    os.environ.pop("RETAILMIND_CALLER_USER_ID", None)
    os.environ["RETAILMIND_STRICT_HOST_AUTH"] = "1"
    try:
        # Untrusted client passes in-band caller_user_id matching the owner
        is_valid, msg = _verify_session_ownership(session_id, caller_user_id=legitimate_owner)

        # Must FAIL CLOSED: An untrusted client cannot self-declare its identity
        assert is_valid is False
        assert "Access Denied" in msg or "PERMISSION_DENIED" in msg
    finally:
        os.environ.pop("RETAILMIND_STRICT_HOST_AUTH", None)


def test_no_synthetic_agent_view_backdoor_in_app():
    """P0 Verification: app.py must not contain mock_agent_view query parameter backdoor."""
    app_code = (WORKSPACE_ROOT / "app.py").read_text(encoding="utf-8")
    assert 'st.query_params.get("mock_agent_view")' not in app_code
    assert '"mock_agent_view"' not in app_code


def test_check_developer_authorization_does_not_fall_back_to_global_auth_token():
    """P1 Verification: check_developer_authorization in app.py must not use global RETAILMIND_AUTH_TOKEN."""
    app_code = (WORKSPACE_ROOT / "app.py").read_text(encoding="utf-8")
    
    # Locate check_developer_authorization definition
    dev_func_match = re.search(
        r"def check_developer_authorization\(\) -> bool:.*?(?=\ndef |\Z)",
        app_code,
        re.DOTALL,
    )
    assert dev_func_match is not None, "check_developer_authorization not found in app.py"
    func_body = dev_func_match.group(0)

    # Must NOT fall back to global RETAILMIND_AUTH_TOKEN
    assert "RETAILMIND_AUTH_TOKEN" not in func_body, (
        "CRITICAL LEAK: check_developer_authorization falls back to global RETAILMIND_AUTH_TOKEN!"
    )


def test_csv_uploader_uses_constant_time_digest_comparison():
    """P1 Verification: app.py CSV uploader must use hmac.compare_digest for secret comparison."""
    app_code = (WORKSPACE_ROOT / "app.py").read_text(encoding="utf-8")
    
    # Check that v3_secret_input == configured_secret is NOT present
    assert "v3_secret_input == configured_secret" not in app_code, (
        "TIMING VULNERABILITY: v3_secret_input uses direct string equality instead of hmac.compare_digest"
    )
    assert "hmac.compare_digest(v3_secret_input, configured_secret)" in app_code or \
           "hmac.compare_digest(v3_secret_input.strip(), configured_secret)" in app_code


def test_audit_forbidden_screen_checks_local_interface_binding():
    """P1 Verification: Audit 403 Forbidden page must check is_local_interface_bound before rendering login."""
    app_code = (WORKSPACE_ROOT / "app.py").read_text(encoding="utf-8")
    
    # Locate View 5 / audit handler
    audit_view_match = re.search(
        r'elif active_view == "audit":.*?(?=\nelif |\Z)',
        app_code,
        re.DOTALL,
    )
    assert audit_view_match is not None, "audit view block not found in app.py"
    audit_view_code = audit_view_match.group(0)

    # The 403 block in audit view must check is_local_interface_bound()
    assert "is_local_interface_bound()" in audit_view_code, (
        "PUBLIC EXPOSURE: audit view 403 screen renders developer password login without checking is_local_interface_bound()!"
    )
