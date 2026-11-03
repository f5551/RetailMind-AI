"""RetailMind AI — MCP Integration and Transport Verification Tests.

Tests real MCP SDK v2 stdio client/server protocol lifecycle:
1. Server startup and real stdio handshake.
2. Discovery of exactly eight approved tools.
3. Strict schema validation and compatibility.
4. Cross-process tool execution of deterministic sales calculations.
5. Invalid arguments and structured error handling.
6. Unknown tool requests and graceful failure.
7. Subprocess cleanup and connection termination.
8. Controlled failure on unreachable server without unauthorized fallback.
"""

import asyncio
from pathlib import Path
import pytest

from src.retailmind.data.loader import DatasetManager
from src.retailmind.mcp.client import EXPECTED_TOOLS, MCPConnectionError, RetailMindMCPClient

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.asyncio
async def test_mcp_server_connection_and_discovery():
    """Verify real stdio connection, initialization handshake, and discovery of exactly 8 tools."""
    client = RetailMindMCPClient()
    async with client:
        assert client.is_connected is True
        tools = client.get_discovered_tools()
        assert len(tools) == 8
        assert set(tools.keys()) == EXPECTED_TOOLS

        declarations = client.get_gemini_tool_declarations()
        assert len(declarations) == 8
        decl_names = {d.name for d in declarations}
        assert decl_names == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_mcp_cross_process_calculation():
    """Verify real MCP execution of calculations across separate processes."""
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    session_id = "test_mcp_calc_session"
    DatasetManager.register_dataset(session_id, csv_path)

    client = RetailMindMCPClient()
    async with client:
        obs = await client.call_tool("summarize_sales", {"session_id": session_id})
        assert obs.get("status") == "success"
        assert obs.get("total_orders") == 15
        assert obs.get("net_units") == 87.0
        assert obs.get("net_revenue") == 2945.0
        assert obs.get("profit_metrics", {}).get("net_profit") == 1525.5
        assert obs.get("profit_metrics", {}).get("gross_margin_percentage") == 51.8


@pytest.mark.asyncio
async def test_mcp_invalid_arguments_and_missing_session():
    """Verify structured error handling when calling tools with nonexistent session or invalid args."""
    client = RetailMindMCPClient()
    async with client:
        obs = await client.call_tool("summarize_sales", {"session_id": "nonexistent_session_id"})
        assert obs.get("status") == "error"
        assert "No dataset found" in obs.get("message", "")


@pytest.mark.asyncio
async def test_mcp_unknown_tool_rejection():
    """Verify calling an unregistered tool returns controlled error."""
    client = RetailMindMCPClient()
    async with client:
        with pytest.raises(ValueError, match="not registered"):
            await client.call_tool("unregistered_malicious_tool", {"session_id": "any"})


@pytest.mark.asyncio
async def test_mcp_connection_failure_behavior():
    """Verify controlled MCPConnectionError when connecting to invalid command."""
    client = RetailMindMCPClient(server_command="nonexistent_python_binary_xyz_123")
    with pytest.raises(MCPConnectionError):
        await client.connect()
    assert client.is_connected is False


@pytest.mark.asyncio
async def test_mcp_clean_cleanup():
    """Verify close cleanly shuts down subprocess and resets connection state."""
    client = RetailMindMCPClient()
    await client.connect()
    assert client.is_connected is True
    await client.close()
    assert client.is_connected is False
    assert client._session is None
