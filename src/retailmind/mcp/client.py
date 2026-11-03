"""RetailMind AI — Official MCP Client Adapter.

Connects to the RetailMind MCP server over stdio transport using official MCP SDK v2.
Discovers the eight approved tools, converts them to Gemini-compatible function declarations,
dispatches model tool calls via session.call_tool(), and keeps the subprocess alive
throughout the agent task lifetime.
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.genai import types as genai_types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logger = logging.getLogger("retailmind.mcp.client")

EXPECTED_TOOLS = {
    "inspect_dataset",
    "validate_dataset",
    "summarize_sales",
    "rank_products",
    "compare_periods",
    "detect_anomalies",
    "segment_sales",
    "generate_report",
}


class MCPConnectionError(Exception):
    """Raised when connecting to or communicating with the MCP server fails."""
    pass


class RetailMindMCPClient:
    """Manages cross-process stdio connection to the RetailMind MCP server."""

    def __init__(
        self,
        server_command: Optional[str] = None,
        server_args: Optional[List[str]] = None,
        server_env: Optional[Dict[str, str]] = None,
    ):
        self.server_command = server_command or sys.executable
        self.server_args = server_args or ["-m", "src.retailmind.mcp.server"]
        self.server_env = server_env or dict(os.environ)

        self._exit_stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None
        self._discovered_tools: Dict[str, Any] = {}
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self._session is not None

    async def connect(self) -> None:
        """Establishes stdio connection, performs initialization handshake, and discovers tools."""
        if self._is_connected:
            return

        self._exit_stack = AsyncExitStack()
        try:
            params = StdioServerParameters(
                command=self.server_command,
                args=self.server_args,
                env=self.server_env,
            )

            # Enter stdio transport
            read_stream, write_stream = await self._exit_stack.enter_async_context(stdio_client(params))

            # Enter client session
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            # Initialize handshake
            init_res = await self._session.initialize()
            logger.info("Connected to MCP server: %s (v%s)", init_res.server_info.name, init_res.server_info.version)

            # Discover tools
            tools_res = await self._session.list_tools()
            self._discovered_tools = {t.name: t for t in tools_res.tools}

            # Validate expected tools are registered
            missing_tools = EXPECTED_TOOLS - set(self._discovered_tools.keys())
            if missing_tools:
                raise MCPConnectionError(f"MCP server is missing expected tools: {missing_tools}")

            self._is_connected = True
            logger.info("Discovered and validated %d MCP tools.", len(self._discovered_tools))

        except Exception as exc:
            await self.close()
            raise MCPConnectionError(f"Failed to connect to MCP server: {exc}") from exc

    async def close(self) -> None:
        """Closes session and terminates MCP server subprocess cleanly."""
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception as exc:
                logger.warning("Error during MCP client close: %s", exc)
            finally:
                self._exit_stack = None
                self._session = None
                self._is_connected = False
                logger.info("MCP client connection closed.")

    async def __aenter__(self) -> "RetailMindMCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def get_discovered_tools(self) -> Dict[str, Any]:
        """Returns the dictionary of discovered MCP tools."""
        return self._discovered_tools

    def get_gemini_tool_declarations(self) -> List[genai_types.FunctionDeclaration]:
        """Converts discovered MCP tools into valid Gemini FunctionDeclaration objects."""
        if not self._is_connected or not self._discovered_tools:
            raise RuntimeError("MCP client must be connected before extracting tool declarations.")

        from src.retailmind.tools.registry import get_gemini_tool_declarations as get_vetted_declarations

        vetted_map = {d["name"]: d for d in get_vetted_declarations()}
        declarations: List[genai_types.FunctionDeclaration] = []

        for name, tool in self._discovered_tools.items():
            if name in vetted_map:
                v_def = vetted_map[name]
                decl = genai_types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or v_def["description"],
                    parameters=v_def["parameters"],
                )
            else:
                schema = tool.input_schema or {"type": "object", "properties": {}}
                cleaned_schema = self._clean_schema_for_gemini(schema)
                decl = genai_types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=cleaned_schema,
                )
            declarations.append(decl)

        return declarations

    @staticmethod
    def _clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitizes JSON schema for strict Google Gemini API compatibility."""
        cleaned: Dict[str, Any] = {}
        for k, v in schema.items():
            if k in ("title", "$defs", "definitions", "default", "additionalProperties", "additional_properties"):
                continue
            if k == "type":
                cleaned["type"] = v.upper() if isinstance(v, str) else v
            elif k == "properties" and isinstance(v, dict):
                cleaned["properties"] = {}
                for prop_name, prop_def in v.items():
                    if isinstance(prop_def, dict):
                        cleaned["properties"][prop_name] = RetailMindMCPClient._clean_schema_for_gemini(prop_def)
                    else:
                        cleaned["properties"][prop_name] = prop_def
            elif k == "required" and isinstance(v, list):
                cleaned["required"] = v
            elif k == "items" and isinstance(v, dict):
                cleaned["items"] = RetailMindMCPClient._clean_schema_for_gemini(v)
            elif k == "description" and isinstance(v, str):
                cleaned["description"] = v
            elif k == "enum" and isinstance(v, list):
                cleaned["enum"] = v

        if cleaned.get("type") in ("OBJECT", "object") and "properties" not in cleaned:
            cleaned["properties"] = {}
        return cleaned

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a tool call via the connected MCP server session."""
        if not self._is_connected or not self._session:
            raise MCPConnectionError("Cannot call tool: MCP client is not connected.")

        if name not in self._discovered_tools:
            raise ValueError(f"Tool '{name}' is not registered on the MCP server.")

        try:
            call_res = await self._session.call_tool(name=name, arguments=arguments)

            if call_res.is_error:
                error_text = "Tool reported error."
                if call_res.content and hasattr(call_res.content[0], "text"):
                    error_text = call_res.content[0].text
                return {"status": "error", "message": error_text, "tool": name}

            if call_res.content and hasattr(call_res.content[0], "text"):
                raw_text = call_res.content[0].text
                try:
                    return json.loads(raw_text)
                except Exception:
                    return {"status": "success", "text": raw_text}

            if call_res.structured_content:
                return call_res.structured_content

            return {"status": "success", "result": str(call_res)}

        except Exception as exc:
            logger.error("MCP tool execution error for '%s': %s", name, exc)
            return {
                "status": "error",
                "message": f"MCP execution error for tool '{name}': {str(exc)}",
                "tool": name,
            }
