from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501")
    page.wait_for_selector("section[data-testid='stSidebar']")
    res = page.evaluate("""() => {
        const el = document.querySelector("[data-testid='stAppViewContainer']");
        const before = window.getComputedStyle(el).flexDirection;
        const styleRules = [];
        for (const sheet of document.styleSheets) {
            try {
                for (const rule of sheet.cssRules) {
                    if (rule.selectorText && rule.selectorText.includes('stAppViewContainer')) {
                        styleRules.push(rule.cssText);
                    }
                }
            } catch (e) {}
        }
        return { before, styleRules };
    }""")
    print("Computed before:", res["before"])
    print("Matching rules:", res["styleRules"])
    b.close()
