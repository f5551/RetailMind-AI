from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501")
    page.wait_for_selector("section[data-testid='stSidebar']")

    # Click collapse button
    btn = page.locator("[data-testid='stSidebarCollapseButton']")
    if btn.count() > 0:
        btn.first.click()
        page.wait_for_timeout(1000)

    info_after = page.evaluate("""() => {
        const sb = document.querySelector("section[data-testid='stSidebar']");
        const collapsedControl = document.querySelector("[data-testid='stSidebarCollapsedControl']");
        const allButtons = Array.from(document.querySelectorAll('button')).map(b => ({
            text: b.innerText,
            ariaLabel: b.getAttribute('aria-label'),
            className: b.className,
            testId: b.getAttribute('data-testid')
        }));
        return {
            sbWidth: window.getComputedStyle(sb).width,
            sbTransform: window.getComputedStyle(sb).transform,
            sbDisplay: window.getComputedStyle(sb).display,
            hasCollapsedControl: !!collapsedControl,
            collapsedControlPos: collapsedControl ? window.getComputedStyle(collapsedControl).position : null,
            collapsedControlDisplay: collapsedControl ? window.getComputedStyle(collapsedControl).display : null,
            collapsedControlVis: collapsedControl ? window.getComputedStyle(collapsedControl).visibility : null,
            allButtons: allButtons.filter(x => x.ariaLabel || x.testId)
        };
    }""")
    print("After collapse click:", info_after)

    b.close()
