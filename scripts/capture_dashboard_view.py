from playwright.sync_api import sync_playwright
import time
import shutil
from pathlib import Path

out_dir = Path("docs/audit_ui/screenshots")
out_dir.mkdir(parents=True, exist_ok=True)
art_dir = Path(r"C:\Users\HP\.gemini\antigravity\brain\1c7d81ed-4bea-496f-bf76-9bdfffeebb00")
art_dir.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501", timeout=60000)
    page.wait_for_selector("section[data-testid='stSidebar']", timeout=30000)
    time.sleep(2)

    # Ensure Arabic language is selected
    ar_lang = page.locator("button:has-text('العربية')")
    if ar_lang.count() > 0:
        ar_lang.first.click()
        time.sleep(2)

    # Check if sample data button is visible on onboarding screen and click it
    sample_btn = page.locator("button:has-text('تحميل بيانات تجريبية'), button:has-text('تحميل بيانات مبيعات تجريبية')")
    if sample_btn.count() > 0:
        sample_btn.first.click()
        time.sleep(4)

    # Ensure overview view is active (first radio option)
    radios = page.locator("label[data-testid='stRadioOption']")
    if radios.count() > 0:
        radios.first.click()
        time.sleep(2)

    # Wait for the main KPI grid to be rendered
    page.wait_for_selector(".kpi-grid", timeout=15000)
    time.sleep(2)

    screenshot_path = out_dir / "reference_3_dashboard_ar.png"
    page.screenshot(path=str(screenshot_path), full_page=False)
    print(f"Screenshot saved to {screenshot_path}")

    # Copy to artifact dir
    art_path = art_dir / "reference_3_dashboard_ar.png"
    shutil.copy2(screenshot_path, art_path)
    print(f"Screenshot copied to artifact dir: {art_path}")

    browser.close()
