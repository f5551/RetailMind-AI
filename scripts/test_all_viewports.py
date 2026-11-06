import shutil
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\c471b13a-7b87-44d9-9a85-39a116863fa9")
OUTPUT_DIR = Path(r"C:\Users\HP\Desktop\RetailMind A\docs\audit_ui\screenshots")

VIEWPORTS = [
    ("12_responsive_laptop_1366x768_after.png", 1366, 768),
    ("13_responsive_tablet_768x1024_after.png", 768, 1024),
    ("14_responsive_mobile_390x844_after.png", 390, 844),
    ("15_responsive_small_mobile_360x800_after.png", 360, 800),
]

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8501")
        page.wait_for_timeout(2500)

        # Ensure sample data loaded
        sample_btn = page.locator('button:has-text("Load Synthetic Sample Data"), button:has-text("Load Benchmark Dataset")')
        if sample_btn.count() > 0:
            sample_btn.first.click()
            page.wait_for_timeout(3000)

        for filename, width, height in VIEWPORTS:
            print(f"--- Testing Viewport {width}x{height} ---")
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(1500)

            kpi_cards = page.locator('.kpi-card')
            count = kpi_cards.count()
            print(f"Viewport {width}x{height}: {count} KPI cards")
            if count > 0:
                box = kpi_cards.first.bounding_box()
                val = kpi_cards.first.locator('.kpi-value').inner_text()
                print(f"First Card: Width={box['width']:.1f}px, Value='{val}'")

            shot_path = OUTPUT_DIR / filename
            page.screenshot(path=str(shot_path), full_page=True)
            if ARTIFACT_DIR.exists():
                shutil.copy2(shot_path, ARTIFACT_DIR / filename)
            print(f"Saved {filename} ({shot_path.stat().st_size // 1024} KB)")

        b.close()

if __name__ == "__main__":
    main()
