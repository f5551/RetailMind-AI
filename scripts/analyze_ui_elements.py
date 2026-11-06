import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

def analyze():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 950})

        views = ["overview", "agent", "dataset", "memory", "audit"]
        results = {}

        for v in views:
            page.goto(f"http://127.0.0.1:8501/?view={v}&load_sample=1&mock_agent_view=1", timeout=30000)
            page.wait_for_selector("h1", timeout=15000)
            page.wait_for_timeout(2000)

            # Extract buttons
            buttons = [b.inner_text().strip() for b in page.locator("button").all() if b.is_visible()]
            
            # Extract badges / pills
            badges = [el.inner_text().strip() for el in page.locator(".status-badge, .col-match-pill, .header-date-pill").all() if el.is_visible()]

            # Extract headers
            h1 = [h.inner_text().strip() for h in page.locator("h1").all() if h.is_visible()]
            h2_h3 = [h.inner_text().strip() for h in page.locator("h2, h3").all() if h.is_visible()]

            # Extract all text in main
            main_text = page.locator("div.block-container").inner_text()

            # Extract sidebar text
            sidebar_text = page.locator("section[data-testid='stSidebar']").inner_text()

            results[v] = {
                "h1": h1,
                "h2_h3": h2_h3,
                "buttons": buttons,
                "badges": badges,
                "main_preview": main_text[:600],
                "sidebar_preview": sidebar_text[:400],
            }

        print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    analyze()
