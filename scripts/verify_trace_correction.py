import os
import shutil
import hashlib
import json
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.makedirs("traces/archive", exist_ok=True)

# 1. Extract pristine original explicit_failure.jsonl from git to archive
original_git_data = subprocess.check_output(["git", "show", "HEAD:traces/explicit_failure.jsonl"])
archived_path = "traces/archive/explicit_failure_permission_gated.jsonl"
with open(archived_path, "wb") as f:
    f.write(original_git_data)

# 2. Copy max_turns_failure.jsonl to traces/explicit_failure.jsonl
source_max_turns = "traces/max_turns_failure.jsonl"
target_explicit = "traces/explicit_failure.jsonl"
shutil.copy2(source_max_turns, target_explicit)

def get_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_jsonl(path):
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line_str = line.strip()
            if line_str:
                events.append((i, json.loads(line_str)))
    return events

src_hash = get_hash(source_max_turns)
tgt_hash = get_hash(target_explicit)
arch_hash = get_hash(archived_path)

# Verify traces/explicit_failure.jsonl
events_explicit = verify_jsonl(target_explicit)
last_explicit = events_explicit[-1][1]
explicit_stop_reason = last_explicit.get("data", {}).get("stop_reason")
explicit_final_answer = last_explicit.get("data", {}).get("final_answer")

# Verify archived file
events_arch = verify_jsonl(archived_path)
last_arch = events_arch[-1][1]
arch_stop_reason = last_arch.get("data", {}).get("stop_reason")
arch_final_answer = last_arch.get("data", {}).get("final_answer")

print(f"SRC_MAX_TURNS_SHA256: {src_hash}")
print(f"TGT_EXPLICIT_SHA256:  {tgt_hash}")
print(f"SHA256_MATCH:         {src_hash == tgt_hash}")
print(f"ARCHIVED_SHA256:      {arch_hash}")
print("---")
print(f"EXPLICIT_EVENTS_COUNT: {len(events_explicit)}")
print(f"EXPLICIT_STOP_REASON:  {explicit_stop_reason}")
print(f"EXPLICIT_FINAL_ANSWER: {repr(explicit_final_answer)}")
print(f"EXPLICIT_TURNS:        {last_explicit.get('data', {}).get('turns_executed')}")
print(f"EXPLICIT_TOOLS_COUNT:  {last_explicit.get('data', {}).get('tool_calls_count')}")
print("---")
print(f"ARCHIVED_EVENTS_COUNT: {len(events_arch)}")
print(f"ARCHIVED_STOP_REASON:  {arch_stop_reason}")
print(f"ARCHIVED_FINAL_ANSWER_LEN: {len(arch_final_answer or '')}")
print(f"ARCHIVED_TURNS:        {last_arch.get('data', {}).get('turns_executed')}")
print(f"ARCHIVED_TOOLS_COUNT:  {last_arch.get('data', {}).get('tool_calls_count')}")
