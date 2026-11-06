import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=agent&mock_agent_view=1", timeout=20000)
    page.wait_for_selector(".execution-stepper", timeout=15000)
    
    html = page.content()
    print("Does HTML contain 'chat_input' or 'ChatInput'?:", "chatinput" in html.lower())
    print("Does HTML contain 'اطرح سؤالاً'?:", "اطرح سؤالاً" in html)
    print("Does HTML contain 'chat_input_prompt'?:", "chat_input_prompt" in html)
    
    # Print the last 1000 characters of the main content container
    main_el = page.locator(".main")
    if main_el.count() > 0:
        print("Main inner text tail:\n", main_el.first.inner_text()[-500:])
    browser.close()
