import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page()
    page.goto("http://127.0.0.1:8501")
    page.wait_for_timeout(3000)
    print("Page title:", page.title())
    print("Exception elements:", page.locator('.stException').count())
    if page.locator('.stException').count() > 0:
        print("Exception text:", page.locator('.stException').all_text_contents())
    page.screenshot(path="temp_page.png")
    print("Saved temp_page.png")
    b.close()
