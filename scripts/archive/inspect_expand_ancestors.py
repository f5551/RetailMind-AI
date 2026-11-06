import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=overview", timeout=20000)
    page.wait_for_selector("h1", timeout=15000)
    
    header = page.locator('[data-testid="stSidebarHeader"]')
    header.hover()
    page.wait_for_timeout(300)
    
    page.locator('[data-testid="stSidebarCollapseButton"] button').click()
    page.wait_for_timeout(1000)
    
    exp_btn = page.locator('[data-testid="stExpandSidebarButton"]')
    print("stExpandSidebarButton count:", exp_btn.count())
    if exp_btn.count() > 0:
        info = exp_btn.evaluate("""el => {
            const getAncestors = (node) => {
                const arr = [];
                let curr = node;
                while (curr && curr !== document.body) {
                    const cs = window.getComputedStyle(curr);
                    arr.push({
                        tag: curr.tagName,
                        id: curr.id,
                        testid: curr.getAttribute('data-testid'),
                        className: curr.className,
                        display: cs.display,
                        visibility: cs.visibility,
                        opacity: cs.opacity,
                        zIndex: cs.zIndex,
                        position: cs.position,
                        width: cs.width,
                        height: cs.height,
                        transform: cs.transform
                    });
                    curr = curr.parentElement;
                }
                return arr;
            };
            return getAncestors(el);
        }""")
        for idx, anc in enumerate(info):
            print(f"[{idx}] {anc['tag']} testid={anc['testid']} display={anc['display']} visibility={anc['visibility']} opacity={anc['opacity']} width={anc['width']} height={anc['height']}")
    browser.close()
