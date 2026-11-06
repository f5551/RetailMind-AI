import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

def test_toggle():
    print("🚀 Testing Sidebar Collapse and Reopen in Arabic and English...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 950})
        page.goto("http://127.0.0.1:8501/?view=overview", timeout=20000)
        page.wait_for_selector("h1", timeout=15000)
        
        sb = page.locator('section[data-testid="stSidebar"]')
        assert sb.is_visible(), "Sidebar should be initially visible!"
        
        # 1. Arabic Collapse & Reopen
        print("\n--- Arabic RTL Test ---")
        collapse_btn = page.locator('[data-testid="stSidebarCollapseButton"] button')
        collapse_btn.click()
        page.wait_for_timeout(1000)
        assert not sb.is_visible()
        expand_btn = page.locator('[data-testid="stExpandSidebarButton"]')
        assert expand_btn.is_visible()
        box_ar = expand_btn.bounding_box()
        print(f"Arabic expand button position: x={box_ar['x']}, y={box_ar['y']}")
        assert box_ar["x"] > 1000, "In Arabic, expand button must be on the right!"
        expand_btn.click()
        page.wait_for_timeout(1000)
        assert sb.is_visible()
        print("✓ Arabic RTL collapse and reopen passed.")
        
        # 2. Switch to English
        print("\n--- English LTR Test ---")
        en_opt = page.get_by_text("English", exact=True)
        en_opt.click()
        page.wait_for_timeout(1500)
        
        # Collapse in English
        collapse_btn = page.locator('[data-testid="stSidebarCollapseButton"] button')
        collapse_btn.click()
        page.wait_for_timeout(1000)
        assert not sb.is_visible()
        expand_btn = page.locator('[data-testid="stExpandSidebarButton"]')
        assert expand_btn.is_visible()
        box_en = expand_btn.bounding_box()
        print(f"English expand button position: x={box_en['x']}, y={box_en['y']}")
        assert box_en["x"] < 100, f"In English, expand button must be on the left (x < 100), got {box_en['x']}!"
        expand_btn.click()
        page.wait_for_timeout(1000)
        assert sb.is_visible()
        print("✓ English LTR collapse and reopen passed.")
        
        print("\n🎉 ALL BILINGUAL TOGGLE TESTS PASSED PERFECTLY!")
        browser.close()

if __name__ == "__main__":
    test_toggle()
