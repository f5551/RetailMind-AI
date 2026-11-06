import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src.retailmind.ui.i18n import TRANSLATIONS
print("chat_input_prompt:", TRANSLATIONS.get("chat_input_prompt"))

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=agent&mock_agent_view=1", timeout=20000)
    page.wait_for_selector(".execution-stepper", timeout=15000)
    
    textareas = page.locator("textarea").all()
    print(f"Found {len(textareas)} textareas:")
    for ta in textareas:
        print("  placeholder:", repr(ta.get_attribute("placeholder")))
        print("  aria-label:", repr(ta.get_attribute("aria-label")))
        print("  data-testid:", repr(ta.get_attribute("data-testid")))
    browser.close()
