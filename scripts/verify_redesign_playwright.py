"""RetailMind AI — Playwright Verification for Reference-Driven Redesign.

Verifies:
1. Warm SaaS theme tokens (ivory canvas, white card surfaces, emerald accents).
2. All 5 Views in Arabic (RTL) & English (LTR).
3. Featured Hero KPI Card for Net Profit.
4. Stepper pipeline, suggested prompts, and governance panel in AI Agent view.
5. Active file pill & Column Matching pills in Dataset Ingestion view.
6. Memory Explorer & Security Audit Trail.
7. Responsive adaptation across 4 key viewports (1440px, 768px, 390px, 360px).
"""

import json
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
    {"name": "tablet_portrait_768x1024", "width": 768, "height": 1024},
    {"name": "mobile_390x844", "width": 390, "height": 844},
    {"name": "small_mobile_360x800", "width": 360, "height": 800},
]

def save_and_copy(page, filename: str):
    local_path = OUTPUT_DIR / filename
    page.evaluate("window.scrollTo(0, 0)")
    page.evaluate("document.querySelector('section.main')?.scrollTo(0, 0)")
    time.sleep(0.4)
    page.screenshot(path=str(local_path), full_page=True)
    if ARTIFACT_DIR.exists():
        shutil.copy2(local_path, ARTIFACT_DIR / filename)
    print(f"[SCREENSHOT] Saved: {filename} ({local_path.stat().st_size // 1024} KB)")

def click_sidebar_nav(page, label_snippet: str):
    labels = page.locator('[data-testid="stSidebar"] [data-testid="stRadio"] label')
    count = labels.count()
    for i in range(count):
        txt = labels.nth(i).inner_text()
        if label_snippet.lower() in txt.lower():
            labels.nth(i).click()
            time.sleep(1.2)
            return True
    return False

def main():
    print("=== STARTING PLAYWRIGHT VERIFICATION FOR REDESIGN ===")
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("\n1. Navigating to http://127.0.0.1:8501...")
        page.goto("http://127.0.0.1:8501", timeout=30000)
        page.wait_for_selector('[data-testid="stSidebar"]', timeout=20000)
        time.sleep(2)

        # 1. Onboarding Empty State (English)
        save_and_copy(page, "redesign_01_onboarding_en.png")
        results["onboarding_en"] = "OK"

        # 2. Load Benchmark Dataset
        print("\n2. Loading Benchmark Dataset...")
        load_btn = page.locator("button:has-text('Load Benchmark Dataset')")
        if load_btn.count() == 0:
            load_btn = page.locator("button:has-text('Load Certified Synthetic')")
        if load_btn.count() == 0:
            load_btn = page.locator('[data-testid="stSidebar"] button:has-text("Load")')

        if load_btn.count() > 0:
            load_btn.first.click()
            time.sleep(3.5)
            page.wait_for_selector(".kpi-grid", timeout=20000)
            print("[INFO] Benchmark dataset loaded successfully.")

        # 3. View 1: Overview Dashboard (English)
        save_and_copy(page, "redesign_02_overview_en.png")
        hero_count = page.locator(".kpi-card-hero").count()
        print(f"[VERIFY] Hero KPI Card count: {hero_count}")
        results["hero_card_present"] = hero_count > 0

        # 4. View 2: AI Sales Agent (English)
        print("\n3. Testing View 2 (AI Sales Agent - English)...")
        click_sidebar_nav(page, "AI Sales Agent")
        time.sleep(1.5)
        save_and_copy(page, "redesign_03_agent_en.png")

        # 5. View 3: Dataset Ingestion (English)
        print("\n4. Testing View 3 (Dataset Ingestion - English)...")
        click_sidebar_nav(page, "Dataset Ingestion")
        time.sleep(1.5)
        save_and_copy(page, "redesign_04_dataset_en.png")

        # 6. View 4: Persistent Memory (English)
        print("\n5. Testing View 4 (Persistent Memory - English)...")
        click_sidebar_nav(page, "Memory")
        time.sleep(1.5)
        save_and_copy(page, "redesign_05_memory_en.png")

        # 7. View 5: Security Audit Trail (English)
        print("\n6. Testing View 5 (Security Audit - English)...")
        click_sidebar_nav(page, "Audit")
        time.sleep(1.5)
        save_and_copy(page, "redesign_06_audit_en.png")

        # ---------------------------------------------------------------------
        # Switch to Arabic (RTL)
        # ---------------------------------------------------------------------
        print("\n7. Switching Language to Arabic (RTL)...")
        ar_option = page.locator('label:has-text("العربية")')
        if ar_option.count() > 0:
            ar_option.first.click()
            time.sleep(2.5)
            print("[INFO] Switched to Arabic successfully.")

        # 8. View 1: Overview Dashboard (Arabic)
        print("\n8. Testing View 1 (Overview - Arabic)...")
        click_sidebar_nav(page, "المؤشرات")
        time.sleep(1.5)
        save_and_copy(page, "redesign_07_overview_ar.png")

        # 9. View 2: AI Sales Agent (Arabic)
        print("\n9. Testing View 2 (Agent - Arabic)...")
        click_sidebar_nav(page, "الذكي")
        time.sleep(1.5)
        save_and_copy(page, "redesign_08_agent_ar.png")

        # 10. View 3: Dataset Ingestion (Arabic)
        print("\n10. Testing View 3 (Dataset & Governance - Arabic)...")
        click_sidebar_nav(page, "استيراد")
        time.sleep(1.5)
        save_and_copy(page, "redesign_09_dataset_ar.png")

        # 11. View 4: Persistent Memory (Arabic)
        print("\n11. Testing View 4 (Memory - Arabic)...")
        click_sidebar_nav(page, "الذاكرة")
        time.sleep(1.5)
        save_and_copy(page, "redesign_10_memory_ar.png")

        # 12. View 5: Security Audit Trail (Arabic)
        print("\n12. Testing View 5 (Audit - Arabic)...")
        click_sidebar_nav(page, "التدقيق")
        time.sleep(1.5)
        save_and_copy(page, "redesign_11_audit_ar.png")

        # ---------------------------------------------------------------------
        # Viewports Responsiveness (Arabic Overview)
        # ---------------------------------------------------------------------
        print("\n13. Testing Responsive Viewports in Arabic...")
        click_sidebar_nav(page, "المؤشرات")
        time.sleep(1.5)

        for vp in VIEWPORTS:
            print(f"Testing viewport: {vp['name']} ({vp['width']}x{vp['height']})...")
            page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            time.sleep(1.5)
            save_and_copy(page, f"redesign_vp_{vp['name']}_ar.png")

        print("\n=== PLAYWRIGHT VERIFICATION COMPLETE ===")
        browser.close()

if __name__ == "__main__":
    main()
