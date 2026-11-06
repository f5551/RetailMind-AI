import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        context = b.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto("http://127.0.0.1:8501")
        page.wait_for_timeout(3000)

        # First load benchmark dataset in English to make sure it's loaded
        load_btn_en = page.locator("button:has-text('Load Benchmark Dataset')")
        if load_btn_en.count() == 0:
            load_btn_en = page.locator("button:has-text('Load Synthetic Sample Data')")
        if load_btn_en.count() > 0:
            load_btn_en.first.click()
            page.wait_for_timeout(3500)
            print("Loaded benchmark in English first.")

        # Switch to Arabic
        ar_radio = page.locator('div[data-testid="stRadio"] label:has-text("العربية")')
        if ar_radio.count() > 0:
            ar_radio.first.click()
            page.wait_for_timeout(4000)
            print("Switched to Arabic.")

        # Check chart headers and texts
        headers = page.locator("h3").all_text_contents()
        print("Subheaders found (AR):", headers)

        charts = page.locator('[data-testid="stVegaLiteChart"]')
        print("Vega-Lite charts count (AR):", charts.count())

        for idx in range(charts.count()):
            chart = charts.nth(idx)
            chart.screenshot(path=f"docs/audit_ui/screenshots/chart_ar_{idx}.png")
            texts = chart.locator("svg text").all_text_contents()
            print(f"Chart {idx} (AR) SVG texts:", texts)

        page.screenshot(path="docs/audit_ui/screenshots/populated_ar_full.png", full_page=True)
        print("Saved populated_ar_full.png")

        b.close()

if __name__ == "__main__":
    main()
