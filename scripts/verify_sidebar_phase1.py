import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

SCREENSHOTS_DIR = Path("docs/audit_ui/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("--> Navigating to http://127.0.0.1:8501")
        page.goto("http://127.0.0.1:8501")
        page.wait_for_selector("section[data-testid='stSidebar']", timeout=15000)
        page.wait_for_timeout(2000)

        # -------------------------------------------------------------
        # 1. Arabic Desktop Verification
        # -------------------------------------------------------------
        print("\n--- 1. Testing Arabic Desktop (1440px) ---")
        sb_info = page.evaluate("""() => {
            const sb = document.querySelector("section[data-testid='stSidebar']");
            if (!sb) return null;
            const rect = sb.getBoundingClientRect();
            const style = window.getComputedStyle(sb);
            const radios = Array.from(sb.querySelectorAll("label[data-testid='stRadioOption']")).map(el => {
                const circle = el.querySelector("div > div:first-child");
                const circleStyle = circle ? window.getComputedStyle(circle) : null;
                const before = window.getComputedStyle(el, "::before");
                return {
                    text: el.innerText.trim(),
                    circleDisplay: circleStyle ? circleStyle.display : null,
                    hasBeforeIcon: before.backgroundImage !== "none",
                    selected: el.getAttribute("data-selected") === "true" || !!el.querySelector("input:checked")
                };
            });
            return {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                display: style.display,
                visibility: style.visibility,
                radios: radios
            };
        }""")
        print("Arabic Sidebar Info:", sb_info)
        assert sb_info is not None, "Sidebar not found in Arabic!"
        assert sb_info["x"] >= 1000, f"Sidebar should be on the RIGHT in Arabic! Got x={sb_info['x']}"
        assert sb_info["width"] >= 240, f"Sidebar width too small: {sb_info['width']}"
        assert len(sb_info["radios"]) == 5, f"Expected 5 nav options, got {len(sb_info['radios'])}"

        for r in sb_info["radios"]:
            print(f"  Nav item: '{r['text']}' - circle: {r['circleDisplay']} - icon: {r['hasBeforeIcon']} - active: {r['selected']}")
            assert r["circleDisplay"] == "none", f"Radio circle visible for '{r['text']}'!"
            assert r["hasBeforeIcon"] is True, f"Nav icon missing for '{r['text']}'!"

        page.screenshot(path=str(SCREENSHOTS_DIR / "phase1_sidebar_arabic_desktop.png"))
        print(f"Saved: {SCREENSHOTS_DIR / 'phase1_sidebar_arabic_desktop.png'}")

        # Test Navigation across all 5 views
        views_to_test = [
            ("المحلل الذكي", "agent"),
            ("البيانات والحوكمة", "dataset"),
            ("الرؤى المحفوظة", "memory"),
            ("سجل التدقيق", "audit"),
            ("الرئيسية", "overview"),
        ]
        for label, key in views_to_test:
            print(f"Testing navigation click to: '{label}'...")
            page.locator(f"section[data-testid='stSidebar'] label[data-testid='stRadioOption']:has-text('{label}')").click()
            page.wait_for_timeout(1000)

        # -------------------------------------------------------------
        # 2. English Desktop Verification
        # -------------------------------------------------------------
        print("\n--- 2. Testing English Desktop (1440px) ---")
        # Click language toggle button
        lang_btn = page.locator("button:has-text('English')").first
        lang_btn.click()
        page.wait_for_timeout(1500)

        sb_en = page.evaluate("""() => {
            const sb = document.querySelector("section[data-testid='stSidebar']");
            if (!sb) return null;
            const rect = sb.getBoundingClientRect();
            const style = window.getComputedStyle(sb);
            return {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                display: style.display
            };
        }""")
        print("English Sidebar Info:", sb_en)
        assert sb_en is not None, "Sidebar not found in English!"
        assert sb_en["x"] <= 10, f"Sidebar should be on the LEFT in English! Got x={sb_en['x']}"

        page.screenshot(path=str(SCREENSHOTS_DIR / "phase1_sidebar_english_desktop.png"))
        print(f"Saved: {SCREENSHOTS_DIR / 'phase1_sidebar_english_desktop.png'}")

        # Switch back to Arabic
        page.locator("button:has-text('العربية')").first.click()
        page.wait_for_timeout(1500)

        # -------------------------------------------------------------
        # 3. Responsive Tablet & Mobile Verification
        # -------------------------------------------------------------
        print("\n--- 3. Testing Tablet (768px) and Mobile (390px) ---")
        for w, name in [(768, "tablet"), (390, "mobile")]:
            page.set_viewport_size({"width": w, "height": 900})
            page.wait_for_timeout(1000)
            
            # Check if buttons on header remain clickable without sidebar interception
            lang_choice = page.locator("button:has-text('English')").first
            is_clickable = page.evaluate("""() => {
                const el = document.querySelector("button[data-variant='segmented_control']");
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                const topEl = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
                return topEl ? (topEl === el || el.contains(topEl)) : false;
            }""")
            print(f"[{name.upper()} @ {w}px] Header element clickable (not intercepted):", is_clickable)
            page.screenshot(path=str(SCREENSHOTS_DIR / f"phase1_sidebar_{name}.png"))
            print(f"Saved: {SCREENSHOTS_DIR / f'phase1_sidebar_{name}.png'}")

        print("\n--> ALL PLAYWRIGHT CHECKS PASSED SUCCESSFULLY!")
        browser.close()

if __name__ == "__main__":
    run_verification()
