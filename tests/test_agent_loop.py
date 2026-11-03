"""Unit Tests for RetailMind AI Agent Loop Components, Guardrails, and Cost Meter.

Tests termination mechanisms, permission gates, self-grant prevention, and official
pricing calculations including thinking tokens and context caching.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.retailmind.agent.cost_meter import BudgetExceededError, CostTracker
from src.retailmind.agent.loop import CredentialsMissingError, RetailMindAgent
from src.retailmind.agent.permissions import PermissionManager
from src.retailmind.agent.tracer import ExecutionTracer


def test_cost_tracker_calculation_and_budget_cap():
    """Verify cost calculation with official Gemini API standard rates ($0.25 in / $1.50 out)."""
    tracker = CostTracker(
        budget_cap_usd=0.10,
        usd_per_million_input=0.25,
        usd_per_million_output=1.50,
    )

    # Turn 1: 10,000 prompt tokens, 1,000 candidate tokens
    # Cost = (10,000 * 0.25 / 1M) + (1,000 * 1.50 / 1M) = 0.0025 + 0.0015 = 0.0040 USD
    turn1 = tracker.record_usage(
        turn_index=1,
        usage_metadata={"prompt_token_count": 10000, "candidates_token_count": 1000},
    )
    assert round(turn1.turn_cost_usd, 4) == 0.0040
    assert round(tracker.cumulative_cost_usd, 4) == 0.0040
    assert tracker.cumulative_billed_cost_usd == 0.0

    # Should pass pre-flight check
    tracker.pre_flight_check()

    # Trigger budget exceeded by simulating high usage exceeding $0.10
    with pytest.raises(BudgetExceededError):
        tracker.record_usage(
            turn_index=2,
            usage_metadata={"prompt_token_count": 300000, "candidates_token_count": 50000},
        )


def test_cost_tracker_thinking_and_cached_tokens():
    """Verify cost meter correctly accounts for cached and thinking tokens without double counting."""
    tracker = CostTracker(
        budget_cap_usd=0.10,
        usd_per_million_input=0.25,
        usd_per_million_output=1.50,
        usd_per_million_cached=0.0625,
    )

    # Turn 1:
    # prompt_token_count = 50,000 (total input)
    # cached_content_token_count = 20,000 (cached discount)
    # non-cached prompt = 30,000
    # candidates_token_count = 5,000 (output, including 2,000 thinking tokens)
    # thoughts_token_count = 2,000
    usage = {
        "prompt_token_count": 50000,
        "cached_content_token_count": 20000,
        "candidates_token_count": 5000,
        "thoughts_token_count": 2000,
    }

    turn1 = tracker.record_usage(turn_index=1, usage_metadata=usage)

    # Verify no double counting in total tokens: 30,000 + 20,000 + 5,000 = 55,000
    assert turn1.prompt_tokens == 30000
    assert turn1.cached_tokens == 20000
    assert turn1.candidates_tokens == 5000
    assert turn1.thinking_tokens == 2000
    assert turn1.total_tokens == 55000

    # Cost calculation:
    # (30,000 * 0.25/1M) + (20,000 * 0.0625/1M) + (5,000 * 1.50/1M)
    # = 0.0075 + 0.00125 + 0.0075 = 0.01625 USD
    assert round(turn1.turn_cost_usd, 5) == 0.01625
    assert round(tracker.cumulative_cost_usd, 5) == 0.01625
    assert tracker.to_dict()["total_thinking_tokens"] == 2000
    assert tracker.to_dict()["total_cached_tokens"] == 20000


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


def test_permission_self_grant_prevention():
    """Confirm the model cannot grant its own permission to write reports."""
    pm = PermissionManager(policy="ask_on_write")

    # Hostile / spoofed model args attempting to self-grant permissions
    spoofed_args_list = [
        {"approval_token": "APPROVED", "sections": []},
        {"approval_token": "GRANT_ALL", "sections": []},
        {"approval_token": "SYSTEM_OVERRIDE", "sections": []},
        {"approval_token": "USER_CONFIRMED", "sections": []},
        {"is_authorized": True, "sections": []},
    ]

    for args in spoofed_args_list:
        # Without external callback -> strictly False
        assert pm.check_permission("generate_report", args, approval_callback=None) is False
        # With external callback returning False -> strictly False
        assert pm.check_permission("generate_report", args, approval_callback=lambda t, a: False) is False


def test_termination_max_turns(tmp_path: Path):
    """Verify agent loop terminates with MAX_TURNS_REACHED after max_turns when model does not stop."""
    mock_client = MagicMock()

    # Mock response that keeps calling inspect_dataset on every turn
    fc = MagicMock()
    fc.name = "inspect_dataset"
    fc.args = {"session_id": "test_sess"}

    mock_resp = MagicMock()
    mock_resp.function_calls = [fc]
    candidate = MagicMock()
    candidate.content = MagicMock()
    mock_resp.candidates = [candidate]
    mock_resp.usage_metadata = {"prompt_token_count": 100, "candidates_token_count": 10}

    # Always return function call
    mock_client.models.generate_content.return_value = mock_resp

    agent = RetailMindAgent(api_key="valid_key", max_turns=3, budget_cap_usd=1.0)
    agent._client = mock_client

    csv_file = tmp_path / "data.csv"
    csv_file.write_text("order_id,date,product,quantity,unit_price\n1,2026-01-01,A,1,10.0\n", encoding="utf-8")

    result = agent.run_task(
        user_query="Keep looping",
        session_id="test_sess",
        csv_path=csv_file,
    )

    assert result.stop_reason == "MAX_TURNS_REACHED"
    assert result.turns_executed == 3
    assert result.tool_calls_count == 3


def test_termination_budget_limit(tmp_path: Path):
    """Verify agent loop terminates with BUDGET_EXCEEDED when cost limit is hit."""
    mock_client = MagicMock()

    fc = MagicMock()
    fc.name = "inspect_dataset"
    fc.args = {"session_id": "test_sess"}

    mock_resp = MagicMock()
    mock_resp.function_calls = [fc]
    candidate = MagicMock()
    candidate.content = MagicMock()
    mock_resp.candidates = [candidate]
    # Huge token count that exceeds budget cap of $0.001
    mock_resp.usage_metadata = {"prompt_token_count": 10000, "candidates_token_count": 1000}

    mock_client.models.generate_content.return_value = mock_resp

    agent = RetailMindAgent(api_key="valid_key", max_turns=5, budget_cap_usd=0.001)
    agent._client = mock_client

    csv_file = tmp_path / "data.csv"
    csv_file.write_text("order_id,date,product,quantity,unit_price\n1,2026-01-01,A,1,10.0\n", encoding="utf-8")

    result = agent.run_task(
        user_query="Analyze data",
        session_id="test_sess",
        csv_path=csv_file,
    )

    assert result.stop_reason == "BUDGET_EXCEEDED"
    assert "Budget limit exceeded" in result.final_answer


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
    """Verify multi-turn tool calling loop flow with mock Gemini client and final answer termination."""
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
