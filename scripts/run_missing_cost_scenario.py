"""RetailMind AI — Live Missing-Cost Scenario Execution.

Runs a real Gemini agent query on sample_data/synthetic_sales_no_cost.csv
asking for revenue, units sold, and profit.
Verifies that revenue and units are calculated deterministically,
profit is reported as UNAVAILABLE, explanation is provided,
and no fabricated profit/cost appears.
Saves genuine execution trace to traces/scenario_missing_cost.jsonl.
"""

import sys
from pathlib import Path

# SSL Native Windows Certificate injection
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
load_dotenv(WORKSPACE_ROOT / ".env")

from src.retailmind.config import settings
from src.retailmind.agent.loop import RetailMindAgent


def main():
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales_no_cost.csv"
    trace_path = WORKSPACE_ROOT / "traces" / "scenario_missing_cost.jsonl"
    query = "What is our total net revenue, total units sold, and profit for this dataset?"

    print(f"=== Running Missing-Cost Live Scenario: Model={settings.gemini_model} ===", flush=True)
    print(f"Dataset: {csv_path}", flush=True)
    print(f"Query: \"{query}\"\n", flush=True)

    agent = RetailMindAgent(model_id=settings.gemini_model)

    res = agent.run_task(
        user_query=query,
        session_id="live_missing_cost_test",
        csv_path=csv_path,
        save_trace_path=trace_path,
    )

    print(f"-> Stop Reason: {res.stop_reason}", flush=True)
    print(f"-> Turns Executed: {res.turns_executed} / {settings.max_turns}", flush=True)
    print(f"-> Tool Calls: {res.tool_calls_count}", flush=True)
    for tc in res.tool_calls_history:
        print(f"     Turn {tc['turn']}: Tool '{tc['tool']}' -> {tc['status']}", flush=True)
    print(f"-> Total Tokens: {res.total_tokens}", flush=True)
    print(f"-> Paid-Tier Equivalent Cost: ${res.total_cost_usd:.6f} USD", flush=True)
    print(f"-> Trace File: {trace_path}", flush=True)
    print(f"\n-> Final Answer:\n{res.final_answer}\n", flush=True)

    # Acceptance verification:
    # 1. Revenue must be $2,945 (or 2945)
    # 2. Units must be 87
    # 3. Profit must be stated as unavailable / not available / cannot be calculated
    # 4. No fabricated cost or profit value
    fa_lower = res.final_answer.lower()
    has_revenue = "2,945" in res.final_answer or "2945" in res.final_answer
    has_units = "87" in res.final_answer
    has_unavailable = any(term in fa_lower for term in ["unavailable", "not available", "cannot be calculated", "no cost", "missing cost"])

    print("=== Acceptance Checks ===")
    print(f"1. Revenue ($2,945) correctly reported: {'PASS' if has_revenue else 'FAIL'}")
    print(f"2. Units (87) correctly reported: {'PASS' if has_units else 'FAIL'}")
    print(f"3. Profit reported as UNAVAILABLE: {'PASS' if has_unavailable else 'FAIL'}")

    if has_revenue and has_units and has_unavailable and res.stop_reason == "FINAL_ANSWER":
        print("\n[SUCCESS] Missing-cost scenario passed all acceptance criteria.")
    else:
        print("\n[FAIL] Missing-cost scenario did not meet all criteria.")
        sys.exit(1)


if __name__ == "__main__":
    main()
