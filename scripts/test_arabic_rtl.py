import shutil
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\c471b13a-7b87-44d9-9a85-39a116863fa9")
OUTPUT_DIR = Path(r"C:\Users\HP\Desktop\RetailMind A\docs\audit_ui\screenshots")

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8501")
        page.wait_for_timeout(3000)

        # 1. Click Arabic in Language Toggle
        ar_radio = page.locator('label:has-text("العربية")')
        if ar_radio.count() > 0:
            print("Found Arabic radio label. Clicking...")
            ar_radio.first.click()
            page.wait_for_timeout(3000)

        # Capture Arabic Overview Dashboard
        shot_path = OUTPUT_DIR / "07_arabic_rtl_overview_dashboard_after.png"
        page.screenshot(path=str(shot_path), full_page=True)
        if ARTIFACT_DIR.exists():
            shutil.copy2(shot_path, ARTIFACT_DIR / "07_arabic_rtl_overview_dashboard_after.png")
        print(f"Saved {shot_path} ({shot_path.stat().st_size // 1024} KB)")

        # Navigate to Agent view in Arabic
        agent_radio = page.locator('label:has-text("وكيل المبيعات")')
        if agent_radio.count() > 0:
            agent_radio.first.click()
            page.wait_for_timeout(2500)
            shot2 = OUTPUT_DIR / "09_arabic_rtl_agent_chat_after.png"
            page.screenshot(path=str(shot2), full_page=True)
            if ARTIFACT_DIR.exists():
                shutil.copy2(shot2, ARTIFACT_DIR / "09_arabic_rtl_agent_chat_after.png")
            print("Saved Arabic Agent view")

        # Navigate to Dataset Ingestion in Arabic
        ds_radio = page.locator('label:has-text("استيراد وتدقيق")')
        if ds_radio.count() > 0:
            ds_radio.first.click()
            page.wait_for_timeout(2500)
            shot3 = OUTPUT_DIR / "08_arabic_rtl_dataset_view_after.png"
            page.screenshot(path=str(shot3), full_page=True)
            if ARTIFACT_DIR.exists():
                shutil.copy2(shot3, ARTIFACT_DIR / "08_arabic_rtl_dataset_view_after.png")
            print("Saved Arabic Dataset view")

        b.close()

if __name__ == "__main__":
    main()
