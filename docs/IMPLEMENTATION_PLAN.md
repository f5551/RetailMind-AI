# Phase-by-Phase Execution — RetailMind AI

**Gate rule:** A phase is only COMPLETE when its tests have been executed and evidence recorded. The Antigravity engineering agent MUST STOP before the next phase and request approval. Time estimates are adapted from the assignment, not a promise of delivery time.

| Phase | Scope | Mandatory acceptance gate | Evidence |
|---|---|---|---|
| 0 — Project control | Create project folders, install always-on rules, read assignment contract, decide exact dependencies, create repo hygiene + status | `AGENTS.md` and requirement docs exist; no unrelated application features created | `docs/STATUS.md`, documented workspace structure |
| 1 — Planning (3h) | `agent_spec.md`, dataset contract, architecture, eight MCP tool schemas, model/pricing strategy | ONE page, one-sentence goal, 8 tools, max_turns + dollar cap + final_answer, ask_on_write, 3 specific I/O cases | `agent_spec.md` and manual spec checklist |
| 2 — Agent loop (6h) | Gemini tool calling; single-agent iterative loop; tool dispatcher, CSV validation, first tools; traces | 5 genuine input cases; JSONL traces; actual stop reason; no fake tool outputs or extra agents | `tests/`, `traces/`, real terminal results |
| 3 — MCP + memory (5h) | Custom Python MCP server, client integration, SQLite episodic memory | MCP handshake and calls actually pass; restart process and verify persisted memory | MCP integration test and restart test output |
| 4 — Safety + cost (5h) | Approval enforcement, audit log, injection defense, metering and USD computations | 3 hostile-input tests; approval denial test; audited events; real API usage vs budget explained; genuine success/recovery/failure traces | `tests/`, `traces/`, audit sample, measured costs |
| 5 — UI + deployment (4h) | Streamlit dashboard, reports, cost/trace views, local Docker/Railway or Render setup | App runs locally; public repo + live URL verified by user; persistence deployment verified; README and `cost_analysis.md` | working URL, screenshots or recording, deployment logs |
| 6 — Final assessment | Map every contract clause to evidence; package submission links | No unverified claim, three exact trace paths, five final submission elements; disclose gaps | `docs/EVIDENCE_MATRIX.md`, final README links, final submission text |

## Phase 0 precise scope
- No fake demo, no placeholder traces presented as genuine, no premature full app generation.
- Existing files in this starter pack are the source of truth; do not delete or rewrite requirements.
- Initialize a Git repo if absent; create `.gitignore`, `.env.example`, `pyproject.toml` or `requirements.txt` after confirming actual SDKs, empty source/test directories as appropriate, and a minimal `README.md` explaining how to begin.
- Confirm project tree and dependency install commands, but do not require a paid API key for Phase 0.
- Record `PHASE_0_COMPLETE` only after running the required local checks.

## Phase 1 decisions to document
- Model identifier is configurable via `GEMINI_MODEL` and version/prices are recorded with source and date, not invented.
- Default `max_turns=8`, `budget_per_task_usd=0.10`, permission mode `ask_on_write`, with clear semantics for total turns and cost estimates. These are project design defaults and can be adjusted if measured results require it.
- Dataset: required date/product/quantity/unit_price; optional unit_cost/category/region/order_id. Define returns and invalid rows handling in one paragraph.
- Tools exactly: inspect_dataset, validate_dataset, summarize_sales, rank_products, compare_periods, detect_anomalies, segment_sales, generate_report. Each tool has constrained arguments and a typed response. Generate_report is approval-gated.
- Three successful, **illustrative** input/output examples in `agent_spec.md` should use a small documented synthetic dataset and explicitly label them as designed examples, not actual test results.
