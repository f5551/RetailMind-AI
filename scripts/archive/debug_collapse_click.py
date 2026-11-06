import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=overview", timeout=20000)
    page.wait_for_selector("h1", timeout=15000)
    
    sb = page.locator('section[data-testid="stSidebar"]')
    print("Initial Sidebar attributes:", sb.evaluate("el => ({collapsed: el.getAttribute('data-collapsed'), expanded: el.getAttribute('aria-expanded'), className: el.className})"))
    
    # Hover over sidebar header to make button visible
    header = page.locator('[data-testid="stSidebarHeader"]')
    header.hover()
    page.wait_for_timeout(500)
    
    btn = page.locator('[data-testid="stSidebarCollapseButton"] button')
    print("Button visible after hover?", btn.is_visible())
    
    btn.click()
    page.wait_for_timeout(1000)
    
    print("After click attributes:", sb.evaluate("el => ({collapsed: el.getAttribute('data-collapsed'), expanded: el.getAttribute('aria-expanded'), className: el.className})"))
    print("Sidebar is_visible:", sb.is_visible())
    
    # Check what collapsed control exists
    print("stSidebarCollapsedControl count:", page.locator('[data-testid="stSidebarCollapsedControl"]').count())
    print("All buttons on page after collapse:")
    for b in page.locator("button").all():
        print("  aria-label:", repr(b.get_attribute("aria-label")), "testid:", repr(b.get_attribute("data-testid")), "visible:", b.is_visible())
    browser.close()
