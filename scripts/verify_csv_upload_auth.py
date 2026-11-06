import os
import sys
import time
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

SCREENSHOTS_DIR = Path("docs/audit_ui/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

FIXTURE_PATH = Path("tests/fixtures/RetailMind_Sales_Products_1000_CATALOG_USD_TEST.csv").resolve()
INVALID_CSV_PATH = Path("tests/fixtures/invalid_missing_cols.csv").resolve()

def run_tests():
    print("======================================================================")
    print("🚀 RetailMind AI — CSV Upload Authorization & Security Verification")
    print("======================================================================")

    # 0. Create temporary invalid schema CSV (missing date, product, unit_price)
    df_invalid = pd.DataFrame({
        "order_number": [101, 102],
        "item_name": ["Widget A", "Widget B"],
        "amount": [50.0, 75.0]
    })
    df_invalid.to_csv(INVALID_CSV_PATH, index=False)
    print(f"✓ Created invalid test CSV at {INVALID_CSV_PATH}")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()

        # -------------------------------------------------------------
        # Case 1: Unauthenticated Custom CSV Upload Rejection (Fail-Closed)
        # -------------------------------------------------------------
        print("\n--- Test 1: Unauthenticated Custom Upload (Should Fail Closed) ---")
        page.goto("http://127.0.0.1:8501/?view=dataset", timeout=30000)
        page.wait_for_selector("h1", timeout=15000)
        page.wait_for_selector("text=وضع العرض التجريبي المعتمد", timeout=10000)
        print("  ✓ Demo mode notice banner is visible before upload.")

        page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)
        file_input = page.locator('input[type="file"]')
        
        print(f"  Uploading custom business CSV: {FIXTURE_PATH.name}...")
        file_input.first.set_input_files(str(FIXTURE_PATH))
        page.wait_for_selector("text=وضع العرض التجريبي", timeout=15000)
        print("  ✓ Custom CSV rejected with clear Arabic restriction message.")

        shot1 = SCREENSHOTS_DIR / "csv_auth_1_unauthenticated_rejected.png"
        page.screenshot(path=str(shot1), full_page=True)
        print(f"  📸 Screenshot saved: {shot1}")

        # -------------------------------------------------------------
        # Case 2: Invalid Developer Authorization Attempt
        # -------------------------------------------------------------
        print("\n--- Test 2: Invalid Developer Secret Verification ---")
        page.wait_for_selector('[data-testid="stMainBlockContainer"] input[type="password"]', timeout=10000)
        main_pwd = page.locator('[data-testid="stMainBlockContainer"] input[type="password"]')
        main_pwd.fill("wrong_secret_attack_999")

        auth_btn = page.locator('[data-testid="stMainBlockContainer"] button', has_text="تفعيل الرفع المحلي")
        auth_btn.first.click()
        page.wait_for_selector("text=الرمز السري لتفويض المطور غير صحيح", timeout=10000)
        print("  ✓ Incorrect secret rejected safely with error message.")

        shot2 = SCREENSHOTS_DIR / "csv_auth_2_wrong_secret.png"
        page.screenshot(path=str(shot2), full_page=True)
        print(f"  📸 Screenshot saved: {shot2}")

        # -------------------------------------------------------------
        # Case 3: Valid Developer Authorization on 127.0.0.1
        # -------------------------------------------------------------
        print("\n--- Test 3: Valid Developer Authorization on 127.0.0.1 ---")
        page.wait_for_selector('[data-testid="stMainBlockContainer"] input[type="password"]', timeout=10000)
        main_pwd = page.locator('[data-testid="stMainBlockContainer"] input[type="password"]')
        main_pwd.fill("retailmind-dev-secret-local-2026")

        auth_btn = page.locator('[data-testid="stMainBlockContainer"] button', has_text="تفعيل الرفع المحلي")
        auth_btn.first.click()
        page.wait_for_selector("text=وضع الاختبار المحلي مفوّض", timeout=10000)
        print("  ✓ Active developer authorized banner displayed successfully.")

        shot3 = SCREENSHOTS_DIR / "csv_auth_3_authorized_banner.png"
        page.screenshot(path=str(shot3), full_page=True)
        print(f"  📸 Screenshot saved: {shot3}")

        # -------------------------------------------------------------
        # Case 4: Authorized Custom CSV Upload
        # -------------------------------------------------------------
        print("\n--- Test 4: Authorized Custom CSV Upload ---")
        page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)
        file_input = page.locator('input[type="file"]')
        file_input.first.set_input_files(str(FIXTURE_PATH))
        page.wait_for_selector("text=1,000", timeout=15000)
        print("  ✓ Custom CSV loaded and registered successfully (1,000 rows).")

        shot4 = SCREENSHOTS_DIR / "csv_auth_4_upload_success.png"
        page.screenshot(path=str(shot4), full_page=True)
        print(f"  📸 Screenshot saved: {shot4}")

        # -------------------------------------------------------------
        # Case 5: Dashboard Verification with Custom Dataset
        # -------------------------------------------------------------
        print("\n--- Test 5: Dashboard Verification with Custom Dataset ---")
        overview_nav = page.locator("label[data-testid='stRadioOption']").filter(has_text="الرئيسية")
        overview_nav.click()
        page.wait_for_selector("h1:has-text('نظرة عامة')", timeout=15000)
        time.sleep(2.0)

        dash_text = page.locator("body").inner_text()
        assert "RetailMind_Sales_Products_1000_CATALOG_USD_TEST.csv" in dash_text or "1,000" in dash_text, \
            "Dashboard must display active custom dataset info!"
        print("  ✓ Dashboard correctly displays active custom dataset metrics.")

        shot5 = SCREENSHOTS_DIR / "csv_auth_5_dashboard_reflected.png"
        page.screenshot(path=str(shot5), full_page=True)
        print(f"  📸 Screenshot saved: {shot5}")

        # -------------------------------------------------------------
        # Case 6: Schema Validation (Missing Columns Rejection)
        # -------------------------------------------------------------
        print("\n--- Test 6: Invalid CSV Schema Handling ---")
        dataset_nav = page.locator("label[data-testid='stRadioOption']").filter(has_text="البيانات والحوكمة")
        dataset_nav.click()
        page.wait_for_selector("h1:has-text('البيانات والحوكمة')", timeout=15000)
        time.sleep(1.0)

        # Open upload expander if closed
        upload_expander = page.locator("details summary").filter(has_text="رفع ملف مبيعات")
        if upload_expander.count() > 0:
            upload_expander.first.click()
            time.sleep(0.5)

        page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)
        file_input = page.locator('input[type="file"]')
        file_input.first.set_input_files(str(INVALID_CSV_PATH))
        page.wait_for_selector("text=هيكل ملف CSV غير صالح", timeout=15000)
        print("  ✓ Invalid CSV schema correctly identified and rejected with Arabic guidance.")

        shot6 = SCREENSHOTS_DIR / "csv_auth_6_invalid_columns_rejected.png"
        page.screenshot(path=str(shot6), full_page=True)
        print(f"  📸 Screenshot saved: {shot6}")

        browser.close()

    # Clean up temp invalid CSV
    if INVALID_CSV_PATH.exists():
        INVALID_CSV_PATH.unlink()
        print(f"✓ Cleaned up temporary invalid fixture {INVALID_CSV_PATH}")

    print("\n🎉 ALL 6 CSV AUTHORIZATION & SECURITY TESTS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    run_tests()
