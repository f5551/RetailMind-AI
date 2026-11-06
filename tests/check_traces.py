import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
traces_dir = Path("traces")

for f in sorted(traces_dir.glob("*.jsonl")):
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        continue
    first_ev = json.loads(lines[0])
    last_ev = json.loads(lines[-1])
    q = first_ev.get("data", {}).get("query", "")
    sr = last_ev.get("data", {}).get("stop_reason")
    turns = last_ev.get("data", {}).get("turns_executed")
    
    # Check if there are tool error events
    tool_errors = []
    for line in lines:
        ev = json.loads(line)
        if ev.get("event_type") == "tool_execution":
            status = ev.get("data", {}).get("call", {}).get("status")
            if status in ("error", "failure", "approval_required"):
                tool_errors.append((ev.get("data", {}).get("call", {}).get("tool"), status))
                
    print(f"{f.name:35} | Turns: {turns} | StopReason: {sr:20} | Tool status: {tool_errors} | Query: {q[:45]!r}")
