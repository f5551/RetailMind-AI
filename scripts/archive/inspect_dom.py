from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page()
    page.goto("http://127.0.0.1:8501")
    page.wait_for_selector("section[data-testid='stSidebar']")
    info = page.evaluate("""() => {
        const sb = document.querySelector("section[data-testid='stSidebar']");
        const parent = sb.parentElement;
        const computed = window.getComputedStyle(parent);
        return {
            parentTag: parent.tagName,
            parentClass: parent.className,
            parentTestId: parent.getAttribute("data-testid"),
            flexDirection: computed.flexDirection,
            display: computed.display,
            order: window.getComputedStyle(sb).order
        };
    }""")
    print("Parent info:", info)
    b.close()
