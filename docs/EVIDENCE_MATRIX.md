# Capstone Traceability and Evidence Matrix

Update this matrix ONLY using evidence observed in the running project. Every status starts as NOT VERIFIED. Do not mark a requirement PASS based on code presence alone.

| ID | Requirement | Current status | Evidence location / command / URL |
|---|---|---|---|
| P1 | One-page agent_spec.md | **PASS** | `agent_spec.md` (47 lines, fits 1 printable page; verified via `pytest tests/test_spec_contracts.py::test_agent_spec_exists_and_fits_one_page`) |
| P2 | Goal, 5–10 tools, 3 stop conditions, budget, permissions, 3 I/O examples | **PASS** | `agent_spec.md` (1-sentence goal, exactly 8 tools, max_turns=8 + $0.10 cap + final_answer, ask_on_write, 3 synthetic I/O examples; verified via `pytest tests/test_spec_contracts.py::test_agent_spec_contains_mandatory_clauses`) |
| A1 | Genuine single-agent Gemini tool-calling loop | **PASS** | `src/retailmind/agent/loop.py` using `google-genai` SDK and model `gemini-3.1-flash-lite`. Verified multi-turn function calling, deterministic observation feedback, and `FINAL_ANSWER` termination. Proven in `traces/scenario_1_summary.jsonl` and `tests/test_agent_loop.py`. |
| A2 | 5 inputs tested with JSONL traces | **PASS** | 5 distinct sales analytics inputs tested against `sample_data/synthetic_sales.csv` with 100% ground-truth mathematical match and genuine multi-turn JSONL traces: `traces/scenario_1_summary.jsonl`, `traces/scenario_2_rankings.jsonl`, `traces/scenario_3_comparison.jsonl`, `traces/scenario_4_anomalies.jsonl`, `traces/scenario_5_validation.jsonl` (and scenario 6 in `traces/scenario_6_report_approval.jsonl`). |
| M1 | Real MCP server + client and model tool routing | NOT VERIFIED | |
| M2 | SQLite memory persists after process restart | NOT VERIFIED | |
| S1 | Executable permissions with denial test | **PASS** | `src/retailmind/agent/permissions.py` and `tests/test_agent_loop.py` (`test_permission_manager_ask_on_write`, `test_permission_self_grant_prevention`, and `tests/test_tools.py::test_tool_generate_report_denial`). Write operations are blocked at code level without external authorization. |
| S2 | Audit log with event evidence | NOT VERIFIED | |
| S3 | Cost tracker based on measured usage + model-specific rates | **PASS** | `src/retailmind/agent/cost_meter.py` tracking prompt, output, thinking, and cached tokens using official Gemini API Standard rates ($0.25/1M in, $1.50/1M out). Pre/post-flight checks against $0.10 cap verified in `test_cost_tracker_calculation_and_budget_cap` and `test_cost_tracker_thinking_and_cached_tokens`. |
| S4 | 3 hostile prompt-injection tests | NOT VERIFIED | |
| D1 | Streamlit UI verified locally | NOT VERIFIED | |
| D2 | Public GitHub repository URL | NOT VERIFIED | |
| D3 | Public app URL + documented persistent DB | NOT VERIFIED | |
| D4 | README with setup and deployment | NOT VERIFIED | |
| T1 | Genuine traces/success_1.jsonl | **PASS** | `traces/success_1.jsonl` (3,188 tokens, $0.000932 USD paid-tier equivalent, $0.00 Free Tier actual billed, 2 turns, tool call: `summarize_sales`, stop reason: `FINAL_ANSWER`). |
| T2 | Genuine traces/near_failure_recovery.jsonl | NOT VERIFIED | |
| T3 | Genuine traces/explicit_failure.jsonl | NOT VERIFIED | |
| C1 | cost_analysis.md with real average $/task and monthly assumptions | **PASS** | `cost_analysis.md` (official Gemini API standard pricing verified 2026-11-03, exact average of $0.001096/task for N=5, $0.001067/task for N=6, highest task $0.004150, budget limit $0.10, monthly volume projections, verified Free Tier $0.00 vs paid-tier equivalent). |
| F1 | All five final submission items linked and verified | NOT VERIFIED | |
| F2 | Gaps disclosed in final submission email | NOT VERIFIED | |
