from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501")
    page.wait_for_selector("section[data-testid='stSidebar']")

    # Check across languages
    for lang in ["ar", "en"]:
        if lang == "ar":
            page.locator("button:has-text('العربية')").first.click()
        else:
            page.locator("button:has-text('English')").first.click()
        page.wait_for_timeout(1000)

        for width in [1440, 1024, 768, 390]:
            page.set_viewport_size({"width": width, "height": 900})
            page.wait_for_timeout(500)
            status = page.evaluate("""() => {
                const sb = document.querySelector("section[data-testid='stSidebar']");
                const rect = sb ? sb.getBoundingClientRect() : null;
                const style = sb ? window.getComputedStyle(sb) : null;
                return {
                    exists: !!sb,
                    rect: rect ? { x: rect.x, y: rect.y, width: rect.width, height: rect.height } : null,
                    display: style ? style.display : null,
                    visibility: style ? style.visibility : null,
                    transform: style ? style.transform : null,
                    zIndex: style ? style.zIndex : null
                };
            }""")
            print(f"[{lang.upper()} @ {width}px] Sidebar:", status)

    b.close()
