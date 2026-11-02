# LLM4Yemen — Track B — Week 5: Original Capstone Contract

**Domain selected:** CSV / database data analysis. **Product:** RetailMind AI. **Build assistant:** Google Antigravity. **Deployed agent model provider:** Gemini, not the Antigravity coding assistant itself.

## Day 1 — Planning (3 hours)
One-page `agent_spec.md` must include:
- Agent goal in ONE sentence.
- Five to ten allowed tools.
- Termination: `max_turns` AND `budget` AND `final_answer`.
- Explicit per-task US-dollar budget cap.
- Permission mode from `auto`, `ask_on_write`, `always_ask`.
- Three successful input/output examples.

## Day 2 — Agent Loop (6 hours)
- Implement a real agent loop with tool calling.
- Test with five distinct inputs.
- Save JSONL execution traces.
- Start with ONE agent; NO multi-agent on this phase (project stays single-agent for clarity).

## Day 3 — MCP and Memory (5 hours)
- Connect at least one genuine MCP server: filesystem, GitHub, or a custom server.
- Implement a SQLite memory layer.
- Verify that memory survives a full restart.

## Day 4 — Safety and Cost (5 hours)
- Executable permission layer.
- Audit log.
- Model cost tracking.
- Three adversarial prompt-injection tests with documented failures/successful defenses.

## Day 5 — Deployment (4 hours)
- Simple Streamlit UI.
- Public deployment on Railway or Render.
- README.
- Document average per-task cost.

## EXACT final submission artifacts
1. **Public GitHub repo URL**.
2. **Live public demo URL**. When a free-tier service sleeps/stops, an authentic screen-recording demonstration may be submitted as evidence (not a fabricated link).
3. Three real logs at these exact relative paths:
   - `traces/success_1.jsonl`
   - `traces/near_failure_recovery.jsonl`
   - `traces/explicit_failure.jsonl`
4. `agent_spec.md`.
5. `cost_analysis.md` — provider-specific actual token pricing, average cost/task, project/monthly cost assumptions.

## Submission email rule
Send to `llm4yemen@gmail.com`, subject exactly: `<FULL NAME> - مسار ب - الاسبوع 5`. Put links in **body**, not as attachment. Clearly disclose anything incomplete. The published deadline in the supplied notice was Sunday 2026-11-01 at 23:59 Yemen time (already past as of 2026-11-03); confirm if late submissions are accepted before assuming eligibility.

## Important course-specific limitations
- Claude Code chapter is NOT required and is unavailable from Yemen for this assignment; do not depend on it.
- OpenAI or Gemini is acceptable; this project chooses Gemini. Do not copy Anthropic token prices.
- The explicit failure trace is positive evidence of honest testing. It must document an authentic failure.
- Do not make deployment conditional on paid products without disclosing cost/alternatives.
