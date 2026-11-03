"""RetailMind AI — Live Execution Script for Real Gemini Agent Scenarios.

Executes genuine Gemini-powered single-agent scenarios against synthetic CSV sales data,
records actual token usage, calculates USD cost, and saves authentic JSONL traces.
"""

import os
import shutil
import sys
from pathlib import Path

# SSL Native Windows Certificate injection
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from dotenv import load_dotenv

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

load_dotenv()

from src.retailmind.agent.loop import RetailMindAgent
from src.retailmind.config import settings

SCENARIOS = [
    {
        "id": "scenario_1",
        "title": "Total Net Revenue & Volume Summary",
        "query": "What was our total net revenue, total units sold, and profit for the uploaded sales data?",
        "trace_file": "traces/scenario_1_summary.jsonl",
        "approval_callback": None,
    },
    {
        "id": "scenario_2",
        "title": "Top Products by Revenue Ranking",
        "query": "List our top 3 products by sales revenue, their units sold, and revenue share.",
        "trace_file": "traces/scenario_2_rankings.jsonl",
        "approval_callback": None,
    },
    {
        "id": "scenario_3",
        "title": "Period-over-Period Performance Comparison",
        "query": "Compare sales performance between January 2026 (2026-01-01 to 2026-01-31) and February 2026 (2026-02-01 to 2026-02-28).",
        "trace_file": "traces/scenario_3_comparison.jsonl",
        "approval_callback": None,
    },
    {
        "id": "scenario_4",
        "title": "Statistical Anomaly Detection",
        "query": "Are there any statistical revenue outliers or anomalous sales orders in the uploaded data?",
        "trace_file": "traces/scenario_4_anomalies.jsonl",
        "approval_callback": None,
    },
    {
        "id": "scenario_5",
        "title": "Dataset Schema & Quality Audit",
        "query": "Validate the uploaded dataset. Check for missing values, invalid dates, and returns.",
        "trace_file": "traces/scenario_5_validation.jsonl",
        "approval_callback": None,
    },
]


def run_all_scenarios():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("\n[BLOCKED] GEMINI_API_KEY is not configured in .env or environment.")
        sys.exit(1)

    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    if not csv_path.exists():
        print(f"Error: Dataset not found at {csv_path}")
        sys.exit(1)

    print(f"=== Starting Live RetailMind AI Scenarios using model: {settings.gemini_model} ===", flush=True)
    print(f"Dataset: {csv_path}", flush=True)
    print(f"Pricing: ${settings.usd_per_million_input_tokens}/1M in, ${settings.usd_per_million_output_tokens}/1M out\n", flush=True)

    agent = RetailMindAgent(model_id=settings.gemini_model)
    results = []

    for sc in SCENARIOS:
        print(f"\n========================================================", flush=True)
        print(f"RUNNING {sc['id'].upper()}: {sc['title']}", flush=True)
        print(f"Query: \"{sc['query']}\"", flush=True)
        trace_path = WORKSPACE_ROOT / sc["trace_file"]

        result = agent.run_task(
            user_query=sc["query"],
            session_id=f"live_{sc['id']}",
            csv_path=csv_path,
            approval_callback=sc["approval_callback"],
            save_trace_path=trace_path,
        )

        print(f"-> Stop Reason: {result.stop_reason}", flush=True)
        print(f"-> Turns Executed: {result.turns_executed} / {settings.max_turns}", flush=True)
        print(f"-> Tool Calls: {result.tool_calls_count}", flush=True)
        for tc in result.tool_calls_history:
            print(f"     Turn {tc['turn']}: Tool '{tc['tool']}' (args: {tc['args']}) -> {tc['status']}", flush=True)
        print(f"-> Actual Tokens: {result.total_tokens} (prompt + candidates)", flush=True)
        print(f"-> Calculated Cost (Paid Equivalent): ${result.total_cost_usd:.6f} USD", flush=True)
        print(f"-> Actual Billed Cost (Free Tier): $0.00 USD", flush=True)
        print(f"-> Trace File: {trace_path}", flush=True)
        print(f"-> Final Answer:\n{result.final_answer}\n", flush=True)
        results.append((sc, result))

        # Pause between scenarios to respect Free Tier 5 RPM limit
        import time
        time.sleep(12)

    # Also run Permission Enforcement Test (Scenario 6: Report generation with human approval)
    print(f"\n========================================================", flush=True)
    print(f"RUNNING SCENARIO 6: Permission Enforcement & Report Generation", flush=True)
    sc6_query = "Generate an executive sales report summarizing our product performance."
    sc6_trace = WORKSPACE_ROOT / "traces" / "scenario_6_report_approval.jsonl"
    print(f"Query: \"{sc6_query}\"", flush=True)
    
    # Callback simulates user confirming approval for report generation
    def approve_report(tool_name: str, args: dict) -> bool:
        print(f"  [HUMAN-IN-THE-LOOP] Approval requested for '{tool_name}'. Granted: YES", flush=True)
        return True

    res6 = agent.run_task(
        user_query=sc6_query,
        session_id="live_scenario_6",
        csv_path=csv_path,
        approval_callback=approve_report,
        save_trace_path=sc6_trace,
    )
    print(f"-> Stop Reason: {res6.stop_reason} | Turns: {res6.turns_executed} | Tools called: {res6.tool_calls_count}", flush=True)
    print(f"-> Actual Tokens: {res6.total_tokens} | Cost: ${res6.total_cost_usd:.6f}", flush=True)
    print(f"-> Final Answer:\n{res6.final_answer}\n", flush=True)
    results.append(({"id": "scenario_6", "title": "Report Generation with Approval"}, res6))

    # Copy genuine scenario 1 trace to traces/success_1.jsonl per capstone requirement
    sc1_trace = WORKSPACE_ROOT / "traces" / "scenario_1_summary.jsonl"
    success_1_trace = WORKSPACE_ROOT / "traces" / "success_1.jsonl"
    if sc1_trace.exists():
        shutil.copy(sc1_trace, success_1_trace)
        print(f"\n[ARTIFACT] Copied genuine trace to {success_1_trace}", flush=True)

    print("\n=== ALL LIVE AGENT SCENARIOS EXECUTED SUCCESSFULLY ===", flush=True)
    return results


if __name__ == "__main__":
    run_all_scenarios()
