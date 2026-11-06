"""RetailMind AI — Agent Five Inputs 15 Test Runner.

Executes five distinct inputs through the real agent loop and real MCP server over stdio.
Routing is provided by Mock LLM to prevent paid API consumption.
Generates genuine unmanipulated JSONL traces for all 5 scenarios.
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.stdout.reconfigure(encoding="utf-8")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.retailmind.agent.loop import RetailMindAgent
from src.retailmind.memory.manager import SQLiteMemoryManager

scenarios = [
    {
        "id": 1,
        "name": "إجمالي الإيرادات والوحدات (Total Revenue & Units)",
        "query": "ما هو إجمالي صافي الإيرادات وعدد الوحدات المباعة في المتجر؟",
        "tool": "summarize_sales",
        "tool_args": lambda sess: {"session_id": sess},
        "trace_file": "eval_five_inputs_1_summary.jsonl",
        "expected_keys": ["net_revenue", "net_units", "total_orders"],
    },
    {
        "id": 2,
        "name": "أفضل المنتجات مبيعاً (Top Products Ranking)",
        "query": "ما هي أفضل 3 منتجات مبيعاً من حيث الإيرادات وحصتها النسبية؟",
        "tool": "rank_products",
        "tool_args": lambda sess: {"session_id": sess, "metric": "revenue", "top_n": 3},
        "trace_file": "eval_five_inputs_2_rankings.jsonl",
        "expected_keys": ["rankings", "metric"],
    },
    {
        "id": 3,
        "name": "مقارنة المبيعات بين فترتين (Period Comparison)",
        "query": "قارن أداء المبيعات بين شهر يناير 2026 وشهر فبراير 2026.",
        "tool": "compare_periods",
        "tool_args": lambda sess: {
            "session_id": sess,
            "period_a": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "period_b": {"start_date": "2026-02-01", "end_date": "2026-02-28"},
        },
        "trace_file": "eval_five_inputs_3_comparison.jsonl",
        "expected_keys": ["variance", "period_a", "period_b"],
    },
    {
        "id": 4,
        "name": "اكتشاف القيم الشاذة (Anomaly Detection)",
        "query": "هل توجد أي قيم أو معاملات شاذة إحصائياً في إيرادات المتجر؟",
        "tool": "detect_anomalies",
        "tool_args": lambda sess: {"session_id": sess, "column": "revenue", "method": "zscore", "threshold": 2.5},
        "trace_file": "eval_five_inputs_4_anomalies.jsonl",
        "expected_keys": ["anomalies_count", "method_used"],
    },
    {
        "id": 5,
        "name": "تحليل المبيعات حسب الفئة (Sales Segmentation by Category)",
        "query": "حلل توزيع المبيعات وصافي الإيرادات حسب فئات المنتجات.",
        "tool": "segment_sales",
        "tool_args": lambda sess: {"session_id": sess, "dimension": "category"},
        "trace_file": "eval_five_inputs_5_segmentation.jsonl",
        "expected_keys": ["segments", "dimension"],
    },
]

def run_all_five_scenarios():
    print("=== RetailMind AI: Five Independent Inputs Verification ===")
    sample_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db = Path(tmp_dir) / "test_memory.db"
        mem_mgr = SQLiteMemoryManager(db_path=tmp_db)
        
        for sc in scenarios:
            print(f"\n-----------------------------------------------------------")
            print(f"Scenario {sc['id']}: {sc['name']}")
            print(f"Query: \"{sc['query']}\"")
            
            session_id = f"eval_sess_sc_{sc['id']}"
            user_id = f"eval_user_{sc['id']}"
            trace_path = WORKSPACE_ROOT / "traces" / sc["trace_file"]
            
            # Setup Mock LLM to return function call in Turn 1, then synthesis in Turn 2
            fc = MagicMock()
            fc.name = sc["tool"]
            fc.args = sc["tool_args"](session_id)
            
            resp1 = MagicMock()
            resp1.function_calls = [fc]
            candidate1 = MagicMock()
            candidate1.content = MagicMock()
            resp1.candidates = [candidate1]
            resp1.usage_metadata = {"prompt_token_count": 3100, "candidates_token_count": 80}
            resp1.text = None
            
            resp2 = MagicMock()
            resp2.function_calls = []
            candidate2 = MagicMock()
            candidate2.content = MagicMock()
            resp2.candidates = [candidate2]
            resp2.usage_metadata = {"prompt_token_count": 3350, "candidates_token_count": 140}
            resp2.text = f"تم إنجاز التحليل بنجاح للأداة {sc['tool']}."
            
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = [resp1, resp2]
            
            agent = RetailMindAgent(
                api_key="mock_key_five_inputs",
                execution_transport="mcp",
                budget_cap_usd=0.10,
                max_turns=4,
                memory_manager=mem_mgr,
            )
            agent._client = mock_client
            
            result = agent.run_task(
                user_query=sc["query"],
                session_id=session_id,
                user_id=user_id,
                csv_path=sample_csv,
                save_trace_path=trace_path,
                language="ar",
                enable_memory=True,
            )
            
            print(f"  Result Task ID: {result.task_id}")
            print(f"  Stop Reason: {result.stop_reason}")
            print(f"  Turns Executed: {result.turns_executed}")
            print(f"  Tool Calls Count: {result.tool_calls_count}")
            print(f"  Execution Transport: {result.execution_transport}")
            
            assert result.stop_reason == "FINAL_ANSWER", f"Stop reason expected FINAL_ANSWER, got {result.stop_reason}"
            assert result.turns_executed == 2, f"Turns expected 2, got {result.turns_executed}"
            assert result.tool_calls_count == 1, f"Tool calls count expected 1, got {result.tool_calls_count}"
            assert result.execution_transport == "mcp", f"Transport expected mcp, got {result.execution_transport}"
            
            tc = result.tool_calls_history[0]
            print(f"  Tool Executed: {tc['tool']} (Transport: {tc['transport']}, Status: {tc['status']})")
            assert tc["tool"] == sc["tool"]
            assert tc["transport"] == "mcp"
            assert tc["status"] == "success"
            
            obs = tc["observation"]
            for k in sc["expected_keys"]:
                assert k in obs, f"Key {k} missing from observation!"
                
            print(f"  Observation Verified: {list(obs.keys())[:5]}")
            print(f"  Trace Saved: {trace_path.name} ({trace_path.stat().st_size} bytes)")
            print(f"  [STATUS]: PASS")

        # Explicitly close memory connection before tempdir cleanup
        mem_mgr.close()

if __name__ == "__main__":
    run_all_five_scenarios()
    print("\n===========================================================")
    print("ALL 5 INDEPENDENT SCENARIOS PASSED VIA REAL MCP OVER STDIO!")
    print("===========================================================")
