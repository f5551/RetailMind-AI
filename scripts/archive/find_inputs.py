import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=agent&mock_agent_view=1", timeout=20000)
    page.wait_for_selector(".execution-stepper", timeout=15000)
    
    # Check if there are any inputs or textareas anywhere on page
    inputs = page.locator("input, textarea").all()
    print(f"Total inputs/textareas on page: {len(inputs)}")
    for inp in inputs:
        tag = inp.evaluate("el => el.tagName")
        ph = inp.get_attribute("placeholder")
        aria = inp.get_attribute("aria-label")
        print(f"  Tag: {tag}, Placeholder: {ph}, Aria: {aria}")
        
    bottom = page.locator(".stBottom, [data-testid='stBottom']").all()
    print(f"Bottom elements: {len(bottom)}")
    browser.close()
