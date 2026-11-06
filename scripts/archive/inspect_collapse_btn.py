import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=overview", timeout=20000)
    page.wait_for_selector("h1", timeout=15000)
    
    btn = page.locator('[data-testid="stSidebarCollapseButton"]')
    if btn.count() > 0:
        styles = btn.evaluate("""el => {
            const s = window.getComputedStyle(el);
            const parent = el.parentElement ? window.getComputedStyle(el.parentElement) : {};
            return {
                display: s.display,
                visibility: s.visibility,
                opacity: s.opacity,
                width: s.width,
                height: s.height,
                parentDisplay: parent.display,
                parentVisibility: parent.visibility
            };
        }""")
        print("stSidebarCollapseButton styles:", styles)
        
        # Check inner button/svg
        inner = btn.locator("button")
        print("Inner buttons:", inner.count())
        if inner.count() > 0:
            bstyles = inner.first.evaluate("el => ({display: window.getComputedStyle(el).display, visibility: window.getComputedStyle(el).visibility})")
            print("Inner button styles:", bstyles)
            
    sb = page.locator('section[data-testid="stSidebar"]')
    print("Clicking collapse button (force=True)...")
    btn.locator("button").click(force=True)
    page.wait_for_timeout(1500)
    
    print("\n--- After Collapse ---")
    print("Sidebar is_visible:", sb.is_visible())
    
    # What controls exist now?
    all_btns = page.locator("button").all()
    for b in all_btns:
        aria = b.get_attribute("aria-label")
        testid = b.get_attribute("data-testid")
        vis = b.is_visible()
        if any(k in (aria or "").lower() for k in ["sidebar", "expand", "collapse"]):
            print(f"Sidebar-related button: aria={aria}, testid={testid}, visible={vis}")
            
    # Check stSidebarCollapsedControl
    collapsed_ctrl = page.locator('[data-testid="stSidebarCollapsedControl"]')
    print("stSidebarCollapsedControl count:", collapsed_ctrl.count())
    if collapsed_ctrl.count() > 0:
        cstyles = collapsed_ctrl.first.evaluate("""el => {
            const s = window.getComputedStyle(el);
            return {
                display: s.display,
                visibility: s.visibility,
                opacity: s.opacity,
                box: el.getBoundingClientRect()
            };
        }""")
        print("stSidebarCollapsedControl styles:", cstyles)
    browser.close()
