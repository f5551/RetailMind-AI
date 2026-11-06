"""RetailMind AI — Live Verification 11 Test Runner.

Executes ONE live query with real Gemini API and real MCP over stdio.
Query: "ما إجمالي صافي الإيرادات وعدد الوحدات المباعة في بيانات المتجر؟"
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Windows UTF-8 stdout
sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# Load .env
from dotenv import load_dotenv
load_dotenv(WORKSPACE_ROOT / ".env")

from src.retailmind.config import settings
from src.retailmind.agent.loop import RetailMindAgent
from src.retailmind.memory.manager import SQLiteMemoryManager

def run_live_test():
    print("=== RetailMind AI: Live Verification 11 ===")
    
    # Verify API key is present locally
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("[BLOCKED] GEMINI_API_KEY is not configured in environment or .env.")
        sys.exit(1)
        
    print(f"[CONFIG] Model configured: {settings.gemini_model}")
    print(f"[CONFIG] Transport: MCP (stdio subprocess)")
    print(f"[CONFIG] API Key present: True (Length: {len(api_key)}, Prefix: {api_key[:4]}...)")
    
    # Use isolated temp directory for SQLite database
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db_path = Path(tmp_dir) / "test_memory.db"
        mem_mgr = SQLiteMemoryManager(db_path=tmp_db_path)
        
        # Initialize Agent with Real Gemini and Real MCP
        agent = RetailMindAgent(
            api_key=api_key,
            model_id=settings.gemini_model,
            execution_transport="mcp",
            budget_cap_usd=0.10,
            max_turns=8,
            memory_manager=mem_mgr,
        )
        
        sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
        trace_path = WORKSPACE_ROOT / "traces" / "live_verification_11.jsonl"
        
        query = "ما إجمالي صافي الإيرادات وعدد الوحدات المباعة في بيانات المتجر؟"
        session_id = "live_sess_11"
        user_id = "live_tester"
        
        print(f"\n[QUERY] \"{query}\"")
        print("[DISPATCHING] Calling RetailMindAgent.run_task with real Gemini API...")
        
        try:
            result = agent.run_task(
                user_query=query,
                session_id=session_id,
                user_id=user_id,
                csv_path=sample_csv,
                save_trace_path=trace_path,
                language="ar",
                enable_memory=True,
            )
        except Exception as e:
            print(f"[FAILURE] Agent execution raised exception: {type(e).__name__}: {e}")
            sys.exit(1)
            
        print("\n=== Agent Execution Completed ===")
        print(f"Task ID: {result.task_id}")
        print(f"Stop Reason: {result.stop_reason}")
        print(f"Turns Executed: {result.turns_executed}")
        print(f"Tool Calls Count: {result.tool_calls_count}")
        print(f"Total Tokens: {result.total_tokens}")
        print(f"Total Cost USD: ${result.total_cost_usd:.6f}")
        print(f"Execution Transport: {result.execution_transport}")
        
        print("\n[TOOL CALLS HISTORY]:")
        for idx, tc in enumerate(result.tool_calls_history, 1):
            print(f"  Step {idx}:")
            print(f"    Tool: {tc.get('tool')}")
            print(f"    Arguments: {json.dumps(tc.get('args'), ensure_ascii=False)}")
            print(f"    Transport: {tc.get('transport')}")
            print(f"    Status: {tc.get('status')}")
            obs = tc.get("observation", {})
            print(f"    Observation Revenue: {obs.get('net_revenue')}")
            print(f"    Observation Units: {obs.get('net_units')}")
            print(f"    Observation Orders: {obs.get('total_orders')}")
            
        print("\n[FINAL ANSWER]:")
        print(result.final_answer)
        
        # Read and inspect JSONL trace
        print("\n=== Trace Verification ===")
        if trace_path.exists():
            trace_lines = trace_path.read_text(encoding="utf-8").strip().splitlines()
            print(f"Trace events logged: {len(trace_lines)}")
            for l in trace_lines:
                ev = json.loads(l)
                print(f"  - Turn {ev.get('turn_index')}: {ev.get('event_type')}")
        else:
            print("[WARN] Trace file not found on disk.")

if __name__ == "__main__":
    run_live_test()
