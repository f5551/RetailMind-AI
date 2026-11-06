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
        # 1. Desktop context to load data
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8501")
        page.wait_for_timeout(2500)

        # Load benchmark sample data
        sample_btn = page.locator('button:has-text("Load Synthetic Sample Data"), button:has-text("Load Benchmark Dataset")')
        if sample_btn.count() > 0:
            print("Clicking Load Benchmark Data...")
            sample_btn.first.click()
            page.wait_for_timeout(3500)

        # 2. Resize viewport to 768 x 1024 (Tablet Portrait)
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(2000)

        # Verify KPI cards
        kpi_cards = page.locator('.kpi-card')
        card_count = kpi_cards.count()
        print(f"Found {card_count} KPI cards on tablet (768px)")

        for i in range(card_count):
            card = kpi_cards.nth(i)
            box = card.bounding_box()
            val = card.locator('.kpi-value').inner_text()
            title = card.locator('.kpi-title').inner_text()
            print(f"Card {i+1} [{title}]: Value='{val}', Width={box['width']:.1f}px, Height={box['height']:.1f}px")

        # Capture screenshot
        shot_path = OUTPUT_DIR / "13_responsive_tablet_768x1024_after.png"
        page.screenshot(path=str(shot_path), full_page=True)
        if ARTIFACT_DIR.exists():
            shutil.copy2(shot_path, ARTIFACT_DIR / "13_responsive_tablet_768x1024_after.png")
        print(f"Saved {shot_path} ({shot_path.stat().st_size // 1024} KB)")

        b.close()

if __name__ == "__main__":
    main()
