import os
import sys
import pandas as pd
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_rendering():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page()
        page.goto("http://127.0.0.1:8501")
        page.wait_for_timeout(3000)

        # Make sure dataset is loaded
        load_btn = page.locator("button:has-text('Load Synthetic Sample Data')")
        if load_btn.count() == 0:
            load_btn = page.locator("button:has-text('Load Benchmark Dataset')")
        if load_btn.count() > 0:
            load_btn.first.click()
            page.wait_for_timeout(3500)

        charts = page.locator('[data-testid="stVegaLiteChart"]')
        print(f"Found {charts.count()} VegaLite charts")
        for i in range(charts.count()):
            texts = charts.nth(i).locator("svg text").all_text_contents()
            print(f"Chart {i} texts: {texts}")

        b.close()

if __name__ == "__main__":
    test_rendering()
