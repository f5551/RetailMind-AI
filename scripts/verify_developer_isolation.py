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

def run_developer_isolation_tests():
    print("=" * 65)
    print("Starting Playwright Verification: Secure Developer View Isolation")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # -------------------------------------------------------------
        # Test 1: Merchant View - Navigation Shows ONLY Business Pages
        # -------------------------------------------------------------
        print("\n[Test 1] Testing Merchant View Navigation (Unauthorized)...")
        ctx1 = browser.new_context(viewport={"width": 1360, "height": 900})
        page1 = ctx1.new_page()
        page1.goto(f"{BASE_URL}/?view=overview&revoke_dev=1")
        page1.wait_for_timeout(4000)

        sidebar = page1.locator('[data-testid="stSidebar"]')
        sidebar.wait_for(state="visible", timeout=10000)
        sidebar_text = sidebar.inner_text()
        print("DEBUG SIDEBAR TEXT:", repr(sidebar_text))
        
        assert "الرئيسية" in sidebar_text, "Missing 'الرئيسية' in merchant navigation"
        assert "المحلل الذكي" in sidebar_text, "Missing 'المحلل الذكي' in merchant navigation"
        assert "البيانات والحوكمة" in sidebar_text, "Missing 'البيانات والحوكمة' in merchant navigation"
        assert "الرؤى المحفوظة" in sidebar_text, "Missing 'الرؤى المحفوظة' in merchant navigation"
        
        # STRICT ISOLATION ASSERTION: 'سجل التدقيق' must NOT be in the sidebar!
        assert "سجل التدقيق" not in sidebar_text, "CRITICAL LEAK: 'سجل التدقيق' is visible to merchant!"
        print("  ✓ Confirmed: Merchant sidebar contains ONLY business pages.")
        print("  ✓ Confirmed: 'سجل التدقيق' is completely hidden from unauthorized merchant.")

        shot1 = SCREENSHOTS_DIR / "iso_1_merchant_sidebar.png"
        page1.screenshot(path=str(shot1), full_page=False)
        print(f"  ✓ Saved screenshot: {shot1}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot1), str(ARTIFACTS_DIR / "iso_1_merchant_sidebar.png"))
        ctx1.close()

        # -------------------------------------------------------------
        # Test 2: Server-Side Route Guard - Direct URL to ?view=audit Blocked
        # -------------------------------------------------------------
        print("\n[Test 2] Testing Server-Side Route Guard (?view=audit Direct Access)...")
        ctx2 = browser.new_context(viewport={"width": 1360, "height": 900})
        page2 = ctx2.new_page()
        page2.goto(f"{BASE_URL}/?view=audit&revoke_dev=1")
        page2.wait_for_timeout(4000)

        # Check 403 Forbidden Screen
        body_text = page2.locator("body").inner_text()
        assert "403 وصول محظور" in body_text, "Expected '403 وصول محظور' forbidden header"
        assert "لا تملك صلاحية استعراض هذه الصفحة مباشرة" in body_text, "Expected forbidden explanation"
        
        # Check that NO audit events table is rendered!
        assert "col_timestamp" not in body_text, "LEAK: Audit timestamp column visible on 403 page!"
        assert "col_transport" not in body_text, "LEAK: Transport column visible on 403 page!"
        assert "data/retailmind.db" not in body_text, "LEAK: Database path leaked on 403 page!"
        print("  ✓ Confirmed: Direct navigation to ?view=audit is blocked by server (403 Forbidden).")
        print("  ✓ Confirmed: Zero audit logs or sensitive database details leaked.")

        shot2 = SCREENSHOTS_DIR / "iso_2_direct_url_forbidden.png"
        page2.screenshot(path=str(shot2), full_page=False)
        print(f"  ✓ Saved screenshot: {shot2}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot2), str(ARTIFACTS_DIR / "iso_2_direct_url_forbidden.png"))
        ctx2.close()

        # -------------------------------------------------------------
        # Test 3: Rejecting URL Token Injection (Requirement 3)
        # -------------------------------------------------------------
        print("\n[Test 3] Testing Rejection of dev_token via URL Query Parameter...")
        ctx3 = browser.new_context(viewport={"width": 1360, "height": 900})
        page3 = ctx3.new_page()
        # Attempt to pass secret via URL
        page3.goto(f"{BASE_URL}/?view=audit&dev_token={DEV_SECRET}")
        page3.wait_for_timeout(4000)

        body_text3 = page3.locator("body").inner_text()
        # Must still be blocked! URL tokens are never trusted!
        assert "403 وصول محظور" in body_text3, "CRITICAL VULNERABILITY: URL token was accepted directly!"
        print("  ✓ Confirmed: URL token injection strictly rejected; page remains 403 Forbidden.")

        shot3 = SCREENSHOTS_DIR / "iso_3_url_token_rejected.png"
        page3.screenshot(path=str(shot3), full_page=False)
        print(f"  ✓ Saved screenshot: {shot3}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot3), str(ARTIFACTS_DIR / "iso_3_url_token_rejected.png"))
        ctx3.close()

        # -------------------------------------------------------------
        # Test 4: Secure Developer Authentication via UI Form
        # -------------------------------------------------------------
        print("\n[Test 4] Testing UI Password Authentication & Audit Trail Unlock...")
        ctx4 = browser.new_context(viewport={"width": 1360, "height": 950})
        page4 = ctx4.new_page()
        page4.goto(f"{BASE_URL}/?view=audit&revoke_dev=1")
        page4.wait_for_timeout(4000)

        # Enter secret in the visible password input on the 403 page
        pw_input = page4.locator("div[data-testid='stMainBlockContainer'] input[type='password']").first
        pw_input.wait_for(state="visible", timeout=10000)
        pw_input.fill(DEV_SECRET)
        page4.wait_for_timeout(500)

        # Click Unlock button on the main 403 page
        unlock_btn = page4.locator("div[data-testid='stMainBlockContainer'] button:has-text('فك قفل مساحة المطور')").first
        unlock_btn.click()
        page4.wait_for_timeout(4000)

        # Now audit page should be unlocked!
        unlocked_text = page4.locator("body").inner_text()
        assert "سجل التدقيق" in unlocked_text, "Failed to unlock Audit Trail after valid credentials"
        
        # Check that sidebar now displays developer section
        sidebar_unlocked = page4.locator('[data-testid="stSidebar"]').inner_text()
        assert "سجل التدقيق والأمان" in sidebar_unlocked, "Audit option not added to sidebar after dev unlock"
        assert "مساحة المطور والإدارة" in sidebar_unlocked, "Developer console badge not in sidebar"
        print("  ✓ Confirmed: Valid secret unlocks Developer Console and Audit Trail.")
        print("  ✓ Confirmed: Sidebar dynamically updates to include Developer Console.")

        shot4 = SCREENSHOTS_DIR / "iso_4_developer_unlocked_audit.png"
        page4.screenshot(path=str(shot4), full_page=False)
        print(f"  ✓ Saved screenshot: {shot4}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot4), str(ARTIFACTS_DIR / "iso_4_developer_unlocked_audit.png"))

        # -------------------------------------------------------------
        # Test 5: Bilingual Support & Navigation while Authorized
        # -------------------------------------------------------------
        print("\n[Test 5] Testing Bilingual English View in Developer Console...")
        en_toggle = page4.locator("button:has-text('English')").first
        if en_toggle.count() > 0:
            en_toggle.click()
            page4.wait_for_timeout(3500)

        en_body = page4.locator("body").inner_text()
        assert "Security & Audit Trail" in en_body, "English 'Security & Audit Trail' missing"
        assert "Developer Console" in en_body, "English 'Developer Console' missing"
        print("  ✓ Confirmed: English developer console and audit trail verified in same session.")

        shot5 = SCREENSHOTS_DIR / "iso_5_developer_english.png"
        page4.screenshot(path=str(shot5), full_page=False)
        print(f"  ✓ Saved screenshot: {shot5}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot5), str(ARTIFACTS_DIR / "iso_5_developer_english.png"))

        # -------------------------------------------------------------
        # Test 6: Revoking Authorization / Locking Developer Console
        # -------------------------------------------------------------
        print("\n[Test 6] Testing Developer Session Revocation & Lock...")
        diag_expander = page4.locator("[data-testid='stSidebar'] details summary:has-text('Advanced Diagnostics')").first
        if diag_expander.count() == 0:
            diag_expander = page4.locator("[data-testid='stSidebar'] details summary:has-text('التشخيص المتقدم')").first
        if diag_expander.count() > 0:
            diag_expander.click()
            page4.wait_for_timeout(1000)

        lock_btn = page4.locator("button:has-text('Lock / Exit Developer Mode'):visible")
        if lock_btn.count() == 0:
            lock_btn = page4.locator("button:has-text('قفل / إنهاء وضع المطور'):visible")
        
        assert lock_btn.count() > 0, "Could not find Lock / Exit Developer Mode button"
        lock_btn.first.click()
        page4.wait_for_timeout(4000)

        # Confirm we are returned to overview and audit is gone from sidebar
        revoked_sidebar = page4.locator('[data-testid="stSidebar"]').inner_text()
        assert "Security & Audit Trail" not in revoked_sidebar and "سجل التدقيق" not in revoked_sidebar, "Audit link still in sidebar after revoke!"
        assert "Developer Console" not in revoked_sidebar, "Developer console still in sidebar after revoke!"
        print("  ✓ Confirmed: Revoking authorization locks developer console and removes audit link from sidebar.")

        shot6 = SCREENSHOTS_DIR / "iso_6_revoked_merchant_restored.png"
        page4.screenshot(path=str(shot6), full_page=False)
        print(f"  ✓ Saved screenshot: {shot6}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot6), str(ARTIFACTS_DIR / "iso_6_revoked_merchant_restored.png"))

        ctx4.close()
        browser.close()

    print("\n" + "=" * 65)
    print("ALL LEVEL 2 ISOLATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    run_developer_isolation_tests()
