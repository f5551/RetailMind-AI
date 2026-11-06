"""RetailMind AI — Verification 02: Mock LLM + Real MCP Pipeline Integration Tests.

Validates the full architectural pipeline:
User Query -> RetailMindAgent Loop -> Mock LLM Tool Call Decision ->
Real MCP Client/Server (stdio transport) -> Synthetic CSV Dataset ->
Real Analytical Calculations -> MCP Response Observation -> Mock LLM Synthesis -> Final Answer.

Constraints:
1. LLM is mocked via MagicMock (NO paid API calls, NO Gemini live proof claimed).
2. MCP Client and MCP Server are 100% REAL running cross-process over stdio.
3. Analytical calculation tools are 100% REAL executing pandas aggregations.
4. Memory and traces use isolated temporary paths (tmp_path).
5. Tests both a clean success scenario and a tool error scenario.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from google.genai import types

from src.retailmind.agent.loop import RetailMindAgent
from src.retailmind.data.loader import DatasetManager
from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.asyncio
async def test_pipeline_success_scenario_with_mock_llm_and_real_mcp(tmp_path: Path):
    """Scenario 1: Clean Success Pipeline.
    
    1. User submits query asking for net revenue and order count.
    2. Agent loop dispatches to Mock LLM.
    3. Mock LLM chooses tool: 'summarize_sales'.
    4. Real MCP Client dispatches tool call across stdio to Real MCP Server.
    5. Real MCP Server executes summarize_sales against sample_data/synthetic_sales.csv.
    6. Real MCP Server returns deterministic revenue $2,945.00, units 87.0, orders 15, profit $1,525.50.
    7. Agent loop injects observation into Mock LLM context.
    8. Mock LLM reads observation and formulates grounded final answer matching exact numbers.
    9. Verified memory is persisted to isolated SQLite with is_verified=True.
    """
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    assert csv_path.exists(), f"Synthetic dataset missing at {csv_path}"

    db_path = tmp_path / "test_memory.db"
    trace_path = tmp_path / "success_pipeline_trace.jsonl"
    mem_mgr = SQLiteMemoryManager(db_path=db_path)

    session_id = "test_pipeline_success_session"
    user_id = "verified_analyst"

    turn_counter = 0
    mcp_observations_captured = []

    def mock_generate_content(model, contents, config):
        nonlocal turn_counter
        turn_counter += 1
        resp = MagicMock()
        resp.usage_metadata = {"prompt_token_count": 150 * turn_counter, "candidates_token_count": 40}

        if turn_counter == 1:
            # Turn 1: LLM decides to call the summarize_sales tool
            fc = MagicMock()
            fc.name = "summarize_sales"
            fc.args = {"session_id": session_id}
            resp.function_calls = [fc]
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text="Calling summarize_sales tool.")])
            resp.candidates = [candidate]
            resp.text = None
            return resp
        else:
            # Turn 2: Inspect observation returned from the REAL MCP Server
            resp.function_calls = None
            last_part = contents[-1].parts[0]
            obs = last_part.function_response.response
            mcp_observations_captured.append(obs)

            # Ground final answer strictly in the real numbers returned by the MCP Server
            net_rev = obs.get("net_revenue")
            total_orders = obs.get("total_orders")
            net_units = obs.get("net_units")
            net_profit = obs.get("profit_metrics", {}).get("net_profit")
            margin = obs.get("profit_metrics", {}).get("gross_margin_percentage")

            final_text = (
                f"Sales Performance Summary: Net Revenue is ${net_rev:,.2f} across {total_orders} orders "
                f"with {net_units:.0f} units sold. Net Profit is ${net_profit:,.2f} ({margin:.1f}% gross margin)."
            )
            resp.text = final_text
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text=final_text)])
            resp.candidates = [candidate]
            return resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate_content

    agent = RetailMindAgent(
        api_key="mock_key_for_offline_test",
        model_id="gemini-mock",
        execution_transport="mcp",
        memory_manager=mem_mgr,
    )
    agent._client = mock_client

    result = agent.run_task(
        user_query="What is our total net revenue, unit count, and profit?",
        session_id=session_id,
        user_id=user_id,
        csv_path=csv_path,
        save_trace_path=trace_path,
    )

    # 1. Pipeline Verification
    assert result.stop_reason == "FINAL_ANSWER"
    assert result.turns_executed == 2
    assert result.tool_calls_count == 1
    assert result.execution_transport == "mcp"

    # 2. Real MCP Observation Verification
    assert len(mcp_observations_captured) == 1
    real_obs = mcp_observations_captured[0]
    assert real_obs.get("status") == "success"
    assert real_obs.get("net_revenue") == 2945.0
    assert real_obs.get("total_orders") == 15
    assert real_obs.get("net_units") == 87.0
    assert real_obs.get("profit_metrics", {}).get("net_profit") == 1525.5
    assert real_obs.get("profit_metrics", {}).get("gross_margin_percentage") == 51.8

    # 3. Final Answer Exact Grounding & Zero Math Invention
    assert "$2,945.00" in result.final_answer
    assert "15 orders" in result.final_answer
    assert "87 units" in result.final_answer
    assert "$1,525.50" in result.final_answer
    assert "51.8%" in result.final_answer

    # 4. Memory Layer Verification
    persisted_context = mem_mgr.retrieve_relevant_context(
        user_id=user_id,
        dataset_fingerprint=DatasetManager.get_dataset_fingerprint(session_id),
    )
    assert len(persisted_context) == 1
    assert "Revenue=$2945.0" in persisted_context[0]["summary"]
    assert "Orders=15" in persisted_context[0]["summary"]
    assert "Units=87.0" in persisted_context[0]["summary"]
    assert "Profit=$1525.5" in persisted_context[0]["summary"]

    with mem_mgr._get_connection() as conn:
        row = conn.execute(
            "SELECT is_verified, task_status FROM analytical_memory WHERE task_id = ?",
            (result.task_id,),
        ).fetchone()
        assert row["is_verified"] == 1
        assert row["task_status"] == "SUCCESS"

    # 5. Trace Verification
    assert trace_path.exists()
    trace_lines = trace_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(trace_lines) >= 4  # task_start, model_turn(call), tool_execution, model_turn(final), task_complete


@pytest.mark.asyncio
async def test_pipeline_tool_failure_scenario_with_mock_llm_and_real_mcp(tmp_path: Path):
    """Scenario 2: Tool Failure & Graceful Recovery Pipeline.
    
    1. User submits query requesting rankings by an invalid/unsupported metric.
    2. Agent loop dispatches to Mock LLM.
    3. Mock LLM chooses tool: 'rank_products' with metric='unsupported_arbitrary_metric'.
    4. Real MCP Client dispatches tool call across stdio to Real MCP Server.
    5. Real MCP Server executes tool, which fails with status='error' and error_code='INVALID_METRIC'.
    6. Real MCP Server returns structured error observation without crash or leak.
    7. Agent loop records status='error' in tool_calls_history and passes observation to Mock LLM.
    8. Mock LLM transparently reports the tool error in final answer without inventing fake data.
    9. Memory persistence records is_verified=False (UNVERIFIED) in SQLite database.
    """
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    assert csv_path.exists(), f"Synthetic dataset missing at {csv_path}"

    db_path = tmp_path / "test_memory_err.db"
    trace_path = tmp_path / "error_pipeline_trace.jsonl"
    mem_mgr = SQLiteMemoryManager(db_path=db_path)

    session_id = "test_pipeline_error_session"
    user_id = "qa_tester_err"

    turn_counter = 0
    mcp_observations_captured = []

    def mock_generate_content_error(model, contents, config):
        nonlocal turn_counter
        turn_counter += 1
        resp = MagicMock()
        resp.usage_metadata = {"prompt_token_count": 120 * turn_counter, "candidates_token_count": 35}

        if turn_counter == 1:
            # Turn 1: LLM decides to call rank_products with an invalid metric
            fc = MagicMock()
            fc.name = "rank_products"
            fc.args = {"session_id": session_id, "metric": "unsupported_arbitrary_metric"}
            resp.function_calls = [fc]
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text="Calling rank_products.")])
            resp.candidates = [candidate]
            resp.text = None
            return resp
        else:
            # Turn 2: Inspect error observation from the REAL MCP Server
            resp.function_calls = None
            last_part = contents[-1].parts[0]
            obs = last_part.function_response.response
            mcp_observations_captured.append(obs)

            err_msg = obs.get("message", "Unknown error")
            err_code = obs.get("error_code", "GENERIC_ERROR")

            # Honest report of tool failure without pretending success or inventing rankings
            final_text = f"Tool Execution Halted: The ranking could not be computed. Error [{err_code}]: {err_msg}"
            resp.text = final_text
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text=final_text)])
            resp.candidates = [candidate]
            return resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate_content_error

    agent = RetailMindAgent(
        api_key="mock_key_for_offline_test",
        model_id="gemini-mock",
        execution_transport="mcp",
        memory_manager=mem_mgr,
    )
    agent._client = mock_client

    result = agent.run_task(
        user_query="Rank products by unsupported metric",
        session_id=session_id,
        user_id=user_id,
        csv_path=csv_path,
        save_trace_path=trace_path,
    )

    # 1. Pipeline Verification
    assert result.stop_reason == "FINAL_ANSWER"
    assert result.turns_executed == 2
    assert result.tool_calls_count == 1
    assert result.execution_transport == "mcp"

    # 2. Real MCP Error Observation Verification
    assert len(mcp_observations_captured) == 1
    err_obs = mcp_observations_captured[0]
    assert err_obs.get("status") == "error"
    assert err_obs.get("error_code") == "INVALID_ARGUMENTS"
    assert "Validation failed for tool 'rank_products' arguments." in err_obs.get("message")

    # 3. Transparent Honest Final Answer (No Fabricated Success)
    assert "Tool Execution Halted" in result.final_answer
    assert "INVALID_ARGUMENTS" in result.final_answer

    # 4. Strict Memory Layer Truthfulness: Failed tool MUST NOT be marked is_verified=True
    # Quality filter excludes is_verified=0 from recall
    persisted_context = mem_mgr.retrieve_relevant_context(
        user_id=user_id,
        dataset_fingerprint=DatasetManager.get_dataset_fingerprint(session_id),
    )
    assert len(persisted_context) == 0  # Quality gate strictly excludes unverified records!

    # Verify directly in SQLite storage that is_verified is recorded as 0 (UNVERIFIED)
    with mem_mgr._get_connection() as conn:
        row = conn.execute(
            "SELECT is_verified, task_status, verified_summary FROM analytical_memory WHERE task_id = ?",
            (result.task_id,),
        ).fetchone()
        assert row["is_verified"] == 0
        assert "[UNVERIFIED MODEL OUTPUT]" in row["verified_summary"]

    # 5. Trace Verification
    assert trace_path.exists()
    trace_lines = trace_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(trace_lines) >= 4
