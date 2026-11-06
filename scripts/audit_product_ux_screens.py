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

def capture_product_review_screens():
    print("=" * 65)
    print("Capturing High-Res Screenshots for Product & UX Review")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # ---------------------------------------------------------
        # 1. Overview Dashboard (Arabic)
        # ---------------------------------------------------------
        print("\n1. Capturing Overview Dashboard (Arabic)...")
        ctx = browser.new_context(viewport={"width": 1440, "height": 950})
        page = ctx.new_page()
        page.goto(f"{BASE_URL}/?view=overview&load_sample=1&revoke_dev=1")
        page.wait_for_timeout(4000)
        shot1 = SCREENSHOTS_DIR / "product_rev_1_dashboard.png"
        page.screenshot(path=str(shot1), full_page=False)
        print(f"  ✓ Saved: {shot1}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot1), str(ARTIFACTS_DIR / "product_rev_1_dashboard.png"))

        # ---------------------------------------------------------
        # 2. AI Sales Agent (Arabic)
        # ---------------------------------------------------------
        print("\n2. Capturing AI Sales Agent (Arabic)...")
        page.goto(f"{BASE_URL}/?view=agent&mock_agent_view=1&revoke_dev=1")
        page.wait_for_timeout(4000)
        shot2 = SCREENSHOTS_DIR / "product_rev_2_agent.png"
        page.screenshot(path=str(shot2), full_page=False)
        print(f"  ✓ Saved: {shot2}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot2), str(ARTIFACTS_DIR / "product_rev_2_agent.png"))

        # ---------------------------------------------------------
        # 3. Dataset Ingestion (Arabic)
        # ---------------------------------------------------------
        print("\n3. Capturing Dataset Ingestion (Arabic)...")
        page.goto(f"{BASE_URL}/?view=dataset&revoke_dev=1")
        page.wait_for_timeout(4000)
        shot3 = SCREENSHOTS_DIR / "product_rev_3_dataset.png"
        page.screenshot(path=str(shot3), full_page=False)
        print(f"  ✓ Saved: {shot3}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot3), str(ARTIFACTS_DIR / "product_rev_3_dataset.png"))

        # ---------------------------------------------------------
        # 4. Memory Explorer (Saved Insights) (Arabic)
        # ---------------------------------------------------------
        print("\n4. Capturing Memory Explorer (Saved Insights) (Arabic)...")
        page.goto(f"{BASE_URL}/?view=memory&revoke_dev=1")
        page.wait_for_timeout(4000)
        shot4 = SCREENSHOTS_DIR / "product_rev_4_memory.png"
        page.screenshot(path=str(shot4), full_page=False)
        print(f"  ✓ Saved: {shot4}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot4), str(ARTIFACTS_DIR / "product_rev_4_memory.png"))

        # ---------------------------------------------------------
        # 5. Security Audit Trail - Unauthorized (403 Forbidden)
        # ---------------------------------------------------------
        print("\n5. Capturing Audit Trail - Unauthorized (403 Screen)...")
        page.goto(f"{BASE_URL}/?view=audit&revoke_dev=1")
        page.wait_for_timeout(4000)
        shot5 = SCREENSHOTS_DIR / "product_rev_5_audit_forbidden.png"
        page.screenshot(path=str(shot5), full_page=False)
        print(f"  ✓ Saved: {shot5}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot5), str(ARTIFACTS_DIR / "product_rev_5_audit_forbidden.png"))

        # ---------------------------------------------------------
        # 6. Security Audit Trail - Authorized Developer Unlocked
        # ---------------------------------------------------------
        print("\n6. Capturing Audit Trail - Authorized Developer Unlocked...")
        # Authenticate via the on-page password box
        pw_field = page.locator("input[type='password']:visible").first
        if pw_field.count() > 0:
            pw_field.fill(DEV_SECRET)
            page.locator("button:has-text('فك قفل مساحة المطور'):visible").first.click()
            page.wait_for_timeout(4000)
        shot6 = SCREENSHOTS_DIR / "product_rev_6_audit_unlocked.png"
        page.screenshot(path=str(shot6), full_page=False)
        print(f"  ✓ Saved: {shot6}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot6), str(ARTIFACTS_DIR / "product_rev_6_audit_unlocked.png"))

        # ---------------------------------------------------------
        # 7. Overview Dashboard (English)
        # ---------------------------------------------------------
        print("\n7. Capturing Overview Dashboard (English)...")
        page.goto(f"{BASE_URL}/?view=overview&lang=en")
        page.wait_for_timeout(4000)
        shot7 = SCREENSHOTS_DIR / "product_rev_7_dashboard_english.png"
        page.screenshot(path=str(shot7), full_page=False)
        print(f"  ✓ Saved: {shot7}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot7), str(ARTIFACTS_DIR / "product_rev_7_dashboard_english.png"))

        # ---------------------------------------------------------
        # 8. AI Sales Agent (English)
        # ---------------------------------------------------------
        print("\n8. Capturing AI Sales Agent (English)...")
        page.goto(f"{BASE_URL}/?view=agent&lang=en&mock_agent_view=1")
        page.wait_for_timeout(4000)
        shot8 = SCREENSHOTS_DIR / "product_rev_8_agent_english.png"
        page.screenshot(path=str(shot8), full_page=False)
        print(f"  ✓ Saved: {shot8}")
        if ARTIFACTS_DIR.exists():
            shutil.copy2(str(shot8), str(ARTIFACTS_DIR / "product_rev_8_agent_english.png"))

        ctx.close()
        browser.close()

    print("\n" + "=" * 65)
    print("All Product Review Screenshots Captured Successfully!")
    print("=" * 65)

if __name__ == "__main__":
    capture_product_review_screens()
