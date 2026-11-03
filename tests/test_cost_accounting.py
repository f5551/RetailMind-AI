"""RetailMind AI — Formal Cost Accounting & Pricing Verification Tests.

Provides rigorous, independent mathematical assertions for:
1. Normal input/output costs ($0.25 / 1M prompt, $1.50 / 1M output).
2. Cached input discount rate ($0.025 / 1M, verified official rate).
3. Thinking token accounting (billed at $1.50 / 1M output, reported distinctly).
4. Multi-turn sequential model call cost accumulation.
5. Floating-point precision and exact cost aggregation.
6. Budget cap enforcement ($0.10 USD).
7. Trace reconciliation verifying all active traces match token counts and exact arithmetic.
"""

import glob
import json
from pathlib import Path
import pytest

from src.retailmind.agent.cost_meter import BudgetExceededError, CostTracker
from src.retailmind.config import settings


def test_1_normal_input_output_cost():
    """Verify exact cost for normal non-cached input and output tokens."""
    tracker = CostTracker(
        budget_cap_usd=0.10,
        usd_per_million_input=0.25,
        usd_per_million_output=1.50,
        usd_per_million_cached=0.025,
    )

    # 10,000 prompt tokens, 1,000 candidate tokens
    # Expected: (10,000 * 0.25 / 1M) + (1,000 * 1.50 / 1M) = 0.0025 + 0.0015 = 0.0040 USD
    tc = tracker.record_usage(
        turn_index=1,
        usage_metadata={"prompt_token_count": 10000, "candidates_token_count": 1000},
    )

    assert tc.prompt_tokens == 10000
    assert tc.cached_tokens == 0
    assert tc.candidates_tokens == 1000
    assert tc.thinking_tokens == 0
    assert tc.total_tokens == 11000
    assert abs(tc.turn_cost_usd - 0.0040) < 1e-8
    assert abs(tracker.cumulative_cost_usd - 0.0040) < 1e-8


def test_2_cached_input_cost():
    """Verify cached input is billed strictly at $0.025 / 1M and not charged twice."""
    tracker = CostTracker(
        budget_cap_usd=0.10,
        usd_per_million_input=0.25,
        usd_per_million_output=1.50,
        usd_per_million_cached=0.025,
    )

    # 100,000 total prompt tokens, of which 60,000 are cached
    # Non-cached prompt = 40,000 -> 40,000 * 0.25 / 1M = 0.0100 USD
    # Cached prompt = 60,000 -> 60,000 * 0.025 / 1M = 0.0015 USD
    # Output = 5,000 -> 5,000 * 1.50 / 1M = 0.0075 USD
    # Expected total = 0.0100 + 0.0015 + 0.0075 = 0.0190 USD
    usage = {
        "prompt_token_count": 100000,
        "cached_content_token_count": 60000,
        "candidates_token_count": 5000,
    }
    tc = tracker.record_usage(turn_index=1, usage_metadata=usage)

    assert tc.prompt_tokens == 40000
    assert tc.cached_tokens == 60000
    assert tc.candidates_tokens == 5000
    assert tc.total_tokens == 105000  # 40,000 + 60,000 + 5,000 (NO double counting)
    assert abs(tc.turn_cost_usd - 0.0190) < 1e-8

    # Ensure rate is strictly $0.025 and would fail if old 0.0625 was used
    wrong_cached_calc = (40000 * 0.25 / 1e6) + (60000 * 0.0625 / 1e6) + (5000 * 1.50 / 1e6)
    assert abs(tc.turn_cost_usd - wrong_cached_calc) > 1e-4


def test_3_thinking_token_cost():
    """Verify thinking tokens are billed at $1.50 / 1M output rate and reported distinctly."""
    tracker = CostTracker(
        budget_cap_usd=0.10,
        usd_per_million_input=0.25,
        usd_per_million_output=1.50,
        usd_per_million_cached=0.025,
    )

    # In Gemini API, candidates_token_count includes thoughts_token_count
    # 20,000 prompt tokens, 8,000 candidate tokens (including 3,000 thinking tokens)
    # Expected cost: (20,000 * 0.25 / 1M) + (8,000 * 1.50 / 1M) = 0.0050 + 0.0120 = 0.0170 USD
    usage = {
        "prompt_token_count": 20000,
        "candidates_token_count": 8000,
        "thoughts_token_count": 3000,
        "total_token_count": 28000,
    }
    tc = tracker.record_usage(turn_index=1, usage_metadata=usage)

    assert tc.prompt_tokens == 20000
    assert tc.candidates_tokens == 8000
    assert tc.thinking_tokens == 3000
    assert tc.total_tokens == 28000
    assert abs(tc.turn_cost_usd - 0.0170) < 1e-8


