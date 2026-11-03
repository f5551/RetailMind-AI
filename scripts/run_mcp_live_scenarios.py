"""RetailMind AI — Live Gemini + MCP Execution Demonstration.

Executes real Gemini agent queries routed exclusively through:
Gemini API -> RetailMindAgent -> RetailMindMCPClient -> RetailMind MCP Server (stdio) -> Python Tools -> MCP Response -> Gemini.

Saves genuine JSONL traces with explicit execution_transport="mcp".
"""

import os
import sys
from pathlib import Path

# Windows SSL certificate injection
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
load_dotenv(WORKSPACE_ROOT / ".env")

from src.retailmind.agent.loop import RetailMindAgent
from src.retailmind.config import settings


def main():
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    if not csv_path.exists():
        print(f"Dataset not found at {csv_path}")
        sys.exit(1)

    print(f"=== Starting Live Gemini + MCP Demonstration (Model: {settings.gemini_model}) ===", flush=True)
    print(f"Execution Transport: MCP (stdio subprocess)", flush=True)
    print(f"Dataset: {csv_path}\n", flush=True)

    agent = RetailMindAgent(
        model_id=settings.gemini_model,
        execution_transport="mcp",
    )

    # Task 1: Multi-tool analytical query (Revenue summary + Top products ranking)
    print("========================================================", flush=True)
    print("RUNNING MCP TASK 1: Multi-Tool Analysis (Summary + Ranking)", flush=True)
    q1 = "What was our total net revenue and profit, and which are our top 3 products by revenue?"
    t1_trace = WORKSPACE_ROOT / "traces" / "mcp_live_multi_tool.jsonl"
    print(f"Query: \"{q1}\"", flush=True)

    res1 = agent.run_task(
        user_query=q1,
        session_id="live_mcp_task_1",
        user_id="user_mcp_demo",
        csv_path=csv_path,
        save_trace_path=t1_trace,
    )

    print(f"-> Transport: {res1.execution_transport}", flush=True)
    print(f"-> Stop Reason: {res1.stop_reason}", flush=True)
    print(f"-> Turns: {res1.turns_executed} / {settings.max_turns}", flush=True)
    print(f"-> Tool Calls: {res1.tool_calls_count}", flush=True)
    for tc in res1.tool_calls_history:
        print(f"     Turn {tc['turn']}: Tool '{tc['tool']}' via transport '{tc.get('transport')}' -> {tc['status']}", flush=True)
    print(f"-> Total Tokens: {res1.total_tokens}", flush=True)
    print(f"-> Paid-Tier Cost: ${res1.total_cost_usd:.6f} USD", flush=True)
    print(f"-> Trace File: {t1_trace}", flush=True)
    print(f"-> Final Answer:\n{res1.final_answer}\n", flush=True)

    # Pause to respect rate limits
    import time
    time.sleep(15)

    # Task 2: Multi-tool validation + period comparison
    print("========================================================", flush=True)
    print("RUNNING MCP TASK 2: Validation & Period Comparison via MCP", flush=True)
    q2 = "First validate our dataset quality, then compare sales performance between January 2026 and February 2026."
    t2_trace = WORKSPACE_ROOT / "traces" / "mcp_live_validation_comparison.jsonl"
    print(f"Query: \"{q2}\"", flush=True)

    res2 = agent.run_task(
        user_query=q2,
        session_id="live_mcp_task_2",
        user_id="user_mcp_demo",
        csv_path=csv_path,
        save_trace_path=t2_trace,
    )

    print(f"-> Transport: {res2.execution_transport}", flush=True)
    print(f"-> Stop Reason: {res2.stop_reason}", flush=True)
    print(f"-> Turns: {res2.turns_executed} / {settings.max_turns}", flush=True)
    print(f"-> Tool Calls: {res2.tool_calls_count}", flush=True)
    for tc in res2.tool_calls_history:
        print(f"     Turn {tc['turn']}: Tool '{tc['tool']}' via transport '{tc.get('transport')}' -> {tc['status']}", flush=True)
    print(f"-> Total Tokens: {res2.total_tokens}", flush=True)
    print(f"-> Paid-Tier Cost: ${res2.total_cost_usd:.6f} USD", flush=True)
    print(f"-> Trace File: {t2_trace}", flush=True)
    print(f"-> Final Answer:\n{res2.final_answer}\n", flush=True)

    # Task 3: Memory Recall Test via Live Gemini + MCP
    time.sleep(15)
    print("========================================================", flush=True)
    print("RUNNING MCP TASK 3: Memory Recall Test (Asking follow-up referencing earlier query)", flush=True)
    q3 = "Based on our earlier findings, how did our top product compare to our total revenue?"
    t3_trace = WORKSPACE_ROOT / "traces" / "mcp_live_memory_recall.jsonl"
    print(f"Query: \"{q3}\"", flush=True)

    res3 = agent.run_task(
        user_query=q3,
        session_id="live_mcp_task_3",
        user_id="user_mcp_demo",
        csv_path=csv_path,
        save_trace_path=t3_trace,
    )

    print(f"-> Recalled Memory Count: {res3.recalled_memory_count}", flush=True)
    print(f"-> Stop Reason: {res3.stop_reason}", flush=True)
    print(f"-> Final Answer:\n{res3.final_answer}\n", flush=True)

    print("=== LIVE GEMINI + MCP DEMONSTRATION COMPLETE ===")


if __name__ == "__main__":
    main()
