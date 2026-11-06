import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page()
    page.goto("http://127.0.0.1:8501")
    page.wait_for_selector("section[data-testid='stSidebar']")
    page.wait_for_timeout(2000)
    info = page.evaluate("""() => {
        const labels = Array.from(document.querySelectorAll("label[data-testid='stRadioOption']"));
        // Check stylesheets for the rule
        let foundRules = [];
        for (let sheet of document.styleSheets) {
            try {
                for (let rule of sheet.cssRules) {
                    if (rule.selectorText && rule.selectorText.includes("radiogroup")) {
                        foundRules.push(rule.cssText);
                    }
                }
            } catch (e) {}
        }
        return {
            foundRules: foundRules,
            before0: window.getComputedStyle(labels[0], "::before").cssText
        };
    }""")
    print("CSS info:")
    for r in info["foundRules"][:10]:
        print("  Rule:", r)
    b.close()