def test_4_multiple_sequential_model_calls():
    """Verify token usage and dollar costs accumulate correctly across multi-turn tasks."""
    tracker = CostTracker(
        budget_cap_usd=0.10,
        usd_per_million_input=0.25,
        usd_per_million_output=1.50,
        usd_per_million_cached=0.025,
    )

    # Turn 1: 1,500 in, 50 out -> 0.000375 + 0.000075 = 0.000450 USD
    tc1 = tracker.record_usage(1, {"prompt_token_count": 1500, "candidates_token_count": 50})
    assert abs(tc1.turn_cost_usd - 0.000450) < 1e-8
    assert abs(tc1.cumulative_cost_usd - 0.000450) < 1e-8

    # Turn 2: 2,000 in, 100 out -> 0.000500 + 0.000150 = 0.000650 USD
    tc2 = tracker.record_usage(2, {"prompt_token_count": 2000, "candidates_token_count": 100})
    assert abs(tc2.turn_cost_usd - 0.000650) < 1e-8
    assert abs(tc2.cumulative_cost_usd - 0.001100) < 1e-8

    # Turn 3: 2,500 in, 200 out -> 0.000625 + 0.000300 = 0.000925 USD
    tc3 = tracker.record_usage(3, {"prompt_token_count": 2500, "candidates_token_count": 200})
    assert abs(tc3.turn_cost_usd - 0.000925) < 1e-8
    assert abs(tc3.cumulative_cost_usd - 0.002025) < 1e-8

    summary = tracker.to_dict()
    assert summary["total_prompt_tokens"] == 6000
    assert summary["total_candidates_tokens"] == 350
    assert summary["total_tokens"] == 6350
    assert abs(summary["cumulative_cost_usd"] - 0.002025) < 1e-8


def test_5_exact_cost_aggregation_precision():
    """Verify that cumulative cost does not suffer from rounding drift across many turns."""
    tracker = CostTracker(budget_cap_usd=0.50, usd_per_million_input=0.25, usd_per_million_output=1.50)

    # 10 turns of 1,333 prompt tokens and 133 candidate tokens each
    expected_turn_cost = (1333 * 0.25 / 1e6) + (133 * 1.50 / 1e6)  # 0.00033325 + 0.0001995 = 0.00053275
    for turn in range(1, 11):
        tracker.record_usage(turn, {"prompt_token_count": 1333, "candidates_token_count": 133})

    expected_cumulative = expected_turn_cost * 10  # 0.00532750
    assert abs(tracker.cumulative_cost_usd - expected_cumulative) < 1e-10


def test_6_budget_threshold_behavior():
    """Verify that budget limit ($0.10) is strictly enforced in pre-flight and post-flight."""
    tracker = CostTracker(budget_cap_usd=0.10, usd_per_million_input=0.25, usd_per_million_output=1.50)

    # Spend $0.095 (under limit)
    # 300,000 in ($0.075) + 13,333.33 out ($0.020) = $0.095
    tracker.record_usage(1, {"prompt_token_count": 300000, "candidates_token_count": 13333})
    assert tracker.cumulative_cost_usd < 0.10
    tracker.pre_flight_check()  # Should pass

    # Next turn exceeds $0.10 ceiling -> raises BudgetExceededError post-flight
    with pytest.raises(BudgetExceededError):
        tracker.record_usage(2, {"prompt_token_count": 50000, "candidates_token_count": 5000})

    # Subsequent pre-flight check must strictly fail
    with pytest.raises(BudgetExceededError):
        tracker.pre_flight_check()


def test_7_trace_reconciliation():
    """Verify that every active JSONL trace in traces/ has consistent arithmetic and token counts."""
    trace_files = glob.glob("traces/scenario_*.jsonl") + ["traces/success_1.jsonl"]
    assert len(trace_files) >= 7, f"Expected at least 7 active trace files, found {len(trace_files)}"

    for tf_path in trace_files:
        with open(tf_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f]

        # Final line is task_complete with cost_info
        assert lines[-1]["event_type"] == "task_complete", f"{tf_path} last event is not task_complete"
        cost_info = lines[-1]["cost_info"]

        p = cost_info["total_prompt_tokens"]
        c = cost_info.get("total_cached_tokens", 0)
        o = cost_info["total_candidates_tokens"]
        tot = cost_info["total_tokens"]
        recorded_cost = cost_info["cumulative_cost_usd"]

        # 1. Total tokens must equal prompt + cached + output
        assert tot == p + c + o, f"{tf_path}: total_tokens ({tot}) != p({p}) + c({c}) + o({o})"

        # 2. Recorded cost must match exact arithmetic
        expected_cost = (p * 0.25 / 1e6) + (c * 0.025 / 1e6) + (o * 1.50 / 1e6)
        assert abs(recorded_cost - expected_cost) < 1e-5, (
            f"{tf_path}: recorded_cost ({recorded_cost}) does not match expected ({expected_cost})"
        )
