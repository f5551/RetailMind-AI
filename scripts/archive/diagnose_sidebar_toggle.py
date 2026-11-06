import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=overview", timeout=20000)
    page.wait_for_selector("h1", timeout=15000)
    
    print("--- 1. Initial State (Sidebar Expanded) ---")
    sidebar = page.locator('section[data-testid="stSidebar"]')
    print("Sidebar count:", sidebar.count())
    print("Sidebar is_visible:", sidebar.is_visible())
    
    # Check collapse controls
    collapse_btn = page.locator('[data-testid="stSidebarCollapseButton"]')
    print("stSidebarCollapseButton count:", collapse_btn.count())
    if collapse_btn.count() > 0:
        print("stSidebarCollapseButton is_visible:", collapse_btn.first.is_visible())
        print("stSidebarCollapseButton parent tag:", collapse_btn.first.evaluate("el => el.parentElement.tagName + '.' + el.parentElement.className"))
        
    collapsed_ctrl = page.locator('[data-testid="stSidebarCollapsedControl"]')
    print("stSidebarCollapsedControl count:", collapsed_ctrl.count())
    if collapsed_ctrl.count() > 0:
        print("stSidebarCollapsedControl is_visible:", collapsed_ctrl.first.is_visible())
        print("stSidebarCollapsedControl parent:", collapsed_ctrl.first.evaluate("el => el.parentElement.tagName + '.' + el.parentElement.className"))
        
    print("\n--- 2. Clicking Collapse Button ---")
    if collapse_btn.count() > 0 and collapse_btn.first.is_visible():
        collapse_btn.first.click()
        page.wait_for_timeout(1000)
        
        print("After collapse:")
        print("Sidebar is_visible:", sidebar.is_visible())
        print("stSidebarCollapseButton count:", collapse_btn.count(), "is_visible:", collapse_btn.first.is_visible() if collapse_btn.count() > 0 else False)
        print("stSidebarCollapsedControl count:", collapsed_ctrl.count(), "is_visible:", collapsed_ctrl.first.is_visible() if collapsed_ctrl.count() > 0 else False)
        if collapsed_ctrl.count() > 0:
            box = collapsed_ctrl.first.bounding_box()
            print("stSidebarCollapsedControl bounding box:", box)
            css_styles = collapsed_ctrl.first.evaluate("""el => {
                const s = window.getComputedStyle(el);
                return {
                    display: s.display,
                    visibility: s.visibility,
                    opacity: s.opacity,
                    position: s.position,
                    top: s.top,
                    right: s.right,
                    left: s.left,
                    zIndex: s.zIndex,
                    pointerEvents: s.pointerEvents
                };
            }""")
            print("stSidebarCollapsedControl computed styles:", css_styles)
            
    browser.close()
