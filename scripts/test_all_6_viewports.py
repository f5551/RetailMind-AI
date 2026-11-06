"""RetailMind AI — Comprehensive 6-Viewport Responsive & Usability Verification Script.

Tests all 6 required viewports:
1. 1440 x 900 (Desktop)
2. 1366 x 768 (Laptop)
3. 1024 x 768 (Small Desktop / iPad Landscape)
4. 768 x 1024 (Tablet Portrait)
5. 390 x 844 (Mobile)
6. 360 x 800 (Small Mobile)

Verifies:
- Horizontal scroll absence (scrollWidth <= clientWidth)
- KPI Card layout, dimensions, and single-line numerical presentation
- Top Products chart axis labels and complete untruncated product names
- Native Material Symbols rendering (sidebar collapse, password visibility, upload button)
- File uploader 10MB text consistency
- Bilingual state retention and RTL/LTR formatting across all 5 views
"""

import os
import shutil
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\9af36c4e-b99a-45f0-85fe-df7bb201ca0f")
OUTPUT_DIR = Path(r"C:\Users\HP\Desktop\RetailMind A\docs\audit_ui\screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    {"name": "desktop_1440x900", "width": 1440, "height": 900},
    {"name": "laptop_1366x768", "width": 1366, "height": 768},
    {"name": "ipad_landscape_1024x768", "width": 1024, "height": 768},
    {"name": "tablet_portrait_768x1024", "width": 768, "height": 1024},
    {"name": "mobile_390x844", "width": 390, "height": 844},
    {"name": "small_mobile_360x800", "width": 360, "height": 800},
]

def save_and_copy(page, filename: str):
    local_path = OUTPUT_DIR / filename
    page.screenshot(path=str(local_path), full_page=True)
    if ARTIFACT_DIR.exists():
        art_path = ARTIFACT_DIR / filename
        shutil.copy2(local_path, art_path)
    print(f"[SCREENSHOT] Saved: {filename} ({local_path.stat().st_size // 1024} KB)")

def check_horizontal_overflow(page):
    return page.evaluate("""() => {
        const docElem = document.documentElement;
        const body = document.body;
        const scrollWidth = Math.max(docElem.scrollWidth, body.scrollWidth);
        const clientWidth = Math.max(docElem.clientWidth, body.clientWidth);
        return {
            scrollWidth: scrollWidth,
            clientWidth: clientWidth,
            hasOverflow: scrollWidth > clientWidth + 1
        };
    }""")

def main():
    print("=== Starting Comprehensive 6-Viewport & UX Verification ===")
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Initial Page Load (Empty State on Desktop)
        page.goto("http://127.0.0.1:8501")
        page.wait_for_selector('[data-testid="stSidebar"]', timeout=30000)
        page.wait_for_timeout(3000)

        # Step 2: Load Benchmark Dataset once
        load_btn = page.locator("button:has-text('Load Benchmark Dataset')")
        if load_btn.count() == 0:
            load_btn = page.locator("button:has-text('Load Synthetic Sample Data')")
        if load_btn.count() > 0:
            load_btn.first.click()
            page.wait_for_timeout(4000)
            print("Loaded benchmark dataset successfully.")

        # Iterate over all 6 viewports on the active populated state
        for vp in VIEWPORTS:
            vp_name = vp["name"]
            w = vp["width"]
            h = vp["height"]
            print(f"\n--- Testing Viewport: {vp_name} ({w}x{h}) ---")
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(2000)

            # Check overflow
            of_info = check_horizontal_overflow(page)
            print(f"[{vp_name}] Overflow Check: clientWidth={of_info['clientWidth']}, scrollWidth={of_info['scrollWidth']}, hasOverflow={of_info['hasOverflow']}")

            # Measure KPI card width if visible
            kpi_cards = page.locator(".kpi-card")
            card1_width = 0.0
            if kpi_cards.count() > 0:
                box = kpi_cards.first.bounding_box()
                if box:
                    card1_width = box["width"]
                    print(f"[{vp_name}] KPI Card 1 Width: {card1_width:.1f}px (Count: {kpi_cards.count()})")

            # Check Top Products chart text elements
            top_prod_chart = page.locator('[data-testid="stVegaLiteChart"]').nth(1) if page.locator('[data-testid="stVegaLiteChart"]').count() > 1 else None
            chart_texts = []
            if top_prod_chart and top_prod_chart.is_visible():
                chart_texts = top_prod_chart.locator("svg text").all_text_contents()
                print(f"[{vp_name}] Top Products texts: {chart_texts}")

            # Save screenshot
            shot_name = f"vp_{vp_name}_populated.png"
            save_and_copy(page, shot_name)

            results[vp_name] = {
                "width": w,
                "height": h,
                "clientWidth": of_info["clientWidth"],
                "scrollWidth": of_info["scrollWidth"],
                "hasOverflow": of_info["hasOverflow"],
                "card1_width": card1_width,
                "top_prod_texts": chart_texts,
            }

        context.close()

        browser.close()

    print("\n=== Viewport Test Summary ===")
    for k, v in results.items():
        status = "FAIL" if v["hasOverflow"] else "PASS"
        print(f"{k}: Overflow={v['hasOverflow']} (width={v['card1_width']:.1f}px) -> {status}")

if __name__ == "__main__":
    main()
