import json
from pathlib import Path

traces = [
    "success_1.jsonl",
    "near_failure_recovery.jsonl",
    "explicit_failure.jsonl",
    "adversarial_attack_a_csv_injection.jsonl",
    "adversarial_attack_b_permission_escalation.jsonl",
    "adversarial_attack_c_memory_poisoning.jsonl",
    "mcp_live_multi_tool.jsonl",
    "mcp_live_validation_comparison.jsonl",
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
    first_ev = lines[0]
    last_ev = lines[-1]
    data = last_ev.get("data", {})
    cost_info = last_ev.get("cost_info", {})
    q = first_ev.get("data", {}).get("query", "")
    print(f"  Start: query=\"{q[:60]}...\"")
    print(f"  Summary: stop={data.get('stop_reason')}, turns={data.get('turns_executed')}, tokens={cost_info.get('total_tokens')}, cost=${cost_info.get('total_cost_usd', 0.0):.6f}, transport={first_ev.get('data', {}).get('execution_transport')}")
