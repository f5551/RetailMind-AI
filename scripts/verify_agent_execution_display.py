import os
import sys
import shutil
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(r"c:\Users\HP\Desktop\RetailMind A")
SCREENSHOTS_DIR = WORKSPACE_ROOT / "docs" / "audit_ui" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACTS_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\1c7d81ed-4bea-496f-bf76-9bdfffeebb00")

DEV_SECRET = "retailmind-dev-secret-local-2026"
BASE_URL = "http://127.0.0.1:8501"

def run_verification():
    print("=" * 60)
    print("Starting Playwright Verification for Agent Execution Display")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # -------------------------------------------------------------
        # Scenario 1: Standard End-User View (Arabic, Unauthorized)
        # -------------------------------------------------------------
        print("\n[Scenario 1] Testing Standard End-User View (Arabic, Unauthorized)...")
        context1 = browser.new_context(viewport={"width": 1360, "height": 950})
        page1 = context1.new_page()
        page1.goto(f"{BASE_URL}/?view=agent&mock_agent_view=1&revoke_dev=1")
        page1.wait_for_timeout(4000)

        # Check for user steps header
        steps_header = page1.get_by_text("خطوات التحليل والتأكيد")
        assert steps_header.count() > 0, "Expected 'خطوات التحليل والتأكيد' header to be present for end-user"
        print("✓ Confirmed: Friendly business steps expander is present.")

        # Check friendly step titles
        step_titles = [
            "فحص بنية وجودة البيانات",
            "تحليل وتلخيص المبيعات الإجمالية",
            "تجزئة المبيعات حسب الفئات",
            "ترتيب وتصنيف أداء المنتجات",
            "إعداد التقرير المالي التنفيذي",
        ]
        for st in step_titles:
            loc = page1.get_by_text(st)
            assert loc.count() > 0, f"Expected friendly step '{st}' to be present"
            print(f"  ✓ Found friendly step: {st}")

        # Check friendly status badges
        completed_badges = page1.get_by_text("✓ مكتمل")
        assert completed_badges.count() >= 4, f"Expected at least 4 '✓ مكتمل' badges, found {completed_badges.count()}"
        print(f"✓ Confirmed: {completed_badges.count()} '✓ مكتمل' badges present.")

        pending_badge = page1.get_by_text("⏳ بانتظار الموافقة")
        assert pending_badge.count() >= 1, "Expected '⏳ بانتظار الموافقة' badge to be present"
        print("✓ Confirmed: '⏳ بانتظار الموافقة' badge present.")

        # Strict checks: Technical details must NOT be visible to end users
        page_content = page1.content()
        assert "عملية فرعية عبر stdio" not in page_content, "Leaked 'stdio' into end-user page!"
        assert "FINAL_ANSWER" not in page_content, "Leaked 'FINAL_ANSWER' into end-user page!"
        assert "17461" not in page_content, "Leaked token count '17461' into end-user page!"
        assert "0.005723" not in page_content, "Leaked API cost '$0.005723' into end-user page!"
        assert "الجولة 1: أداة inspect_dataset عبر mcp" not in page_content, "Leaked raw tool invocation into end-user page!"
        assert "التشخيص التقني المتقدم" not in page_content, "Leaked developer diagnostics expander into end-user page!"
        print("✓ STRICT CHECK PASSED: Zero technical internals (stdio, tokens, API cost, raw code names) exposed to end user.")

        # Save screenshot
        user_shot_path = SCREENSHOTS_DIR / "agent_display_fixed_user.png"
        page1.screenshot(path=str(user_shot_path), full_page=False)
        print(f"✓ Saved user screenshot: {user_shot_path}")

        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(user_shot_path), str(ARTIFACTS_DIR / "agent_display_fixed_user.png"))
            print("✓ Copied user screenshot to artifacts directory.")
        context1.close()

        # -------------------------------------------------------------
        # Scenario 2: Authorized Developer View (Arabic, Authorized)
        # -------------------------------------------------------------
        print("\n[Scenario 2] Testing Authorized Developer View (Arabic, Authorized)...")
        context2 = browser.new_context(viewport={"width": 1360, "height": 1100})
        page2 = context2.new_page()
        page2.goto(f"{BASE_URL}/?view=agent&mock_agent_view=1")
        page2.wait_for_timeout(3500)

        # Authenticate via sidebar developer drawer using UI password input
        diag_exp = page2.locator("[data-testid='stSidebar'] details summary:has-text('التشخيص المتقدم')").first
        if diag_exp.count() > 0:
            diag_exp.click()
            page2.wait_for_timeout(600)
        pw_field = page2.locator("input[type='password']:visible").first
        pw_field.fill(DEV_SECRET)
        page2.locator("button:has-text('فك قفل مساحة المطور'):visible").first.click()
        page2.wait_for_timeout(3500)

        # Developer expander should now be present!
        dev_expander = page2.get_by_text("التشخيص التقني المتقدم")
        assert dev_expander.count() > 0, "Expected 'التشخيص التقني المتقدم' expander for authorized developer"
        print("✓ Confirmed: Developer diagnostics expander is present for authorized dev.")

        # Click to expand it
        dev_expander.first.click()
        page2.wait_for_timeout(1500)

        # Verify that developer diagnostics details appear inside
        dev_content = page2.content()
        assert "وسيط التنفيذ" in dev_content, "Expected transport info in developer section"
        assert "سبب انتهاء المهمة" in dev_content, "Expected stop reason in developer section"
        assert "17461" in dev_content, "Expected token metrics in developer section"
        assert "0.005723" in dev_content, "Expected cost metrics in developer section"
        assert "سجل استدعاء الأدوات الفعلي" in dev_content, "Expected tool audit log in developer section"
        print("✓ Confirmed: All technical details properly accessible to authorized developer.")

        dev_shot_path = SCREENSHOTS_DIR / "agent_display_fixed_dev.png"
        page2.screenshot(path=str(dev_shot_path), full_page=False)
        print(f"✓ Saved developer screenshot: {dev_shot_path}")

        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(dev_shot_path), str(ARTIFACTS_DIR / "agent_display_fixed_dev.png"))
            print("✓ Copied developer screenshot to artifacts directory.")
        context2.close()

        # -------------------------------------------------------------
        # Scenario 3: Standard End-User View in English
        # -------------------------------------------------------------
        print("\n[Scenario 3] Testing Standard End-User View (English, Unauthorized)...")
        context3 = browser.new_context(viewport={"width": 1360, "height": 950})
        page3 = context3.new_page()
        page3.goto(f"{BASE_URL}/?view=agent&mock_agent_view=1&revoke_dev=1&lang=en")
        page3.wait_for_timeout(4000)

        en_steps_header = page3.get_by_text("Analysis & Verification Steps")
        assert en_steps_header.count() > 0, "Expected 'Analysis & Verification Steps' header in English"
        print("✓ Confirmed: English business steps header is present.")

        en_step_titles = [
            "Dataset Structure Inspection",
            "Sales & Revenue Summary",
            "Sales Segmentation by Category",
            "Product Performance Ranking",
            "Executive Financial Report Drafting",
        ]
        for est in en_step_titles:
            loc = page3.get_by_text(est)
            assert loc.count() > 0, f"Expected English step '{est}' to be present"
            print(f"  ✓ Found English step: {est}")

        en_completed_badge = page3.get_by_text("✓ Completed")
        assert en_completed_badge.count() >= 4, "Expected '✓ Completed' badges in English"
        print("✓ Confirmed: English status badges present.")

        en_shot_path = SCREENSHOTS_DIR / "agent_display_fixed_en.png"
        page3.screenshot(path=str(en_shot_path), full_page=False)
        print(f"✓ Saved English screenshot: {en_shot_path}")

        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(en_shot_path), str(ARTIFACTS_DIR / "agent_display_fixed_en.png"))
            print("✓ Copied English screenshot to artifacts directory.")
        context3.close()

        browser.close()

    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO DEFECTS!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
