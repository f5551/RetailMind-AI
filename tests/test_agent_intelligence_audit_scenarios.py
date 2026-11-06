"""RetailMind AI — Agent Intelligence Audit 04: Ten Comprehensive Scenarios.

Tests the agent's tool orchestration and grounding across 10 bilingual scenarios:
1. Sales Summary (EN) -> summarize_sales
2. Profit Analysis (EN) -> summarize_sales
3. Product Ranking by Revenue (EN) -> rank_products
4. Period Comparison (EN) -> compare_periods
5. Missing Cost Data & Zero Hallucination (EN) -> summarize_sales
6. Sales & Orders Summary (AR) -> summarize_sales
7. Product Ranking by Units (AR) -> rank_products
8. Statistical Anomaly Detection (AR) -> detect_anomalies
9. Sales Segmentation by Category (AR) -> segment_sales
10. Ambiguous Forecasting Query (Disambiguation limitation without real LLM) -> NOT VERIFIED

Constraints:
- READ-ONLY on production code.
- Mock LLM used solely for routing orchestration without claiming proof of Gemini's neural comprehension.
- 0 paid API calls.
- Isolated temporary SQLite memory.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from google.genai import types

from src.retailmind.agent.loop import RetailMindAgent
from src.retailmind.data.loader import DatasetManager
from src.retailmind.memory.manager import SQLiteMemoryManager

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def test_env(tmp_path: Path):
    sales_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales.csv"
    no_cost_csv = WORKSPACE_ROOT / "sample_data" / "synthetic_sales_no_cost.csv"

    db_path = tmp_path / "scenario_memory.db"
    mem_mgr = SQLiteMemoryManager(db_path=db_path)

    return {
        "sales_csv": sales_csv,
        "no_cost_csv": no_cost_csv,
        "mem_mgr": mem_mgr,
        "tmp_path": tmp_path,
    }


def _run_single_tool_scenario(agent_query: str, tool_name: str, tool_args: dict, test_env, csv_path: Path, session_id: str, user_id: str, final_answer_formatter):
    """Executes a 2-turn agent task where Mock LLM calls the specified tool via Real MCP."""
    turn_counter = 0
    captured_obs = []

    def mock_generate_content(model, contents, config):
        nonlocal turn_counter
        turn_counter += 1
        resp = MagicMock()
        resp.usage_metadata = {"prompt_token_count": 120 * turn_counter, "candidates_token_count": 45}

        if turn_counter == 1:
            fc = MagicMock()
            fc.name = tool_name
            fc.args = tool_args
            resp.function_calls = [fc]
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text=f"Calling {tool_name}")])
            resp.candidates = [candidate]
            resp.text = None
            return resp
        else:
            resp.function_calls = None
            last_part = contents[-1].parts[0]
            obs = last_part.function_response.response
            captured_obs.append(obs)

            final_text = final_answer_formatter(obs)
            resp.text = final_text
            candidate = MagicMock()
            candidate.content = types.Content(role="model", parts=[types.Part.from_text(text=final_text)])
            resp.candidates = [candidate]
            return resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate_content

    agent = RetailMindAgent(
        api_key="mock_key",
        model_id="gemini-mock",
        execution_transport="mcp",
        memory_manager=test_env["mem_mgr"],
    )
    agent._client = mock_client

    result = agent.run_task(
        user_query=agent_query,
        session_id=session_id,
        user_id=user_id,
        csv_path=csv_path,
    )
    return result, captured_obs[0] if captured_obs else {}


@pytest.mark.asyncio
async def test_scenario_01_sales_summary_en(test_env):
    """Scenario 1 (EN): Total net revenue and total units sold."""
    session_id = "sess_sc_01"
    res, obs = _run_single_tool_scenario(
        agent_query="What was our total net revenue and total units sold?",
        tool_name="summarize_sales",
        tool_args={"session_id": session_id},
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_en_1",
        final_answer_formatter=lambda o: f"Total Net Revenue is ${o.get('net_revenue'):,.2f} across {o.get('net_units')} units sold.",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("status") == "success"
    assert obs.get("net_revenue") == 2945.0
    assert obs.get("net_units") == 87.0
    assert "$2,945.00" in res.final_answer


@pytest.mark.asyncio
async def test_scenario_02_profit_analysis_en(test_env):
    """Scenario 2 (EN): Net profit and gross margin percentage."""
    session_id = "sess_sc_02"
    res, obs = _run_single_tool_scenario(
        agent_query="Can you break down our net profit and gross margin percentage?",
        tool_name="summarize_sales",
        tool_args={"session_id": session_id},
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_en_2",
        final_answer_formatter=lambda o: f"Net Profit is ${o.get('profit_metrics', {}).get('net_profit'):,.2f} ({o.get('profit_metrics', {}).get('gross_margin_percentage')}% margin).",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("profit_metrics", {}).get("net_profit") == 1525.5
    assert obs.get("profit_metrics", {}).get("gross_margin_percentage") == 51.8
    assert "$1,525.50" in res.final_answer
    assert "51.8%" in res.final_answer


@pytest.mark.asyncio
async def test_scenario_03_product_ranking_en(test_env):
    """Scenario 3 (EN): Top 3 products by revenue."""
    session_id = "sess_sc_03"
    res, obs = _run_single_tool_scenario(
        agent_query="Which are our top 3 best-selling products by total revenue?",
        tool_name="rank_products",
        tool_args={"session_id": session_id, "metric": "revenue", "top_n": 3},
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_en_3",
        final_answer_formatter=lambda o: f"Top product is {o.get('rankings')[0]['product']} with ${o.get('rankings')[0]['net_revenue']:,.2f}.",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert len(obs.get("rankings", [])) == 3
    assert obs.get("rankings")[0]["product"] == "USB-C Hub"
    assert obs.get("rankings")[0]["net_revenue"] == 640.0
    assert "USB-C Hub" in res.final_answer


@pytest.mark.asyncio
async def test_scenario_04_period_comparison_en(test_env):
    """Scenario 4 (EN): January vs February 2026 performance comparison."""
    session_id = "sess_sc_04"
    res, obs = _run_single_tool_scenario(
        agent_query="Compare our sales performance between January 2026 and February 2026.",
        tool_name="compare_periods",
        tool_args={
            "session_id": session_id,
            "period_a": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "period_b": {"start_date": "2026-02-01", "end_date": "2026-02-28"},
        },
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_en_4",
        final_answer_formatter=lambda o: f"Revenue grew by ${o.get('variance', {}).get('revenue_delta'):,.2f} (+{o.get('variance', {}).get('revenue_growth_percentage')}%).",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("variance", {}).get("revenue_delta") == 235.0
    assert obs.get("variance", {}).get("revenue_growth_percentage") == 17.34
    assert "$235.00" in res.final_answer


@pytest.mark.asyncio
async def test_scenario_05_missing_cost_data_en(test_env):
    """Scenario 5 (EN): Missing cost column -> profit unavailable (Zero Hallucination)."""
    session_id = "sess_sc_05"
    res, obs = _run_single_tool_scenario(
        agent_query="What was our net profit for these transactions?",
        tool_name="summarize_sales",
        tool_args={"session_id": session_id},
        test_env=test_env,
        csv_path=test_env["no_cost_csv"],
        session_id=session_id,
        user_id="user_en_5",
        final_answer_formatter=lambda o: (
            "Profit and margin are UNAVAILABLE because unit cost information is missing."
            if not o.get("profit_metrics", {}).get("available")
            else f"Net Profit is ${o.get('profit_metrics', {}).get('net_profit')}"
        ),
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("profit_metrics", {}).get("available") is False
    assert obs.get("profit_metrics", {}).get("net_profit") == "UNAVAILABLE"
    assert "UNAVAILABLE" in res.final_answer
    assert "missing" in res.final_answer.lower()


@pytest.mark.asyncio
async def test_scenario_06_sales_summary_ar(test_env):
    """Scenario 6 (AR): ملخص المبيعات وصافي الإيرادات باللغة العربية."""
    session_id = "sess_sc_06"
    res, obs = _run_single_tool_scenario(
        agent_query="كم بلغ إجمالي صافي الإيرادات وعدد الطلبات في البيانات المحملة؟",
        tool_name="summarize_sales",
        tool_args={"session_id": session_id},
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_ar_1",
        final_answer_formatter=lambda o: f"صافي الإيرادات الإجمالي بلغ ${o.get('net_revenue'):,.2f} عبر {o.get('total_orders')} طلباً.",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("net_revenue") == 2945.0
    assert obs.get("total_orders") == 15
    assert "$2,945.00" in res.final_answer
    assert "15" in res.final_answer


@pytest.mark.asyncio
async def test_scenario_07_product_ranking_by_units_ar(test_env):
    """Scenario 7 (AR): تصنيف المنتجات الأكثر مبيعاً حسب عدد الوحدات."""
    session_id = "sess_sc_07"
    res, obs = _run_single_tool_scenario(
        agent_query="ما هي المنتجات الأكثر مبيعاً من حيث عدد الوحدات المباعة؟",
        tool_name="rank_products",
        tool_args={"session_id": session_id, "metric": "units", "top_n": 3},
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_ar_2",
        final_answer_formatter=lambda o: f"المنتج الأكثر مبيعاً هو {o.get('rankings')[0]['product']} بإجمالي {o.get('rankings')[0]['units']} وحدة.",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("rankings")[0]["product"] == "USB-C Hub"
    assert obs.get("rankings")[0]["units"] == 32.0
    assert "USB-C Hub" in res.final_answer
    assert "32" in res.final_answer


@pytest.mark.asyncio
async def test_scenario_08_detect_anomalies_ar(test_env):
    """Scenario 8 (AR): كشف المعاملات الشاذة إحصائياً في الإيرادات."""
    session_id = "sess_sc_08"
    res, obs = _run_single_tool_scenario(
        agent_query="هل توجد أي معاملات مبيعات شاذة أو غير اعتيادية في الإيرادات؟",
        tool_name="detect_anomalies",
        tool_args={"session_id": session_id, "column": "revenue", "method": "zscore", "threshold": 2.0},
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_ar_3",
        final_answer_formatter=lambda o: f"تم فحص الشذوذ بطريقة {o.get('method_used')} ورصد {o.get('anomalies_count')} معاملة شاذة.",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("status") == "success"
    assert obs.get("method_used") == "zscore"
    assert "zscore" in res.final_answer


@pytest.mark.asyncio
async def test_scenario_09_segment_sales_by_category_ar(test_env):
    """Scenario 9 (AR): تجزئة المبيعات والإيرادات حسب فئة المنتجات."""
    session_id = "sess_sc_09"
    res, obs = _run_single_tool_scenario(
        agent_query="حلل لي توزيع المبيعات وصافي الإيرادات حسب فئات المنتجات المختلفة.",
        tool_name="segment_sales",
        tool_args={"session_id": session_id, "dimension": "category"},
        test_env=test_env,
        csv_path=test_env["sales_csv"],
        session_id=session_id,
        user_id="user_ar_4",
        final_answer_formatter=lambda o: f"تم توزيع المبيعات عبر فئتين بمجموع إيرادات ${sum(s.get('net_revenue', 0.0) for s in o.get('segments', [])):,.2f}.",
    )
    assert res.stop_reason == "FINAL_ANSWER"
    assert obs.get("status") == "success"
    assert obs.get("dimension") == "category"
    total_rev = sum(s.get("net_revenue", 0.0) for s in obs.get("segments", []))
    assert round(total_rev, 2) == 2945.00
    assert "$2,945.00" in res.final_answer


def test_scenario_10_ambiguous_intent_without_real_model(test_env):
    """Scenario 10: Ambiguous unconstrained query ('حلل لي الوضع العام وتوقع المستقبل').
    
    Demonstrates architectural boundary:
    Determining whether Gemini correctly disambiguates vague user phrasing into 
    specific analytical tools CANNOT be proven using a pre-scripted Mock LLM.
    Per task constraint 4: Must be classified as NOT VERIFIED.
    """
    ambiguous_query = "حلل لي الوضع بشكل عام وتوقع لي المستقبل؟"
    # Documented constraint: Mock LLM can only execute scripted routing.
    # True neural disambiguation requires a real model inference session.
    assert len(ambiguous_query) > 0
    # Explicitly classified as NOT VERIFIED per instructions
