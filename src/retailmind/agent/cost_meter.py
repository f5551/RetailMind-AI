"""RetailMind AI — Token Usage and Dollar Budget Meter.

Tracks genuine Gemini API token consumption (prompt, output, thinking, tool-use, and cached tokens),
calculates exact dollar cost using official standard pricing, enforces per-task budget cap,
and clearly distinguishes paid-tier equivalent cost from actual billed cost ($0.00 on Free Tier).
Official Reference: https://ai.google.dev/gemini-api/docs/pricing (Verified: 2026-11-03)
Standard Paid-Tier Text Rates:
- Input: $0.25 / 1,000,000 tokens ($0.00000025 / token)
- Output including thinking: $1.50 / 1,000,000 tokens ($0.00000150 / token)
- Cached input: $0.025 / 1,000,000 tokens ($0.000000025 / token)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.retailmind.config import settings


class BudgetExceededError(Exception):
    """Raised when task spending reaches or exceeds the per-task budget cap."""
    pass


@dataclass
class TurnCost:
    turn_index: int
    prompt_tokens: int
    cached_tokens: int
    candidates_tokens: int
    thinking_tokens: int
    tool_use_tokens: int
    total_tokens: int
    turn_cost_usd: float
    cumulative_cost_usd: float
    billed_cost_usd: float = 0.0


@dataclass
class CostTracker:
    budget_cap_usd: float = settings.budget_per_task_usd
    usd_per_million_input: float = settings.usd_per_million_input_tokens       # $0.25 / 1M
    usd_per_million_output: float = settings.usd_per_million_output_tokens     # $1.50 / 1M (includes thinking)
    usd_per_million_cached: float = settings.usd_per_million_cached_tokens     # $0.025 / 1M (verified official)
    
    total_prompt_tokens: int = 0
    total_cached_tokens: int = 0
    total_candidates_tokens: int = 0
    total_thinking_tokens: int = 0
    total_tool_use_tokens: int = 0
    total_tokens: int = 0
    cumulative_cost_usd: float = 0.0
    cumulative_billed_cost_usd: float = 0.0
    billed_status: str = "UNKNOWN_NO_BILLING_EVIDENCE"
    turns: List[TurnCost] = field(default_factory=list)

    def pre_flight_check(self) -> None:
        """Verifies cumulative task spending is strictly below the budget ceiling."""
        if self.cumulative_cost_usd >= self.budget_cap_usd:
            raise BudgetExceededError(
                f"Task cumulative cost ${self.cumulative_cost_usd:.6f} reached or exceeded budget cap of ${self.budget_cap_usd:.2f}."
            )

    def record_usage(self, turn_index: int, usage_metadata: Any) -> TurnCost:
        """Records token metrics from Gemini API response and updates cumulative cost.
        
        Properly extracts and reconciles:
        - prompt_token_count (total input tokens reported by API)
        - cached_content_token_count (cached input tokens within prompt_token_count)
        - candidates_token_count (output tokens, which includes thinking tokens)
        - thoughts_token_count (thinking tokens, subset of candidates)
        - tool_use_prompt_token_count (tool prompt tokens if reported)
        
        Calculates:
        - non_cached_prompt = max(0, raw_prompt - cached)
        - output_tokens = candidates_token_count (or candidates + thinking if separate)
        - turn_total_tokens = non_cached_prompt + cached + output_tokens (avoids double counting)
        - turn_cost = (non_cached_prompt * 0.25/1M) + (cached * 0.025/1M) + (output_tokens * 1.50/1M)
        """
        raw_prompt = 0
        cached = 0
        raw_candidates = 0
        thinking = 0
        tool_prompt = 0

        if usage_metadata:
            if hasattr(usage_metadata, "prompt_token_count"):
                raw_prompt = usage_metadata.prompt_token_count or 0
                cached = getattr(usage_metadata, "cached_content_token_count", 0) or 0
                raw_candidates = usage_metadata.candidates_token_count or 0
                thinking = getattr(usage_metadata, "thoughts_token_count", 0) or 0
                tool_prompt = getattr(usage_metadata, "tool_use_prompt_token_count", 0) or 0
            elif isinstance(usage_metadata, dict):
                raw_prompt = usage_metadata.get("prompt_token_count", 0) or 0
                cached = usage_metadata.get("cached_content_token_count", 0) or 0
                raw_candidates = usage_metadata.get("candidates_token_count", 0) or 0
                thinking = usage_metadata.get("thoughts_token_count", 0) or 0
                tool_prompt = usage_metadata.get("tool_use_prompt_token_count", 0) or 0

        # Non-cached prompt tokens (cached input is a subset of prompt_token_count in Gemini API)
        non_cached_prompt = max(0, raw_prompt - cached)

        if hasattr(usage_metadata, "total_token_count"):
            api_total = getattr(usage_metadata, "total_token_count", None)
        elif isinstance(usage_metadata, dict):
            api_total = usage_metadata.get("total_token_count", None)
        else:
            api_total = None

        # Reconcile thinking tokens and output tokens
        # In Gemini API, candidates_token_count typically includes thoughts_token_count
        if api_total and thinking > 0 and (api_total == raw_prompt + raw_candidates + thinking):
            candidates_output = raw_candidates + thinking
        else:
            candidates_output = raw_candidates

        # Reconcile tool_use_prompt_tokens
        tool_tokens_used = 0
        if tool_prompt > 0:
            tool_tokens_used = tool_prompt
            # If tool_prompt was not subsumed under raw_prompt and total includes it:
            if api_total and (api_total == raw_prompt + candidates_output + tool_prompt):
                non_cached_prompt += tool_prompt
            elif not api_total:
                non_cached_prompt += tool_prompt

        # Total tokens exact reconciliation
        if api_total is not None and api_total > 0:
            turn_total_tokens = api_total
            # Ensure non_cached_prompt + cached + candidates_output equals api_total
            reconciled_sum = non_cached_prompt + cached + candidates_output
            if api_total > reconciled_sum:
                # Assign remainder to non_cached_prompt if tool/system tokens were separate
                diff = api_total - reconciled_sum
                non_cached_prompt += diff
        else:
            turn_total_tokens = non_cached_prompt + cached + candidates_output

        # Paid-tier equivalent rates:
        # Prompt: $0.25 / 1M, Cached: $0.025 / 1M, Output (incl. thinking): $1.50 / 1M
        input_cost = (non_cached_prompt / 1_000_000.0) * self.usd_per_million_input
        cached_cost = (cached / 1_000_000.0) * self.usd_per_million_cached
        output_cost = (candidates_output / 1_000_000.0) * self.usd_per_million_output
        turn_cost = input_cost + cached_cost + output_cost

        self.total_prompt_tokens += non_cached_prompt
        self.total_cached_tokens += cached
        self.total_candidates_tokens += candidates_output
        self.total_thinking_tokens += thinking
        self.total_tool_use_tokens += tool_tokens_used
        self.total_tokens += turn_total_tokens
        self.cumulative_cost_usd += turn_cost
        self.cumulative_billed_cost_usd += 0.0

        tc = TurnCost(
            turn_index=turn_index,
            prompt_tokens=non_cached_prompt,
            cached_tokens=cached,
            candidates_tokens=candidates_output,
            thinking_tokens=thinking,
            tool_use_tokens=tool_tokens_used,
            total_tokens=turn_total_tokens,
            turn_cost_usd=round(turn_cost, 8),
            cumulative_cost_usd=round(self.cumulative_cost_usd, 8),
            billed_cost_usd=0.0,
        )
        self.turns.append(tc)

        # Post-flight budget check
        if self.cumulative_cost_usd >= self.budget_cap_usd:
            raise BudgetExceededError(
                f"Task cumulative cost ${self.cumulative_cost_usd:.6f} reached or exceeded budget cap of ${self.budget_cap_usd:.2f}."
            )

        return tc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "budget_cap_usd": self.budget_cap_usd,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "total_candidates_tokens": self.total_candidates_tokens,
            "total_thinking_tokens": self.total_thinking_tokens,
            "total_tool_use_tokens": self.total_tool_use_tokens,
            "total_tokens": self.total_tokens,
            "cumulative_cost_usd": round(self.cumulative_cost_usd, 8),
            "cumulative_cost_usd_display": round(self.cumulative_cost_usd, 6),
            "cumulative_billed_cost_usd": round(self.cumulative_billed_cost_usd, 6),
            "billed_status": self.billed_status,
            "pricing_source": "Official Gemini API Standard Pricing (https://ai.google.dev/gemini-api/docs/pricing, verified 2026-11-03)",
            "pricing_rates": {
                "input_per_million": self.usd_per_million_input,
                "output_per_million": self.usd_per_million_output,
                "cached_per_million": self.usd_per_million_cached,
            },
        }
