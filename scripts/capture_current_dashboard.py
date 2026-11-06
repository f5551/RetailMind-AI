import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
SCREENSHOTS_DIR = Path("docs/audit_ui/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501")
    page.wait_for_selector("section[data-testid='stSidebar']")
    time.sleep(2)

    # Click load benchmark dataset button on onboarding screen
    load_btn = page.locator("button:has-text('تحميل البيانات المرجعية')")
    if load_btn.count() > 0:
        print("Clicking load benchmark dataset button...")
        load_btn.first.click()
        time.sleep(4)

    # If still onboarding, try sidebar sample load button
    if page.locator(".kpi-grid").count() == 0:
        print("Opening sidebar dataset expander...")
        exp = page.locator("details:has-text('بيانات الجلسة النشطة') summary")
        if exp.count() > 0:
            exp.first.click()
            time.sleep(1)
            sample_btn = page.locator("button:has-text('تحميل بيانات مبيعات تجريبية')")
            if sample_btn.count() > 0:
                print("Clicking sidebar sample data button...")
                sample_btn.first.click()
                time.sleep(4)

    page.wait_for_selector(".kpi-grid", timeout=20000)
    time.sleep(2)

    # Capture Arabic Dashboard
    page.screenshot(path=str(SCREENSHOTS_DIR / "phase2_dashboard_before.png"), full_page=False)
    print("Saved:", SCREENSHOTS_DIR / "phase2_dashboard_before.png")

    b.close()
