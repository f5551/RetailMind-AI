import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page()
        page.goto("http://127.0.0.1:8501")
        page.wait_for_selector('[data-testid="stSidebar"]', timeout=20000)
        btn = page.locator('button:has-text("English")')
        print("PARENT OUTER HTML:")
        print(btn.evaluate("el => el.parentElement.outerHTML"))
        b.close()

if __name__ == "__main__":
    main()
