import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page()
    page.goto("http://127.0.0.1:8501")
    page.wait_for_timeout(3000)

    icon = page.locator('[data-testid="stIconMaterial"]').first
    computed_font = icon.evaluate("el => window.getComputedStyle(el).fontFamily")
    print("Computed fontFamily of stIconMaterial:", repr(computed_font))
    computed_width = icon.evaluate("el => el.getBoundingClientRect().width")
    print("Computed width of stIconMaterial:", computed_width)
    b.close()
