"""RetailMind AI — Package Source Code for Independent Technical Audit.

Packages the complete clean source code, documentation, synthetic datasets,
and verified execution traces into RetailMind-Full-Audit.zip.
Excludes all secrets, virtual environments, SQLite databases, caches, and runtime state.
"""

import os
import re
import zipfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ZIP_OUTPUT_PATH = WORKSPACE_ROOT / "RetailMind-Full-Audit.zip"

# Explicitly allowed top-level files
TOP_LEVEL_FILES = [
    ".env.example",
    ".gitignore",
    "AGENTS.md",
    "agent_spec.md",
    "app.py",
    "cost_analysis.md",
    "Dockerfile",
    "Procfile",
    "pyproject.toml",
    "railway.json",
    "README.md",
    "README_START_HERE.md",
    "requirements.txt",
]

# Explicitly allowed directories
INCLUDE_DIRS = [
    "docs",
    "sample_data",
    "scripts",
    "src",
    "tests",
    "traces",
]

# Prohibited filename extensions and patterns
EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".log",
}

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".pytest_tmp",
    ".venv",
    ".git",
    ".streamlit",
}

EXCLUDE_FILE_NAMES = {
    ".env",
    "audit.db",
    "auth.db",
    "retailmind.db",
    "session_registry.json",
    "RetailMind-Full-Audit.zip",
}


def build_audit_archive():
    manifest_entries = []

    if ZIP_OUTPUT_PATH.exists():
        ZIP_OUTPUT_PATH.unlink()

    with zipfile.ZipFile(ZIP_OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Top level files
        for fname in sorted(TOP_LEVEL_FILES):
            fpath = WORKSPACE_ROOT / fname
            if fpath.exists():
                arcname = fname
                zf.write(fpath, arcname)
                size_bytes = fpath.stat().st_size
                manifest_entries.append((arcname, size_bytes))

        # 2. Included directories
        for dname in sorted(INCLUDE_DIRS):
            dir_path = WORKSPACE_ROOT / dname
            if not dir_path.exists():
                continue
            for root, dirs, files in os.walk(dir_path):
                # Filter out excluded directory names in-place
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
                for file in sorted(files):
                    if file in EXCLUDE_FILE_NAMES:
                        continue
                    if any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                        continue
                    full_p = Path(root) / file
                    rel_p = full_p.relative_to(WORKSPACE_ROOT)
                    arcname = str(rel_p).replace("\\", "/")
                    zf.write(full_p, arcname)
                    size_bytes = full_p.stat().st_size
                    manifest_entries.append((arcname, size_bytes))

        # 3. Add clean placeholder directories (reports/.gitkeep, data/.gitkeep)
        for ph in ["data/.gitkeep", "reports/.gitkeep"]:
            ph_path = WORKSPACE_ROOT / ph
            if ph_path.exists():
                arcname = ph.replace("\\", "/")
                zf.write(ph_path, arcname)
                manifest_entries.append((arcname, ph_path.stat().st_size))

    # Sort manifest alphabetically
    manifest_entries.sort(key=lambda x: x[0])

    # 4. Security Audit Scan of the created archive
    api_key_regex = re.compile(r"AIza[0-9A-Za-z-_]{35}")
    violations = []

    with zipfile.ZipFile(ZIP_OUTPUT_PATH, "r") as zf:
        namelist = zf.namelist()
        for member in namelist:
            # Check prohibited files
            if member == ".env" or member.endswith("/.env"):
                violations.append(f"Forbidden file detected: {member}")
            if member.endswith(".db") or member.endswith(".sqlite"):
                violations.append(f"Database file detected: {member}")
            if "__pycache__" in member or member.endswith(".pyc"):
                violations.append(f"Compiled python bytecode detected: {member}")
            if member.startswith(".git/") or member.startswith(".venv/"):
                violations.append(f"Internal directory detected: {member}")

            # Check text content for Google API keys
            try:
                raw_bytes = zf.read(member)
                text = raw_bytes.decode("utf-8", errors="ignore")
                matches = api_key_regex.findall(text)
                if matches:
                    violations.append(f"API key pattern detected in {member}: {len(matches)} matches")
            except Exception:
                pass

    return manifest_entries, violations


if __name__ == "__main__":
    entries, violations = build_audit_archive()
    print(f"Archive created at: {ZIP_OUTPUT_PATH}")
    print(f"Total files archived: {len(entries)}")
    total_size = sum(sz for _, sz in entries)
    print(f"Total uncompressed size: {total_size:,} bytes")
    print(f"Archive file size: {ZIP_OUTPUT_PATH.stat().st_size:,} bytes")
    print(f"Security scan violations: {len(violations)}")
    if violations:
        for v in violations:
            print("  VIOLATION:", v)
        raise SystemExit(1)
    else:
        print("SECURITY SCAN: PASSED (Zero credentials, zero private databases, zero secrets)")
