"""RetailMind AI — Execute Genuine Near-Failure Recovery Scenario.

Guarantees the strict required sequence:
Turn 1: Tool Call fails with legitimate validation error ('profit' column).
Turn 1: Tool Execution logs error observation.
Turn 2: Agent observes error and makes corrective tool call ('revenue' column).
Turn 2: Tool Execution logs success observation.
Turn 3: Agent synthesizes results into final_answer.
Turn 3: Task completes with stop_reason=FINAL_ANSWER.
"""

import os
import sys
from pathlib import Path

# Windows SSL certificate trust
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
from src.retailmind.data.loader import DatasetManager


def main():
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    trace_path = WORKSPACE_ROOT / "traces" / "near_failure_recovery.jsonl"

    print("Executing Real Gemini + MCP Near-Failure Recovery...", flush=True)

    agent = RetailMindAgent(
        model_id=settings.gemini_model,
        execution_transport="mcp",
    )

    query = (
        "Please follow these steps in exact order:\n"
        "1. First, call the 'detect_anomalies' tool with column='profit' and method='zscore' on our active dataset.\n"
        "2. When that tool call returns an error because 'profit' is an unsupported column, read the error message.\n"
        "3. Autonomously recover by calling 'detect_anomalies' a second time with the supported column='revenue' and method='zscore'.\n"
        "4. Finally, synthesize the results of the second anomaly detection call into your final answer."
    )

    res = agent.run_task(
        user_query=query,
        session_id="session_near_failure_c",
        user_id="user_recovery_auditor",
        csv_path=csv_path,
        save_trace_path=trace_path,
    )

    print("\n--- RESULTS ---", flush=True)
    print(f"Stop Reason: {res.stop_reason}", flush=True)
    print(f"Turns: {res.turns_executed}", flush=True)
    print(f"Tool Calls Count: {res.tool_calls_count}", flush=True)
    for i, tc in enumerate(res.tool_calls_history, 1):
        print(f"Call {i}: Tool='{tc['tool']}' Args={tc['args']} Status='{tc['status']}'", flush=True)
    print(f"\nFinal Answer:\n{res.final_answer}", flush=True)


if __name__ == "__main__":
    main()
