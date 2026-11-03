"""Tests for Phase 1 Specifications and Technical Contracts.

Verifies that:
1. agent_spec.md exists, conforms to 1-page constraints, and contains all required clauses.
2. docs/CSV_DATA_CONTRACT.md defines schema, missing/return policies, and formula safety.
3. docs/TOOL_CONTRACTS.md covers all 8 tools with input/output schemas and permissions.
4. docs/PHASE_01_TEST_PLAN.md covers 5 loop inputs, MCP, SQLite restart, 3 injections, traces.
5. docs/ARCHITECTURE_DESIGN.md covers single agent, Gemini SDK, MCP, SQLite, isolation, UI.
"""

from pathlib import Path
import re
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_agent_spec_exists_and_fits_one_page():
    spec_path = WORKSPACE_ROOT / "agent_spec.md"
    assert spec_path.exists(), "agent_spec.md must exist at workspace root"
    content = spec_path.read_text(encoding="utf-8")

    # One printable page constraint: ~50-120 lines and reasonable character length
    lines = content.strip().splitlines()
    assert 40 <= len(lines) <= 120, f"Expected 40-120 lines for 1-page spec, got {len(lines)}"
    assert len(content) < 6000, f"Expected < 6000 characters for 1-page spec, got {len(content)}"


def test_agent_spec_contains_mandatory_clauses():
    content = (WORKSPACE_ROOT / "agent_spec.md").read_text(encoding="utf-8")

    # 1. Goal (single sentence under ## 1. Goal)
    goal_section = re.search(r"## 1\. Goal\s*\n+([^\n]+)", content)
    assert goal_section is not None, "Goal section missing"
    goal_sentence = goal_section.group(1).strip()
    assert goal_sentence.count(".") == 1, "Goal must be exactly one sentence"
    assert "RetailMind AI" in goal_sentence

    # 2. Exactly 8 tools
    expected_tools = [
        "inspect_dataset",
        "validate_dataset",
        "summarize_sales",
        "rank_products",
        "compare_periods",
        "detect_anomalies",
        "segment_sales",
        "generate_report",
    ]
    for tool in expected_tools:
        assert tool in content, f"Missing tool in agent_spec.md: {tool}"

    # 3. All 3 termination conditions
    assert "max_turns = 8" in content or "max_turns=8" in content
    assert "$0.10" in content
    assert "final_answer" in content

    # 4. Permission policy
    assert "ask_on_write" in content

    # 5. Three concrete examples
    assert "Example 1:" in content
    assert "Example 2:" in content
    assert "Example 3:" in content


def test_csv_data_contract_completeness():
    csv_contract = (WORKSPACE_ROOT / "docs" / "CSV_DATA_CONTRACT.md").read_text(encoding="utf-8")

    # Required columns
    for col in ["date", "product", "quantity", "unit_price"]:
        assert col in csv_contract, f"Missing required column in CSV contract: {col}"

    # Optional columns
    for col in ["unit_cost", "category", "region", "order_id"]:
        assert col in csv_contract, f"Missing optional column in CSV contract: {col}"

    # Invariants and safety
    assert "formula" in csv_contract.lower()
    assert "quarantin" in csv_contract.lower()
    assert "profit" in csv_contract.lower()
    assert "UNAVAILABLE" in csv_contract
    assert "50,000" in csv_contract


def test_tool_contracts_completeness():
    tools_doc = (WORKSPACE_ROOT / "docs" / "TOOL_CONTRACTS.md").read_text(encoding="utf-8")

    expected_tools = [
        "inspect_dataset",
        "validate_dataset",
        "summarize_sales",
        "rank_products",
        "compare_periods",
        "detect_anomalies",
        "segment_sales",
        "generate_report",
    ]
    for tool in expected_tools:
        assert f"##" in tools_doc and tool in tools_doc, f"Tool contract missing: {tool}"

    # generate_report must be write_approval_required
    assert "write_approval_required" in tools_doc
    assert "PERMISSION_DENIED_PENDING_APPROVAL" in tools_doc


def test_phase_01_test_plan_completeness():
    test_plan = (WORKSPACE_ROOT / "docs" / "PHASE_01_TEST_PLAN.md").read_text(encoding="utf-8")

    # 5 loop inputs
    for test_id in ["AL-01", "AL-02", "AL-03", "AL-04", "AL-05"]:
        assert test_id in test_plan, f"Missing test case {test_id} in test plan"

    # MCP and memory tests
    assert "MCP-01" in test_plan
    assert "MEM-01" in test_plan

    # 3 prompt injection attacks
    assert "PI-01" in test_plan
    assert "PI-02" in test_plan
    assert "PI-03" in test_plan

    # 3 required traces
    assert "traces/success_1.jsonl" in test_plan
    assert "traces/near_failure_recovery.jsonl" in test_plan
    assert "traces/explicit_failure.jsonl" in test_plan


def test_architecture_design_completeness():
    arch_doc = (WORKSPACE_ROOT / "docs" / "ARCHITECTURE_DESIGN.md").read_text(encoding="utf-8")

    assert "single-agent" in arch_doc.lower()
    assert "google-genai" in arch_doc
    assert "mcp" in arch_doc.lower()
    assert "data/retailmind.db" in arch_doc
    assert "session_id" in arch_doc
    assert "audit_log" in arch_doc
    assert "streamlit" in arch_doc.lower()
    assert "railway" in arch_doc.lower() or "render" in arch_doc.lower()
