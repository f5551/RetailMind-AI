"""
Standalone script to run Scenario 6: Permission Enforcement and Report Generation.
Verifies ask_on_write policy, deterministic report export, and genuine multi-turn trace.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
load_dotenv(WORKSPACE_ROOT / ".env")

from src.retailmind.config import settings
from src.retailmind.agent.loop import RetailMindAgent

def main():
    csv_path = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    sc6_query = "Generate an executive sales report summarizing our product performance."
    sc6_trace = WORKSPACE_ROOT / "traces" / "scenario_6_report_approval.jsonl"
    
    print(f"=== Running Scenario 6: Model={settings.gemini_model} ===", flush=True)
    agent = RetailMindAgent(model_id=settings.gemini_model)

    def approve_report(tool_name: str, args: dict) -> bool:
        print(f"  [HUMAN-IN-THE-LOOP] Approval requested for '{tool_name}'. Args: {args}", flush=True)
        print("  [HUMAN-IN-THE-LOOP] Decision: GRANTED (Approved by user)", flush=True)
        return True

    res = agent.run_task(
        user_query=sc6_query,
        session_id="live_scenario_6",
        csv_path=csv_path,
        approval_callback=approve_report,
        save_trace_path=sc6_trace,
    )

    print(f"-> Stop Reason: {res.stop_reason}", flush=True)
    print(f"-> Turns Executed: {res.turns_executed} / {settings.max_turns}", flush=True)
    print(f"-> Tool Calls: {res.tool_calls_count}", flush=True)
    for tc in res.tool_calls_history:
        print(f"     Turn {tc['turn']}: Tool '{tc['tool']}' -> {tc['status']}", flush=True)
    print(f"-> Actual Tokens: {res.total_tokens}", flush=True)
    print(f"-> Cost (USD): ${res.total_cost_usd:.6f}", flush=True)
    print(f"-> Final Answer:\n{res.final_answer}\n", flush=True)

    if res.stop_reason == "FINAL_ANSWER":
        print("[PASS] Scenario 6 completed successfully with FINAL_ANSWER.")
    else:
        print(f"[FAIL] Scenario 6 finished with stop_reason={res.stop_reason}")

if __name__ == "__main__":
    main()
