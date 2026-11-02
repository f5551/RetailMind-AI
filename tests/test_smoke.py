"""Phase 0 Smoke Verification Test.

Validates that:
1. Python environment is >= 3.11.
2. Core dependencies (google-genai, mcp, pandas, pydantic, sqlite3) can be imported.
3. SQLite in-memory functionality works as expected for persistent memory layers.
4. Essential project files exist and repository hygiene is maintained.
"""

import importlib
import sys
from pathlib import Path
import sqlite3
import pytest


def test_python_version():
    """Verify that Python version meets minimum project requirement (>= 3.11)."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"


@pytest.mark.parametrize(
    "module_name",
    [
        "sqlite3",
        "pydantic",
        "mcp",
        "pandas",
        "google.genai",
        "streamlit",
    ],
)
def test_core_dependencies_importable(module_name: str):
    """Verify each critical dependency can be imported cleanly without error."""
    mod = importlib.import_module(module_name)
    assert mod is not None, f"Failed to import {module_name}"


def test_sqlite_in_memory_basic_operations():
    """Verify standard library SQLite functions correctly for memory and audit."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE smoke_check (id INTEGER PRIMARY KEY, note TEXT);")
    cursor.execute("INSERT INTO smoke_check (note) VALUES ('phase_0_verified');")
    conn.commit()
    cursor.execute("SELECT note FROM smoke_check WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "phase_0_verified"


def test_essential_project_governance_files_exist():
    """Verify root governance and configuration files are present."""
    workspace_root = Path(__file__).resolve().parent.parent
    expected_files = [
        "AGENTS.md",
        ".gitignore",
        ".env.example",
        "requirements.txt",
        "pyproject.toml",
        "docs/CAPSTONE_REQUIREMENTS.md",
        "docs/IMPLEMENTATION_PLAN.md",
        "docs/EVIDENCE_MATRIX.md",
        "docs/STATUS.md",
    ]
    for rel_path in expected_files:
        p = workspace_root / rel_path
        assert p.exists(), f"Missing required file: {rel_path}"
