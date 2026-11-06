import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        context = b.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto("http://127.0.0.1:8501")
        page.wait_for_timeout(3000)

        # Click Load Synthetic Sample Data button
        load_btn = page.locator("button:has-text('Load Synthetic Sample Data')")
        if load_btn.count() == 0:
            load_btn = page.locator("button:has-text('Load Benchmark Dataset')")
        if load_btn.count() > 0:
            load_btn.first.click()
            page.wait_for_timeout(4000)
            print("Loaded benchmark dataset.")
        else:
            print("Could not find load button!")

        # Check chart headers and texts
        headers = page.locator("h3").all_text_contents()
        print("Subheaders found:", headers)

        # Find vega-lite or chart containers
        vega_charts = page.locator('[data-testid="stVegaLiteChart"]')
        print("Vega-Lite charts count:", vega_charts.count())

        # Screenshot the charts specifically
        for idx in range(vega_charts.count()):
            chart = vega_charts.nth(idx)
            chart.screenshot(path=f"docs/audit_ui/screenshots/chart_{idx}.png")
            print(f"Saved chart_{idx}.png")
            # Extract SVG text elements from inside chart
            texts = chart.locator("svg text").all_text_contents()
            print(f"Chart {idx} SVG text elements:", texts)

        # Full page screenshot populated EN
        page.screenshot(path="docs/audit_ui/screenshots/populated_en_full.png", full_page=True)
        print("Saved populated_en_full.png")

        b.close()

if __name__ == "__main__":
    main()
