# Capstone Traceability and Evidence Matrix

Update this matrix ONLY using evidence observed in the running project. Every status starts as NOT VERIFIED. Do not mark a requirement PASS based on code presence alone.

| ID | Requirement | Current status | Evidence location / command / URL |
|---|---|---|---|
| P1 | One-page agent_spec.md | **PASS** | `agent_spec.md` (47 lines, fits 1 printable page; verified via `pytest tests/test_spec_contracts.py::test_agent_spec_exists_and_fits_one_page`) |
| P2 | Goal, 5–10 tools, 3 stop conditions, budget, permissions, 3 I/O examples | **PASS** | `agent_spec.md` (1-sentence goal, exactly 8 tools, max_turns=8 + $0.10 cap + final_answer, ask_on_write, 3 synthetic I/O examples; verified via `pytest tests/test_spec_contracts.py::test_agent_spec_contains_mandatory_clauses`) |
| A1 | Genuine single-agent Gemini tool-calling loop | NOT VERIFIED | |
| A2 | 5 inputs tested with JSONL traces | NOT VERIFIED | |
| M1 | Real MCP server + client and model tool routing | NOT VERIFIED | |
| M2 | SQLite memory persists after process restart | NOT VERIFIED | |
| S1 | Executable permissions with denial test | NOT VERIFIED | |
| S2 | Audit log with event evidence | NOT VERIFIED | |
| S3 | Cost tracker based on measured usage + model-specific rates | NOT VERIFIED | |
| S4 | 3 hostile prompt-injection tests | NOT VERIFIED | |
| D1 | Streamlit UI verified locally | NOT VERIFIED | |
| D2 | Public GitHub repository URL | NOT VERIFIED | |
| D3 | Public app URL + documented persistent DB | NOT VERIFIED | |
| D4 | README with setup and deployment | NOT VERIFIED | |
| T1 | Genuine traces/success_1.jsonl | NOT VERIFIED | |
| T2 | Genuine traces/near_failure_recovery.jsonl | NOT VERIFIED | |
| T3 | Genuine traces/explicit_failure.jsonl | NOT VERIFIED | |
| C1 | cost_analysis.md with real average $/task and monthly assumptions | NOT VERIFIED | |
| F1 | All five final submission items linked and verified | NOT VERIFIED | |
| F2 | Gaps disclosed in final submission email | NOT VERIFIED | |
