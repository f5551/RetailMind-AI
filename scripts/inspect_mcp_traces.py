import json
from pathlib import Path

traces = [
    "mcp_live_multi_tool.jsonl",
    "mcp_live_validation_comparison.jsonl",
    "mcp_live_memory_recall.jsonl",
]

for name in traces:
    p = Path("traces") / name
    if not p.exists():
        print(f"File {name} does not exist!")
        continue
    print(f"\n==================================================")
    print(f"TRACE FILE: {name} ({p.stat().st_size} bytes)")
    lines = [json.loads(line) for line in p.read_text(encoding="utf-8").strip().splitlines() if line.strip()]
    print(f"Total events: {len(lines)}")
    for i, ev in enumerate(lines):
        ev_type = ev.get("event_type")
        turn = ev.get("turn_index")
        data = ev.get("data", {})
        if ev_type == "tool_execution":
            call = data.get("call", {})
            print(f"  [{i}] TOOL_EXECUTION (Turn {turn}): tool={call.get('tool')}, transport={data.get('transport')}, status={call.get('status')}")
        elif ev_type == "model_turn":
            calls = data.get("calls", [])
            call_names = [c.get("name") for c in calls] if calls else "final_text"
            print(f"  [{i}] MODEL_TURN (Turn {turn}): action={data.get('action')}, calls={call_names}")
        elif ev_type == "task_completed":
            summ = ev.get("session_summary", {})
            print(f"  [{i}] TASK_COMPLETED: stop={summ.get('stop_reason')}, turns={summ.get('turns_executed')}, tokens={summ.get('total_tokens')}, cost=${summ.get('total_cost_usd'):.6f}, transport={summ.get('execution_transport')}")
        else:
            print(f"  [{i}] {ev_type}")
