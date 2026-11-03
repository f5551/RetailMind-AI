"""RetailMind AI — Live Execution Script for 5 Gemini Scenarios.

Executes genuine Gemini-powered single-agent scenarios using synthetic CSV data,
records actual token usage, cost, and saves authentic JSONL traces.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

load_dotenv()

from src.retailmind.agent.loop import CredentialsMissingError, RetailMindAgent
from src.retailmind.config import settings

SCENARIOS = [
    {
        "id": "scenario_1",
        "title": "Total Net Revenue & Volume Summary",
        "query": "What was our total net revenue and how many units were sold?",
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
        "query": "Are there any statistical revenue outliers or anomalous sales orders in the data?",
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
        print("Please configure your GEMINI_API_KEY before running live scenarios.")
        print("Never fabricate fake API calls or fake traces.\n")
        sys.exit(1)

    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    if not csv_path.exists():
        print(f"Error: Dataset not found at {csv_path}")
        sys.exit(1)

    print(f"=== Starting Live RetailMind AI Scenarios using model: {settings.gemini_model} ===")
    print(f"Dataset: {csv_path}\n")

    agent = RetailMindAgent()
    results = []

    for sc in SCENARIOS:
        print(f"\n--- Running {sc['id']}: {sc['title']} ---")
        print(f"Query: \"{sc['query']}\"")
        trace_path = WORKSPACE_ROOT / sc["trace_file"]

        result = agent.run_task(
            user_query=sc["query"],
            session_id=f"live_{sc['id']}",
            csv_path=csv_path,
            approval_callback=sc["approval_callback"],
            save_trace_path=trace_path,
        )

        print(f"Outcome: {result.stop_reason} | Turns: {result.turns_executed} | Tools called: {result.tool_calls_count}")
        print(f"Tokens: {result.total_tokens} | Cost: ${result.total_cost_usd:.6f}")
        print(f"Final Answer:\n{result.final_answer}\n")
        print(f"Trace saved to: {trace_path}")
        results.append(result)

    print("\n=== All 5 Scenarios Completed Successfully ===")
    return results


if __name__ == "__main__":
    run_all_scenarios()
