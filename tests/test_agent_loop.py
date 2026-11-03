"""Unit Tests for RetailMind AI Agent Loop Components and Guardrails."""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.retailmind.agent.cost_meter import BudgetExceededError, CostTracker
from src.retailmind.agent.loop import CredentialsMissingError, RetailMindAgent
from src.retailmind.agent.permissions import PermissionManager
from src.retailmind.agent.tracer import ExecutionTracer


def test_cost_tracker_calculation_and_budget_cap():
    """Verify cost calculation with published rates and budget cutoff."""
    tracker = CostTracker(
        budget_cap_usd=0.10,
        usd_per_million_input=0.30,
        usd_per_million_output=2.50,
    )

    # Turn 1: 10,000 prompt tokens, 1,000 candidate tokens
    # Cost = (10000 * 0.30 / 1M) + (1000 * 2.50 / 1M) = 0.003 + 0.0025 = 0.0055 USD
    turn1 = tracker.record_usage(
        turn_index=1,
        usage_metadata={"prompt_token_count": 10000, "candidates_token_count": 1000},
    )
    assert round(turn1.turn_cost_usd, 4) == 0.0055
    assert round(tracker.cumulative_cost_usd, 4) == 0.0055

    # Should pass pre-flight check
    tracker.pre_flight_check()

    # Trigger budget exceeded by simulating high usage
    tracker.record_usage(
        turn_index=2,
        usage_metadata={"prompt_token_count": 300000, "candidates_token_count": 50000},
    )
    # 300,000 * 0.30/1M = 0.09, 50,000 * 2.50/1M = 0.125 -> Cumulative > 0.10
    with pytest.raises(BudgetExceededError):
        tracker.pre_flight_check()


def test_permission_manager_ask_on_write():
    """Verify ask_on_write strictly gates write actions."""
    pm = PermissionManager(policy="ask_on_write")

    # Read-only tools require no approval
    assert pm.check_permission("summarize_sales", {}) is True
    assert pm.check_permission("rank_products", {}) is True

    # generate_report denied without callback
    assert pm.check_permission("generate_report", {}) is False

    # generate_report approved with positive callback
    assert pm.check_permission("generate_report", {}, approval_callback=lambda tool, args: True) is True

    # generate_report denied with negative callback
    assert pm.check_permission("generate_report", {}, approval_callback=lambda tool, args: False) is False


def test_execution_tracer_saves_valid_jsonl(tmp_path: Path):
    """Verify JSONL serialization of execution events."""
    tracer = ExecutionTracer(task_id="task-123", session_id="sess-abc")
    tracer.log_event("task_start", turn_index=0, data={"query": "Test query"})
    tracer.log_event("tool_execution", turn_index=1, data={"tool": "summarize_sales", "status": "success"})

    trace_file = tmp_path / "test_trace.jsonl"
    saved_path = tracer.save_jsonl(trace_file)

    assert saved_path.exists()
    lines = [json.loads(line) for line in saved_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(lines) == 2
    assert lines[0]["event_type"] == "task_start"
    assert lines[1]["event_type"] == "tool_execution"


def test_retailmind_agent_credentials_guard():
    """Verify agent safely reports missing credentials instead of fabricating calls."""
    agent = RetailMindAgent(api_key="")
    with pytest.raises(CredentialsMissingError):
        _ = agent.client


def test_agent_loop_mocked_execution(tmp_path: Path):
    """Verify multi-turn tool calling loop flow with mock Gemini client."""
    # Setup mock Gemini client
    mock_client = MagicMock()

    # Mock response 1: calls summarize_sales
    fc = MagicMock()
    fc.name = "summarize_sales"
    fc.args = {"session_id": "mock_sess"}

    candidate_turn1 = MagicMock()
    candidate_turn1.content = MagicMock()

    resp1 = MagicMock()
    resp1.function_calls = [fc]
    resp1.candidates = [candidate_turn1]
    resp1.usage_metadata = {"prompt_token_count": 500, "candidates_token_count": 50}

    # Mock response 2: produces final answer
    candidate_turn2 = MagicMock()
    candidate_turn2.content = MagicMock()

    resp2 = MagicMock()
    resp2.function_calls = []
    resp2.text = "The total net revenue is $280.00."
    resp2.candidates = [candidate_turn2]
    resp2.usage_metadata = {"prompt_token_count": 600, "candidates_token_count": 60}

    mock_client.models.generate_content.side_effect = [resp1, resp2]

    # Initialize agent with injected mock client
    agent = RetailMindAgent(api_key="valid_key")
    agent._client = mock_client

    # Register synthetic dataset
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "order_id,date,product,quantity,unit_price\n"
        "1,2026-01-01,ItemA,2,50.00\n",
        encoding="utf-8",
    )

    trace_file = tmp_path / "mock_trace.jsonl"
    result = agent.run_task(
        user_query="What is total sales?",
        session_id="mock_sess",
        csv_path=csv_file,
        save_trace_path=trace_file,
    )

    assert result.stop_reason == "FINAL_ANSWER"
    assert result.turns_executed == 2
    assert result.tool_calls_count == 1
    assert "total net revenue is $280.00" in result.final_answer
    assert trace_file.exists()
