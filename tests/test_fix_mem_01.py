"""RetailMind AI — Regression Tests for MEM-01 Fix.

Verifies:
1. `extract_verified_financial_facts` correctly extracts verified profit from `profit_metrics.net_profit`
   when `profit_metrics.available` is True.
2. `extract_verified_financial_facts` safely sets `Profit=UNAVAILABLE` when `profit_metrics.available` is False.
3. Preserves backward compatibility with legacy observations using flat `has_cost_data`.
4. End-to-end integration with Mock LLM and Real MCP on synthetic dataset with cost data.
5. End-to-end integration with Mock LLM and Real MCP on synthetic dataset without cost data.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from google.genai import types

from src.retailmind.agent.loop import RetailMindAgent, extract_verified_financial_facts
from src.retailmind.data.loader import DatasetManager
from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_unit_extract_verified_financial_facts_with_cost_data():
    """Verify profit is accurately extracted when profit_metrics.available is True."""
    obs = {
        "status": "success",
        "total_orders": 15,
        "net_units": 87.0,
        "net_revenue": 2945.0,
        "profit_metrics": {
            "available": True,
            "net_profit": 1525.5,
            "gross_margin_percentage": 51.8,
        },
    }
    tool_history = [{"tool": "summarize_sales", "status": "success", "observation": obs}]
    facts = extract_verified_financial_facts(tool_history)

    assert "Revenue=$2945.0" in facts
    assert "Orders=15" in facts
    assert "Units=87.0" in facts
    assert "Profit=$1525.5" in facts
    assert "Profit=UNAVAILABLE" not in facts


def test_unit_extract_verified_financial_facts_without_cost_data():
    """Verify Profit=UNAVAILABLE is recorded when profit_metrics.available is False."""
    obs = {
        "status": "success",
        "total_orders": 15,
        "net_units": 87.0,
        "net_revenue": 2945.0,
        "profit_metrics": {
            "available": False,
            "net_profit": "UNAVAILABLE",
            "gross_margin_percentage": "UNAVAILABLE",
            "reason": "unit_cost column is missing or incomplete in dataset",
        },
    }
    tool_history = [{"tool": "summarize_sales", "status": "success", "observation": obs}]
    facts = extract_verified_financial_facts(tool_history)

    assert "Revenue=$2945.0" in facts
    assert "Orders=15" in facts
    assert "Units=87.0" in facts
    assert "Profit=UNAVAILABLE" in facts
    assert "Profit=$None" not in facts
    assert "Profit=$UNAVAILABLE" not in facts


def test_unit_extract_verified_financial_facts_backward_compatibility():
    """Verify backward compatibility with legacy flat has_cost_data format."""
    legacy_with_cost = {
        "status": "success",
        "total_orders": 3,
        "net_units": 6.0,
        "net_revenue": 75.0,
        "has_cost_data": True,
        "net_profit": 35.0,
    }
    history_with_cost = [{"tool": "summarize_sales", "status": "success", "observation": legacy_with_cost}]
    facts_with_cost = extract_verified_financial_facts(history_with_cost)
    assert "Profit=$35.0" in facts_with_cost

    legacy_no_cost = {
        "status": "success",
        "total_orders": 3,
        "net_units": 6.0,
        "net_revenue": 75.0,
        "has_cost_data": False,
    }
    history_no_cost = [{"tool": "summarize_sales", "status": "success", "observation": legacy_no_cost}]
    facts_no_cost = extract_verified_financial_facts(history_no_cost)
    assert "Profit=UNAVAILABLE" in facts_no_cost


@pytest.mark.asyncio
async def test_integration_mem_01_persists_verified_profit_in_sqlite(tmp_path: Path):
    """End-to-end integration: dataset with cost stores real verified profit in SQLite memory."""
    sales_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    db_path = tmp_path / "mem01_test.db"
    mem_mgr = SQLiteMemoryManager(db_path=db_path)

    session_id = "mem01_with_cost_sess"
    user_id = "user_mem01"

    turn_counter = 0

    def mock_generate_content(model, contents, config):
        nonlocal turn_counter
        turn_counter += 1
        resp = MagicMock()
        resp.usage_metadata = {"prompt_token_count": 100, "candidates_token_count": 40}

        if turn_counter == 1:
            fc = MagicMock()
            fc.name = "summarize_sales"
            fc.args = {"session_id": session_id}
            resp.function_calls = [fc]
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text="Calling summarize_sales")])
            resp.candidates = [candidate]
            resp.text = None
            return resp
        else:
            resp.function_calls = None
            resp.text = "Verified financial summary: Net revenue is $2,945.00, profit is $1,525.50."
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text=resp.text)])
            resp.candidates = [candidate]
            return resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate_content

    agent = RetailMindAgent(
        api_key="mock_key",
        model_id="gemini-mock",
        execution_transport="mcp",
        memory_manager=mem_mgr,
    )
    agent._client = mock_client

    result = agent.run_task(
        user_query="What was our total revenue and profit?",
        session_id=session_id,
        user_id=user_id,
        csv_path=sales_csv,
    )

    assert result.stop_reason == "FINAL_ANSWER"

    # Verify directly in SQLite memory
    recalled = mem_mgr.retrieve_relevant_context(
        user_id=user_id,
        dataset_fingerprint=DatasetManager.get_dataset_fingerprint(session_id),
    )
    assert len(recalled) == 1
    stored_summary = recalled[0]["summary"]

    assert "Revenue=$2945.0" in stored_summary
    assert "Profit=$1525.5" in stored_summary
    assert "Profit=UNAVAILABLE" not in stored_summary


@pytest.mark.asyncio
async def test_integration_mem_01_persists_unavailable_when_cost_missing(tmp_path: Path):
    """End-to-end integration: dataset without cost stores Profit=UNAVAILABLE in SQLite memory."""
    no_cost_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales_no_cost.csv"
    db_path = tmp_path / "mem01_no_cost_test.db"
    mem_mgr = SQLiteMemoryManager(db_path=db_path)

    session_id = "mem01_no_cost_sess"
    user_id = "user_mem01_nc"

    turn_counter = 0

    def mock_generate_content(model, contents, config):
        nonlocal turn_counter
        turn_counter += 1
        resp = MagicMock()
        resp.usage_metadata = {"prompt_token_count": 100, "candidates_token_count": 40}

        if turn_counter == 1:
            fc = MagicMock()
            fc.name = "summarize_sales"
            fc.args = {"session_id": session_id}
            resp.function_calls = [fc]
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text="Calling summarize_sales")])
            resp.candidates = [candidate]
            resp.text = None
            return resp
        else:
            resp.function_calls = None
            resp.text = "Verified financial summary: Net revenue is $2,945.00, profit is unavailable."
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text=resp.text)])
            resp.candidates = [candidate]
            return resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate_content

    agent = RetailMindAgent(
        api_key="mock_key",
        model_id="gemini-mock",
        execution_transport="mcp",
        memory_manager=mem_mgr,
    )
    agent._client = mock_client

    result = agent.run_task(
        user_query="What was our total revenue and profit?",
        session_id=session_id,
        user_id=user_id,
        csv_path=no_cost_csv,
    )

    assert result.stop_reason == "FINAL_ANSWER"

    # Verify directly in SQLite memory
    recalled = mem_mgr.retrieve_relevant_context(
        user_id=user_id,
        dataset_fingerprint=DatasetManager.get_dataset_fingerprint(session_id),
    )
    assert len(recalled) == 1
    stored_summary = recalled[0]["summary"]

    assert "Revenue=$2945.0" in stored_summary
    assert "Profit=UNAVAILABLE" in stored_summary
    assert "Profit=$" not in stored_summary
