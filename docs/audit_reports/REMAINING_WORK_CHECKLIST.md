# RetailMind AI — Remaining Work & Pre-Submission Action Checklist

> **Audit Baseline Date:** 2026-11-03  
> **Overall Assessment:** READY WITH MINOR ISSUES  
> **Target:** Final Submission for LLM4Yemen Track B Week 5  

This checklist categorizes all remaining actions required before final delivery into clear, actionable priority tiers.

---

## 🔴 Priority 1: User-Actionable Submission Blockers (External Actions)

These items require the user's explicit account credentials and authorization. They cannot be executed automatically by the agent.

- [ ] **A1. Create & Push to Public GitHub Repository**
  - **Prerequisites:** Git repository is clean and local commits are up-to-date.
  - **Action:**
    ```bash
    git remote add origin https://github.com/<YOUR-USERNAME>/retailmind-ai.git
    git branch -M master
    git push -u origin master
    ```
  - **Verification:** Ensure `.env`, `data/*.db`, and private uploads are not published (verified covered by `.gitignore`).
  - **Submission Artifact:** Required URL for Submission Item A.

- [ ] **A2. Deploy Application to Cloud Platform (Railway or Render)**
  - **Target:** Railway (recommended via Nixpacks + `railway.json` / `Procfile`) or Render.
  - **Configuration:**
    - Attach persistent volume at `/app/data` (mapped via `RETAILMIND_DATA_DIR=/app/data`).
    - Set environment variables: `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.1-flash-lite`, `MAX_TURNS=8`, `BUDGET_PER_TASK_USD=0.10`, `PERMISSION_POLICY=ask_on_write`.
  - **Healthcheck Verification:** `https://<YOUR-APP>.up.railway.app/_stcore/health` returns `ok`.
  - **Fallback (if hosting sleeps/fails):** Record a genuine screen recording demonstrating local app walkthrough, Gemini+MCP tool calling, write approval gate, and persistent memory inspection.

- [ ] **A3. Format and Send Final Submission Email**
  - **To:** `llm4yemen@gmail.com`
  - **Subject:** `<YOUR FULL NAME> - مسار ب - الاسبوع 5`
  - **Body Format:** Direct links in email body (no attachments). Include:
    1. Public GitHub repository URL
    2. Live public demo URL (or screen recording link)
    3. Links to `traces/success_1.jsonl`, `traces/near_failure_recovery.jsonl`, `traces/explicit_failure.jsonl`
    4. Link to `agent_spec.md`
    5. Link to `cost_analysis.md`
    6. Transparent disclosure of project limits (synthetic demo policy, process restart memory, Docker CLI status).

---

## 🟡 Priority 2: Documentation Cosmetic Refinements

Cosmetic documentation updates to eliminate minor inconsistencies identified during audit:

- [x] **B1. Update `README.md` test counter badge:** Updated from 74 tests to 98 tests passing (100%).
- [x] **B2. Update `README.md` directory tree:** Reflect full directory hierarchy including `agent/`, `audit/`, `memory/`, `ui/`, `snapshots/`.
- [x] **B3. Update `docs/STATUS.md`:** Added comprehensive Audit phase entry and status determination.
- [x] **B4. Update `docs/EVIDENCE_MATRIX.md`:** Verified status for all Day 1–5 requirements, remediation findings, and audit gates.
- [x] **B5. Align `docs/ARCHITECTURE_DESIGN.md` rates note:** Mention official pricing ($0.25/$1.50) override.

---

## 🟢 Priority 3: Optional Long-Term / Enterprise Enhancements (Post-Capstone)

Items that exceed the Track B capstone requirements but improve production maturity:

- [ ] **C1. Multi-Tenant Enterprise Authentication:** Integrate OAuth2/OIDC/SSO (e.g. Auth0, Clerk, or Supabase Auth) to replace session-based tenant IDs with cryptographically verified identity tokens.
- [ ] **C2. Centralized Audit Logging (WORM/SIEM):** Stream SQLite audit logs to external append-only log sinks (AWS CloudWatch, Datadog, or S3 Object Lock).
- [ ] **C3. Automated Container CI/CD Pipeline:** Configure GitHub Actions workflow running tests and container linting on pull requests.
- [ ] **C4. Model Context Caching Optimization:** Enable explicit prompt caching on large dataset schemas to leverage Gemini's $0.025/1M cached token tier during multi-turn chats.
