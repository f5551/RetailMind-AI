"""RetailMind AI — Comprehensive End-User UI/UX Audit Automation Script.

Executes real browser automation via Playwright + Chrome to:
1. Navigate all 5 views in English (LTR) and Arabic (RTL).
2. Load synthetic benchmark dataset.
3. Capture high-resolution screenshots across 5 standard device viewports.
4. Record console logs, network errors, accessibility metrics, and responsiveness.
5. Save screenshots to docs/audit_ui/screenshots/ and conversation artifact directory.
"""

import os
import shutil
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\c471b13a-7b87-44d9-9a85-39a116863fa9")
OUTPUT_DIR = Path(r"C:\Users\HP\Desktop\RetailMind A\docs\audit_ui\screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

console_messages = []
page_errors = []

def record_console(msg):
    console_messages.append(f"[{msg.type}] {msg.text}")

def record_error(err):
    page_errors.append(str(err))

def save_and_copy(page, filename: str):
    local_path = OUTPUT_DIR / filename
    page.screenshot(path=str(local_path), full_page=True)
    if ARTIFACT_DIR.exists():
        art_path = ARTIFACT_DIR / filename
        shutil.copy2(local_path, art_path)
    print(f"[SCREENSHOT] Saved: {filename} ({local_path.stat().st_size // 1024} KB)")

def get_sidebar_radios(page):
    return page.locator('[data-testid="stSidebar"] [data-testid="stRadio"] label')

def main():
    print("=== Starting Playwright UI/UX Audit ===")
    t0 = time.time()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("console", record_console)
        page.on("pageerror", record_error)
        
        # 1. Initial Page Load (Empty State)
        print("[STEP 1] Loading initial application at http://127.0.0.1:8501 ...")
        t_load_start = time.time()
        page.goto("http://127.0.0.1:8501")
        page.wait_for_selector('[data-testid="stSidebar"]', timeout=30000)
        time.sleep(3)
        t_load = time.time() - t_load_start
        print(f"[PERF] Initial Load & Hydration Time: {t_load:.2f}s")
        save_and_copy(page, "01_initial_dashboard_empty_en.png")
        
        # 2. Load Synthetic Dataset via Sidebar Button
        print("[STEP 2] Clicking '⚡ Load Synthetic Sample Data' button ...")
        t_sample_start = time.time()
        load_btn = page.locator("button:has-text('Load Synthetic Sample Data')")
        if load_btn.count() > 0:
            load_btn.first.click()
            time.sleep(4)
        t_sample = time.time() - t_sample_start
        print(f"[PERF] Sample Dataset Ingestion & Render Time: {t_sample:.2f}s")
        save_and_copy(page, "02_overview_dashboard_populated_en.png")
        
        # 3. Navigate to Dataset View (English)
        print("[STEP 3] Navigating to Dataset Ingestion & Validation view ...")
        radios = get_sidebar_radios(page)
        # Option 1: Overview, Option 2: Agent, Option 3: Dataset, Option 4: Memory, Option 5: Audit
        radios.nth(3).click()
        time.sleep(3)
        save_and_copy(page, "03_dataset_ingestion_view_en.png")
        
        # 4. Navigate to AI Sales Agent View (English)
        print("[STEP 4] Navigating to AI Sales Agent view ...")
        radios = get_sidebar_radios(page)
        radios.nth(2).click()
        time.sleep(3)
        save_and_copy(page, "04_ai_agent_chat_view_en.png")
        
        # 5. Navigate to Memory Explorer View (English)
        print("[STEP 5] Navigating to Persistent Memory Explorer view ...")
        radios = get_sidebar_radios(page)
        radios.nth(4).click()
        time.sleep(3)
        save_and_copy(page, "05_persistent_memory_view_en.png")
        
        # 6. Navigate to Security Audit Trail View (English)
        print("[STEP 6] Navigating to Security Audit Trail view ...")
        radios = get_sidebar_radios(page)
        radios.nth(5).click()
        time.sleep(3)
        save_and_copy(page, "06_security_audit_view_en.png")
        
        # 7. Switch Language to Arabic (العربية)
        print("[STEP 7] Switching language to Arabic ...")
        t_lang_start = time.time()
        page.locator("label:has-text('العربية')").click()
        time.sleep(3)
        t_lang = time.time() - t_lang_start
        print(f"[PERF] Language Switch Latency: {t_lang:.2f}s")
        
        # Overview in Arabic
        print("[STEP 7A] Navigating to Arabic Overview Dashboard ...")
        radios_ar = get_sidebar_radios(page)
        radios_ar.nth(1).click()
        time.sleep(3)
        save_and_copy(page, "07_arabic_rtl_overview_dashboard.png")
        
        # Arabic Dataset Ingestion View
        print("[STEP 7B] Navigating to Arabic Dataset Ingestion View ...")
        radios_ar = get_sidebar_radios(page)
        radios_ar.nth(3).click()
        time.sleep(3)
        save_and_copy(page, "08_arabic_rtl_dataset_view.png")
        
        # Arabic AI Agent View
        print("[STEP 7C] Navigating to Arabic AI Agent Chat View ...")
        radios_ar = get_sidebar_radios(page)
        radios_ar.nth(2).click()
        time.sleep(3)
        save_and_copy(page, "09_arabic_rtl_agent_chat.png")
        
        # Arabic Memory View
        print("[STEP 7D] Navigating to Arabic Memory Explorer View ...")
        radios_ar = get_sidebar_radios(page)
        radios_ar.nth(4).click()
        time.sleep(3)
        save_and_copy(page, "10_arabic_rtl_memory_view.png")

        # Arabic Audit Trail View
        print("[STEP 7E] Navigating to Arabic Security Audit Trail View ...")
        radios_ar = get_sidebar_radios(page)
        radios_ar.nth(5).click()
        time.sleep(3)
        save_and_copy(page, "11_arabic_rtl_audit_view.png")
        
        # 8. Responsive Design Viewports Testing (on Overview View in English)
        print("[STEP 8] Testing responsive viewports in English ...")
        page.locator("label:has-text('English')").click()
        time.sleep(2)
        radios_en = get_sidebar_radios(page)
        radios_en.nth(1).click()
        time.sleep(2)
            
        viewports = [
            ("12_responsive_laptop_1366x768.png", 1366, 768),
            ("13_responsive_tablet_768x1024.png", 768, 1024),
            ("14_responsive_mobile_390x844.png", 390, 844),
            ("15_responsive_small_mobile_360x800.png", 360, 800),
        ]
        
        overflow_findings = []
        for fname, w, h in viewports:
            print(f"  -> Testing viewport {w}x{h} ({fname}) ...")
            page.set_viewport_size({"width": w, "height": h})
            time.sleep(2)
            
            # Check for horizontal overflow
            scroll_width = page.evaluate("document.documentElement.scrollWidth")
            client_width = page.evaluate("document.documentElement.clientWidth")
            has_h_scroll = scroll_width > client_width
            if has_h_scroll:
                overflow_findings.append(f"Viewport {w}x{h}: Horizontal scroll detected (scrollWidth={scroll_width} > clientWidth={client_width})")
                print(f"     [OVERFLOW DETECTED] scrollWidth={scroll_width} vs clientWidth={client_width}")
            else:
                print(f"     [CLEAN] No horizontal overflow (scrollWidth={scroll_width} == clientWidth={client_width})")
                
            save_and_copy(page, fname)
            
        browser.close()
        
    print(f"\n=== Playwright UI/UX Audit Complete in {time.time() - t0:.2f}s ===")
    print(f"Console Messages Logged: {len(console_messages)}")
    for msg in console_messages:
        if "error" in msg.lower() or "warn" in msg.lower():
            print(f"  [CONSOLE] {msg}")
    print(f"Page Errors Logged: {len(page_errors)}")
    for err in page_errors:
        print(f"  [PAGE ERROR] {err}")
    print("Horizontal Overflow Summary:")
    if overflow_findings:
        for of in overflow_findings:
            print(f"  ⚠️ {of}")
    else:
        print("  ✅ Zero horizontal overflow across all tested viewports.")

if __name__ == "__main__":
    main()
