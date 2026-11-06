import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page()
        page.goto("http://127.0.0.1:8501")
        page.wait_for_selector('[data-testid="stSidebar"]', timeout=20000)
        
        print("=== CHECKING ALL BUTTONS ===")
        buttons = page.locator("button")
        print("Total buttons:", buttons.count())
        for i in range(buttons.count()):
            btn = buttons.nth(i)
            print(f"Button {i}: text={repr(btn.inner_text())}, role={btn.get_attribute('role')}, data-testid={btn.get_attribute('data-testid')}")

        print("\n=== CHECKING TOP HEADER ELEMENTS ===")
        # Look at the first column block
        col_blocks = page.locator('[data-testid="stHorizontalBlock"]')
        print("Horizontal blocks count:", col_blocks.count())
        if col_blocks.count() > 0:
            print("First horizontal block inner HTML:")
            print(col_blocks.first.evaluate("el => el.innerHTML")[:1200])

        b.close()

if __name__ == "__main__":
    main()
