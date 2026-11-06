import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', headless=True)
    page = b.new_page()
    page.goto('http://127.0.0.1:8501')
    page.wait_for_selector('[data-testid="stSidebar"]', timeout=30000)
    time.sleep(3)
    
    radios = page.locator('[data-testid="stRadio"] label')
    print('Radio label count:', radios.count())
    for i in range(radios.count()):
        print(f"  Option {i}: {radios.nth(i).inner_text()}")
        
    buttons = page.locator('button')
    print('Buttons count:', buttons.count())
    for i in range(buttons.count()):
        print(f"  Button {i}: {repr(buttons.nth(i).inner_text())}")
        
    b.close()
