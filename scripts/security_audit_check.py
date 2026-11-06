import glob
import json
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("--- 1. SCANNING ALL JSONL TRACES FOR SECRETS ---")
patterns = {
    "google_api_key": re.compile(r"AIzaSy[A-Za-z0-9_\-]{33}"),
    "generic_api_key": re.compile(r"""(?i)(?:api[_-]?key|secret|password|access_token)\s*[:=]\s*["']([^"']{8,})["']"""),
    "jwt_bearer": re.compile(r"""bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_=]*""", re.IGNORECASE),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36}"),
}

trace_matches = []
all_trace_files = glob.glob("traces/**/*.jsonl", recursive=True)
print(f"Total JSONL trace files found: {len(all_trace_files)}")

for p in all_trace_files:
    with open(p, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            for pat_name, pat in patterns.items():
                m = pat.search(line)
                if m:
                    # check if it's not a redacted placeholder
                    val = m.group(0)
                    if "[REDACTED" not in val and "your_gemini" not in val:
                        trace_matches.append((p, idx, pat_name, val[:12] + "..."))

print(f"Trace secret matches: {len(trace_matches)}")
for m in trace_matches:
    print(f"  [ALERT] {m[0]}:{m[1]} ({m[2]}): {m[3]}")

print("\n--- 2. SCANNING GIT TRACKED FILES FOR SENSITIVE FILES ---")
tracked_files = subprocess.check_output(["git", "ls-files"]).decode("utf-8").splitlines()
sensitive_exts = (".db", ".sqlite", ".sqlite3", ".key", ".pem", ".p12", ".pfx", ".log", ".env")
sensitive_tracked = []
for tf in tracked_files:
    lower_tf = tf.lower()
    if lower_tf.endswith(sensitive_exts) or lower_tf == ".env" or lower_tf.startswith(".env."):
        if tf != ".env.example":
            sensitive_tracked.append(tf)

print(f"Sensitive tracked files: {len(sensitive_tracked)}")
for st in sensitive_tracked:
    print(f"  [ALERT] Tracked: {st}")

print("\n--- 3. SCANNING FULL GIT COMMIT HISTORY FOR SENSITIVE BLOCKS ---")
# Check every commit in history for tracked sensitive paths
history_paths = subprocess.check_output(["git", "log", "--name-only", "--pretty=format:", "--all"]).decode("utf-8").splitlines()
sensitive_history = set()
for hp in history_paths:
    hp_clean = hp.strip()
    if not hp_clean:
        continue
    lower_hp = hp_clean.lower()
    if lower_hp.endswith(sensitive_exts) or lower_hp == ".env" or lower_hp.startswith(".env."):
        if hp_clean != ".env.example":
            sensitive_history.add(hp_clean)

print(f"Sensitive paths ever committed in history: {len(sensitive_history)}")
for sh in sensitive_history:
    print(f"  [ALERT] In history: {sh}")

print("\n--- 4. DATASET CHECK (sample_data vs uploads) ---")
sample_data_files = glob.glob("sample_data/**/*", recursive=True)
print(f"Files in sample_data: {sample_data_files}")
tracked_csvs = [tf for tf in tracked_files if tf.lower().endswith(".csv")]
print(f"Tracked CSV files ({len(tracked_csvs)}): {tracked_csvs}")

print("\n--- 5. DOCKERFILE AND RAILWAY CONFIG CHECK ---")
for conf in ["Dockerfile", "railway.json", "Procfile"]:
    if os.path.exists(conf):
        with open(conf, "r", encoding="utf-8") as f:
            content = f.read()
            has_secret = bool(patterns["google_api_key"].search(content))
            print(f"{conf}: exists, secrets found: {has_secret}")
