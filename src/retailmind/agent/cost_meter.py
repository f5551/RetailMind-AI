"""RetailMind AI — Token Usage and Dollar Budget Meter."""

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
    candidates_tokens: int
    total_tokens: int
    turn_cost_usd: float
    cumulative_cost_usd: float


@dataclass
class CostTracker:
    budget_cap_usd: float = settings.budget_per_task_usd
    usd_per_million_input: float = settings.usd_per_million_input_tokens
    usd_per_million_output: float = settings.usd_per_million_output_tokens
    total_prompt_tokens: int = 0
    total_candidates_tokens: int = 0
    cumulative_cost_usd: float = 0.0
    turns: List[TurnCost] = field(default_factory=list)

    def pre_flight_check(self) -> None:
        """Verifies cumulative task spending is strictly below the budget ceiling."""
        if self.cumulative_cost_usd >= self.budget_cap_usd:
            raise BudgetExceededError(
                f"Task cumulative cost ${self.cumulative_cost_usd:.6f} reached or exceeded budget cap of ${self.budget_cap_usd:.2f}."
            )

    def record_usage(self, turn_index: int, usage_metadata: Any) -> TurnCost:
        """Records token metrics from Gemini API response and updates cumulative cost."""
        prompt_tokens = 0
        candidates_tokens = 0

        if usage_metadata:
            # Handle object attributes or dict items from google-genai response
            if hasattr(usage_metadata, "prompt_token_count"):
                prompt_tokens = usage_metadata.prompt_token_count or 0
                candidates_tokens = usage_metadata.candidates_token_count or 0
            elif isinstance(usage_metadata, dict):
                prompt_tokens = usage_metadata.get("prompt_token_count", 0)
                candidates_tokens = usage_metadata.get("candidates_token_count", 0)

        total_tokens = prompt_tokens + candidates_tokens

        # Published rates calculation
        input_cost = (prompt_tokens / 1_000_000.0) * self.usd_per_million_input
        output_cost = (candidates_tokens / 1_000_000.0) * self.usd_per_million_output
        turn_cost = input_cost + output_cost

        self.total_prompt_tokens += prompt_tokens
        self.total_candidates_tokens += candidates_tokens
        self.cumulative_cost_usd += turn_cost

        tc = TurnCost(
            turn_index=turn_index,
            prompt_tokens=prompt_tokens,
            candidates_tokens=candidates_tokens,
            total_tokens=total_tokens,
            turn_cost_usd=round(turn_cost, 6),
            cumulative_cost_usd=round(self.cumulative_cost_usd, 6),
        )
        self.turns.append(tc)
        return tc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "budget_cap_usd": self.budget_cap_usd,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_candidates_tokens": self.total_candidates_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_candidates_tokens,
            "cumulative_cost_usd": round(self.cumulative_cost_usd, 6),
            "pricing_rates": {
                "input_per_million": self.usd_per_million_input,
                "output_per_million": self.usd_per_million_output,
            },
        }
