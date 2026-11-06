"""RetailMind AI — Failure Trace 13 Execution Runner.

Executes a genuine operational task failure scenario using a Mock LLM that generates
repetitive valid tool calls across max_turns=2, communicating with the REAL MCP server.
Produces traces/max_turns_failure.jsonl directly via the execution tracer.
"""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

sys.stdout.reconfigure(encoding="utf-8")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.retailmind.agent.loop import RetailMindAgent

def run_failure_scenario():
    print("=== RetailMind AI: Failure Trace 13 (MAX_TURNS_REACHED) ===")
    
    trace_path = WORKSPACE_ROOT / "traces" / "max_turns_failure.jsonl"
    sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    session_id = "sess_fail_max_turns"
    user_id = "user_evaluator_13"
    query = "يرجى تحليل المبيعات وتصنيف المنتجات ومقارنة الفترات بالتفصيل دون توقف."
    
    # 1. Initialize agent with max_turns=2 and real MCP transport
    agent = RetailMindAgent(
        api_key="mock_key_evaluator_trace",
        max_turns=2,
        budget_cap_usd=0.10,
        execution_transport="mcp",
    )
    
    # 2. Build mock responses that call real tools on each turn without a final answer
    # Turn 1: Call summarize_sales
    fc1 = MagicMock()
    fc1.name = "summarize_sales"
    fc1.args = {"session_id": session_id}
    
    resp1 = MagicMock()
    resp1.function_calls = [fc1]
    candidate1 = MagicMock()
    candidate1.content = MagicMock()
    resp1.candidates = [candidate1]
    resp1.usage_metadata = {
        "prompt_token_count": 3120,
        "candidates_token_count": 85,
        "cached_content_token_count": 0,
        "thoughts_token_count": 0,
    }
    resp1.text = None
    
    # Turn 2: Call rank_products
    fc2 = MagicMock()
    fc2.name = "rank_products"
    fc2.args = {"session_id": session_id, "metric": "revenue", "top_n": 3}
    
    resp2 = MagicMock()
    resp2.function_calls = [fc2]
    candidate2 = MagicMock()
    candidate2.content = MagicMock()
    resp2.candidates = [candidate2]
    resp2.usage_metadata = {
        "prompt_token_count": 3450,
        "candidates_token_count": 110,
        "cached_content_token_count": 0,
        "thoughts_token_count": 0,
    }
    resp2.text = None
    
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [resp1, resp2]
    agent._client = mock_client
    
    print(f"[CONFIG] Model Mode: Mock LLM (repetitive valid tool calls)")
    print(f"[CONFIG] Transport: REAL MCP (stdio subprocess)")
    print(f"[CONFIG] Max Turns Cap: {agent.max_turns}")
    print(f"[TARGET TRACE]: {trace_path}")
    
    # 3. Execute the agent loop
    result = agent.run_task(
        user_query=query,
        session_id=session_id,
        user_id=user_id,
        csv_path=sample_csv,
        save_trace_path=trace_path,
        language="ar",
        enable_memory=False,
    )
    
    print("\n=== Execution Completed ===")
    print(f"Task ID: {result.task_id}")
    print(f"Stop Reason: {result.stop_reason}")
    print(f"Final Answer: {result.final_answer!r}")
    print(f"Turns Executed: {result.turns_executed}")
    print(f"Tool Calls Count: {result.tool_calls_count}")
    print(f"Execution Transport: {result.execution_transport}")
    
    print("\n[TOOL EXECUTIONS VIA MCP]:")
    for tc in result.tool_calls_history:
        print(f"  - Turn {tc.get('turn')}: Tool={tc.get('tool')} | Transport={tc.get('transport')} | Status={tc.get('status')}")
    
    # 4. Verify the saved JSONL trace file
    print("\n=== Validating Saved JSONL Trace ===")
    if not trace_path.exists():
        print("[FAIL] Trace file was not created!")
        sys.exit(1)
        
    lines = trace_path.read_text(encoding="utf-8").strip().splitlines()
    print(f"Total events in trace: {len(lines)}")
    
    for idx, l in enumerate(lines, 1):
        ev = json.loads(l)
        print(f"  Event {idx}: Turn={ev.get('turn_index')} | Type={ev.get('event_type')}")
        
    last_event = json.loads(lines[-1])
    assert last_event["event_type"] == "task_complete"
    assert last_event["data"]["stop_reason"] == "MAX_TURNS_REACHED"
    assert last_event["data"]["turns_executed"] == 2
    assert last_event["data"]["tool_calls_count"] == 2
    assert last_event["data"]["final_answer"] == ""
    print("\n[VERIFICATION PASS]: Authentic MAX_TURNS_REACHED task failure trace confirmed.")

if __name__ == "__main__":
    run_failure_scenario()
