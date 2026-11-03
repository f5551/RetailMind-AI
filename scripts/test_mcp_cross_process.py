"""Test script to verify real MCP stdio cross-process communication and calculation."""

import asyncio
import json
import os
import sys
from pathlib import Path

# SSL Native Windows Certificate injection
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from src.retailmind.data.loader import DatasetManager

async def main():
    print("Testing stdio_client subprocess launch...")
    csv_file = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    DatasetManager.register_dataset("cross_proc_session", csv_file)

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.retailmind.mcp.server"],
        env=dict(os.environ),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_res = await session.initialize()
            print("Session initialized:", init_res.server_info.name, init_res.server_info.version)
            
            tools_res = await session.list_tools()
            print(f"Discovered {len(tools_res.tools)} tools:")
            for t in tools_res.tools:
                print(f"  - {t.name}")

            # Call summarize_sales across stdio
            print("\nInvoking summarize_sales across real MCP stdio...")
            call_res = await session.call_tool("summarize_sales", arguments={"session_id": "cross_proc_session"})
            print("MCP Call is_error:", call_res.is_error)
            text_result = call_res.content[0].text
            print("Returned text payload:", text_result)
            parsed = json.loads(text_result)
            print("Parsed revenue:", parsed.get("net_revenue"))
            print("Parsed profit:", parsed.get("profit_metrics", {}).get("net_profit"))
            assert parsed.get("net_revenue") == 2945.0
            assert parsed.get("profit_metrics", {}).get("net_profit") == 1525.5
            print("\n[SUCCESS] Cross-process MCP tool invocation executed deterministically!")

if __name__ == "__main__":
    asyncio.run(main())
