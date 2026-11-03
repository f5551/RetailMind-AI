# RetailMind AI — Model Context Protocol (MCP) Integration Specification

## 1. Overview and Architecture

RetailMind AI implements a genuine cross-process Model Context Protocol (MCP) architecture using the official Python MCP SDK v2 (`mcp==2.3.0`).

All tool calls initiated by the Gemini model (`gemini-3.1-flash-lite`) are routed exclusively through the MCP client and server subsystem:
```
┌─────────────────┐      Prompt / Schema      ┌─────────────────────────┐
│                 │ ◄───────────────────────► │                         │
│   Gemini API    │                           │    RetailMindAgent      │
│                 │ ──── Tool Call JSON ────► │       (Loop)            │
└─────────────────┘                           └────────────┬────────────┘
                                                           │
                                             session.call_tool(name, args)
                                                           │
                                              ┌────────────▼────────────┐
                                              │   RetailMindMCPClient   │
                                              │      (ClientSession)    │
                                              └────────────┬────────────┘
                                                           │
                                                 Standard I/O (JSON-RPC)
                                                           │
                                              ┌────────────▼────────────┐
                                              │    RetailMind MCP       │
                                              │        Server           │
                                              │(MCPServer stdio process)│
                                              └────────────┬────────────┘
                                                           │
                                                  dispatch_tool_call()
                                                           │
                                              ┌────────────▼────────────┐
                                              │  Deterministic Python   │
                                              │    Analytics Tools      │
                                              └─────────────────────────┘
```

## 2. Server Implementation (`src/retailmind/mcp/server.py`)

- **Server Instance:** `server = MCPServer(name="retailmind-sales-server", version="1.0.0")`.
- **Transport:** Standard input / standard output (`server.run_stdio_async()`).
- **Registered Tools (Exactly 8 approved tools):**
  1. `inspect_dataset`: Row count, column inventory, detected types, date range, sample preview rows.
  2. `validate_dataset`: Audits CSV data against contract rules, returns quarantined rows count, issues, and profit availability.
  3. `summarize_sales`: Calculates total orders, net units sold, net revenue, and profit/margin (if cost data present).
  4. `rank_products`: Ranks top or bottom products by revenue, units sold, or profit with revenue share percentages.
  5. `compare_periods`: Compares revenue and volume variance between two calendar date ranges.
  6. `detect_anomalies`: Detects statistical outliers in revenue or quantity using Z-score or IQR methods.
  7. `segment_sales`: Aggregates sales metrics broken down by category or region dimensions.
  8. `generate_report`: Executive markdown report generation (WRITE ACTION; requires explicit human authorization).
- **Security & Data Isolation:**
  - Tools do not accept arbitrary filesystem paths from the model.
  - The model provides only the authorized `session_id`.
  - The server resolves the dataset path through `DatasetManager` using a persistent file-backed session registry (`data/session_registry.json`) and validates the dataset's SHA-256 fingerprint.
  - Raw system paths are stripped from error messages to prevent path disclosure.

## 3. Client Implementation (`src/retailmind/mcp/client.py`)

- **Subprocess Lifecycle:**
  - Manages the MCP server subprocess via `mcp.client.stdio.stdio_client` and `mcp.client.session.ClientSession`.
  - Uses `AsyncExitStack` to guarantee clean, non-leaking termination of the child process on shutdown or error.
- **Dynamic Discovery & Verification:**
  - On connection handshake (`await session.initialize()`), the client calls `await session.list_tools()`.
  - Verifies that all 8 required tools are registered and available.
- **Gemini Schema Compatibility:**
  - Converted tool declarations sanitize JSON Schemas to conform to Google Gemini OpenAPI standards.
  - Disallowed properties (`additionalProperties`, `$defs`, `title`) are stripped recursively to prevent API rejection.
- **Execution Dispatch:**
  - The agent loop calls `await client.call_tool(name, arguments)`.
  - Tool execution is executed over the stdio JSON-RPC connection via `session.call_tool()`.
  - Structured results and errors are safely deserialized and returned to the reasoning loop.

## 4. Cross-Process Communication Verification

Communication occurs across separate operating system processes:
1. **Agent Process:** Runs the Gemini LLM agent loop, handles user interaction, permission gating, and memory management.
2. **MCP Server Process:** Spawned as a child Python subprocess running `src.retailmind.mcp.server`, completely isolated in memory space from the agent process.
3. **Evidence:**
   - Automated unit tests in `tests/test_mcp_integration.py` verify stdio communication, tool discovery, arithmetic accuracy across processes, invalid argument handling, unknown tool rejection, and clean subprocess cleanup.
   - Real Gemini API runs in `scripts/run_mcp_live_scenarios.py` confirm genuine tool calls executed through the MCP subprocess with `execution_transport="mcp"`.
