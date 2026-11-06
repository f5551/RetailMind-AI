from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501")
    page.wait_for_selector("section[data-testid='stSidebar']")

    info = page.evaluate("""() => {
        const sb = document.querySelector("section[data-testid='stSidebar']");
        const collapseBtn = document.querySelector("[data-testid='stSidebarCollapseButton']");
        const collapsedControl = document.querySelector("[data-testid='stSidebarCollapsedControl']");
        return {
            sbDisplay: window.getComputedStyle(sb).display,
            sbVisibility: window.getComputedStyle(sb).visibility,
            sbWidth: window.getComputedStyle(sb).width,
            sbTransform: window.getComputedStyle(sb).transform,
            sbAriaExpanded: sb.getAttribute("aria-expanded"),
            hasCollapseBtn: !!collapseBtn,
            hasCollapsedControl: !!collapsedControl
        };
    }""")
    print("Desktop 1440 expanded:", info)

    # Now test mobile viewport (390x844)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(1000)
    info_mobile = page.evaluate("""() => {
        const sb = document.querySelector("section[data-testid='stSidebar']");
        const collapseBtn = document.querySelector("[data-testid='stSidebarCollapseButton']");
        const collapsedControl = document.querySelector("[data-testid='stSidebarCollapsedControl']");
        return {
            sbDisplay: sb ? window.getComputedStyle(sb).display : 'none',
            sbVisibility: sb ? window.getComputedStyle(sb).visibility : 'none',
            sbWidth: sb ? window.getComputedStyle(sb).width : '0',
            sbTransform: sb ? window.getComputedStyle(sb).transform : 'none',
            sbAriaExpanded: sb ? sb.getAttribute("aria-expanded") : null,
            hasCollapseBtn: !!collapseBtn,
            hasCollapsedControl: !!collapsedControl,
            collapsedControlDisplay: collapsedControl ? window.getComputedStyle(collapsedControl).display : 'none',
            collapsedControlPos: collapsedControl ? {
                left: window.getComputedStyle(collapsedControl).left,
                right: window.getComputedStyle(collapsedControl).right,
                top: window.getComputedStyle(collapsedControl).top,
                visibility: window.getComputedStyle(collapsedControl).visibility
            } : null
        };
    }""")
    print("Mobile 390 state:", info_mobile)

    b.close()
