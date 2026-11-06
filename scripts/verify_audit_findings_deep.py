import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(r"c:\Users\HP\Desktop\RetailMind A")
app_py = (WORKSPACE_ROOT / "app.py").read_text(encoding="utf-8")
i18n_py = (WORKSPACE_ROOT / "src" / "retailmind" / "ui" / "i18n.py").read_text(encoding="utf-8")

def check_finding(fid, pattern, description):
    matches = [(i+1, line.strip()) for i, line in enumerate(app_py.splitlines()) if re.search(pattern, line, re.IGNORECASE)]
    print(f"[{fid}] {description}")
    if matches:
        print(f"  ✓ Confirmed in app.py: {len(matches)} match(es)")
        for lno, text in matches[:3]:
            print(f"    L{lno}: {text[:90]}")
    else:
        print(f"  ✗ Pattern not found in app.py: {pattern}")
    print()

print("--- DEEP CODE VERIFICATION OF AUDIT FINDINGS ---\n")

check_finding("NAV-01", "status_model|status_mcp|status_policy", "Sidebar top badges (Gemini, MCP, ask_on_write)")
check_finding("NAV-02", "fingerprint_label|dataset_fingerprint", "Sidebar session data expander & SHA-256")
check_finding("NAV-03", "guardrails_header|gemini_model|max_turns", "Sidebar security guardrails expander")
check_finding("NAV-04", "btn_load_sample|btn_onboarding_load_sample", "Duplicate sample loaders")
check_finding("NAV-05", "nav_labels.*view_keys", "5-tab navigation structure")
check_finding("DASH-01", "header-date-pill.*▼", "Misleading dropdown arrow on date pill")
check_finding("DASH-02", "calc_period_deltas|مقارنة بالفترة السابقة", "Baseline growth deltas")
check_finding("DASH-03", r"\$|format_curr", "Hardcoded $ currency symbol")
check_finding("DASH-04", "alt\.Chart.*category", "Category performance chart")
check_finding("AGT-01", "ref_context_sources|ask_on_write", "AI Agent right panel technical jargon")
check_finding("AGT-02", "ref_step_mcp|التحقق عبر MCP", "Stepper MCP phrasing")
check_finding("AGT-03", "pill_cols.*chat_input.*or suggested_prompt", "Instant trigger of suggestion pills")
check_finding("AGT-04", "total_tokens.*total_cost_usd", "Execution metadata footer (tokens, cost)")
check_finding("DATA-01", "ref_user_greeting|مرحباً أحمد|27 أكتوبر 2025", "Hardcoded greeting & date")
check_finding("DATA-02", "RETAILMIND_LOCAL_DEV_SECRET|dev_mode_secret_input", "Local dev secret input box")
check_finding("DATA-03", "تقرير الأرباح الشهري - أكتوبر 2025|ref_pending_review", "Idle approval card pre-filled report")
check_finding("DATA-04", "أحمد الشراري|ref_audit_event_upload", "Dummy rows in audit table")
check_finding("MEM-01", "memory_title.*SQLite", "Memory Explorer technical title")
check_finding("MEM-02", "lbl_active_user|lbl_dataset_fingerprint", "Raw user UUID & SHA-256 hash in memory")
check_finding("MEM-03", "st\.json.*tool_calls", "Raw JSON tool calls in memory expander")
check_finding("AUD-01", "lbl_db_location|audit\.db", "OS filesystem path exposed in audit view")
check_finding("AUD-02", "col_timestamp.*col_tool.*col_action.*col_reason", "Raw developer column headers in audit")
check_finding("EMPTY-01", "no_dataset_loaded|warn_agent_no_dataset", "Empty states across views")
