# RetailMind AI — Antigravity Phase-Control Kit

This ZIP is NOT a completed capstone. It contains persistent engineering instructions, the original capstone contract, the execution plan, an evidence matrix, and copy-paste prompts for Phases 0 and 1.

## Install
1. Create/open a new EMPTY project folder named `RetailMind-AI` in **Google Antigravity**.
2. Extract the ZIP contents DIRECTLY into that project root. The file `AGENTS.md` must sit at the very top level (not buried in a nested directory).
3. Open Antigravity's agent panel. Workspace rules in `AGENTS.md` are automatically discovered; see official rules documentation: https://antigravity.google/docs/rules/ . You can also inspect Workspace Rules via Customizations > Rules.
4. Open `prompts/PHASE_00_START.md`, copy its contents into the agent chat, and run Phase 0 ONLY.
5. When Phase 0 tests are complete, inspect changes in `docs/STATUS.md` and `docs/EVIDENCE_MATRIX.md`. After you approve, execute `prompts/PHASE_01_PLANNING.md`.

## Critical distinction
- Antigravity is your **coding/build assistant**.
- Gemini API + a SINGLE agent loop + an actual MCP client/server is the **delivered capstone product**. Using Antigravity to write code does not itself satisfy the capstone requirements.
- The original deadline supplied in the assignment (2026-11-01 23:59 Yemen time) has passed as of 2026-11-03. Verify whether late work can be accepted.

## Files
- `AGENTS.md` — always-on constraints for the coding agent
- `docs/CAPSTONE_REQUIREMENTS.md` — assignment contract
- `docs/IMPLEMENTATION_PLAN.md` — phases and gates
- `docs/EVIDENCE_MATRIX.md` — requirement-to-test mapping
- `docs/STATUS.md` — real-time verified status
- `prompts/PHASE_00_START.md` — begin with this
- `prompts/PHASE_01_PLANNING.md` — only after Phase 0 approval
