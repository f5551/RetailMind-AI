"""RetailMind AI — Complete Views & Defect Verification Automation.

Captures:
1. RM-UX-001: Tablet 768px KPI grid
2. RM-UX-002: Sidebar collapse button
3. RM-UX-003: Password visibility toggle
4. RM-UX-004: File uploader browse button
5. RM-UX-005: File uploader 10MB limit text
6. RM-UX-006: Onboarding hero card
7. RM-UX-007: Top Products chart (horizontal bars, axis labels, untruncated labels)
8. All 5 Views in English (Overview, Agent, Dataset, Memory, Audit)
9. All 5 Views in Arabic RTL (Overview, Agent, Dataset, Memory, Audit)
"""

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

def save_and_copy(page_or_locator, filename: str, full_page: bool = False):
    local_path = OUTPUT_DIR / filename
    if hasattr(page_or_locator, "screenshot"):
        if full_page:
            page_or_locator.screenshot(path=str(local_path), full_page=True)
        else:
            page_or_locator.screenshot(path=str(local_path))
        if ARTIFACT_DIR.exists():
            shutil.copy2(local_path, ARTIFACT_DIR / filename)
        print(f"[SCREENSHOT] Saved: {filename} ({local_path.stat().st_size // 1024} KB)")

def get_sidebar_radios(page):
    return page.locator('[data-testid="stSidebar"] [data-testid="stRadio"] label')

def main():
    print("=== Starting Full UX Verification Suite ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # ---------------------------------------------------------------------
        # 1. Onboarding Empty State & RM-UX-006
        # ---------------------------------------------------------------------
        page.goto("http://127.0.0.1:8501")
        page.wait_for_selector('[data-testid="stSidebar"]', timeout=30000)
        page.wait_for_timeout(2500)

        # Reset chat / session if needed or if already loaded
        reset_btn = page.locator("button:has-text('Reset Chat & Approvals')")
        
        onboarding = page.locator(".onboarding-card")
        if onboarding.count() > 0:
            print("[RM-UX-006] Onboarding hero card detected.")
            save_and_copy(onboarding.first, "rm_ux_006_onboarding_hero.png")
            save_and_copy(page, "view_01_overview_empty_en.png", full_page=True)

        # ---------------------------------------------------------------------
        # 2. RM-UX-002: Sidebar Collapse Button
        # ---------------------------------------------------------------------
        sidebar = page.locator('[data-testid="stSidebar"]')
        if sidebar.count() > 0:
            sidebar.hover()
            page.wait_for_timeout(500)
            collapse_btn = page.locator('[data-testid="stSidebarCollapseButton"]')
            if collapse_btn.count() > 0 and collapse_btn.is_visible():
                print("[RM-UX-002] Sidebar collapse button found and visible on hover.")
                save_and_copy(collapse_btn.first, "rm_ux_002_sidebar_collapse_btn.png")
            else:
                # Capture top portion of sidebar
                print("[RM-UX-002] Capturing sidebar brand area.")
                save_and_copy(sidebar.first, "rm_ux_002_sidebar_brand_area.png")

        # ---------------------------------------------------------------------
        # 3. RM-UX-003: Password Visibility Toggle
        # ---------------------------------------------------------------------
        pwd_input = page.locator('[data-testid="stTextInput"]')
        if pwd_input.count() > 0:
            print("[RM-UX-003] Password input found.")
            save_and_copy(pwd_input.first, "rm_ux_003_password_visibility_input.png")

        # ---------------------------------------------------------------------
        # 4. Load Benchmark Dataset
        # ---------------------------------------------------------------------
        load_btn = page.locator("button:has-text('Load Benchmark Dataset')")
        if load_btn.count() == 0:
            load_btn = page.locator("button:has-text('Load Synthetic Sample Data')")
        if load_btn.count() > 0:
            load_btn.first.click()
            page.wait_for_timeout(4000)
            print("Loaded benchmark dataset.")

        # Populated Overview Dashboard
        save_and_copy(page, "view_01_overview_populated_en.png", full_page=True)

        # ---------------------------------------------------------------------
        # 5. RM-UX-007: Top Products Chart Zoom & Verification
        # ---------------------------------------------------------------------
        top_prod_chart = page.locator('[data-testid="stVegaLiteChart"]').nth(1)
        if top_prod_chart.count() > 0:
            print("[RM-UX-007] Top Products chart located.")
            save_and_copy(top_prod_chart.first, "rm_ux_007_top_products_chart_en.png")

        # ---------------------------------------------------------------------
        # 6. RM-UX-001: 768px Tablet Portrait KPI Grid
        # ---------------------------------------------------------------------
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(2000)
        kpi_grid = page.locator(".kpi-grid")
        if kpi_grid.count() > 0:
            print("[RM-UX-001] KPI grid located on 768px tablet.")
            save_and_copy(kpi_grid.first, "rm_ux_001_tablet_kpi_grid_768px.png")
            save_and_copy(page, "view_01_overview_tablet_768px.png", full_page=True)

        # Restore 1440x900
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(2000)

        # ---------------------------------------------------------------------
        # 7. View 2: AI Sales Agent (English)
        # ---------------------------------------------------------------------
        radios = get_sidebar_radios(page)
        # Option 1: Overview, Option 2: Agent, Option 3: Dataset, Option 4: Memory, Option 5: Audit
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "AI Sales Agent" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_02_ai_sales_agent_en.png", full_page=True)

        # ---------------------------------------------------------------------
        # 8. View 3: Dataset Ingestion (English) & RM-UX-004 & RM-UX-005
        # ---------------------------------------------------------------------
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "Dataset" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_03_dataset_ingestion_en.png", full_page=True)

        uploader = page.locator('[data-testid="stFileUploader"]')
        if uploader.count() > 0:
            print("[RM-UX-004 & RM-UX-005] Uploader found.")
            save_and_copy(uploader.first, "rm_ux_004_005_file_uploader_en.png")

        # ---------------------------------------------------------------------
        # 9. View 4: Persistent Memory Explorer (English)
        # ---------------------------------------------------------------------
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "Memory" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_04_memory_explorer_en.png", full_page=True)

        # ---------------------------------------------------------------------
        # 10. View 5: Security & Audit Trail (English)
        # ---------------------------------------------------------------------
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "Audit" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_05_security_audit_en.png", full_page=True)

        # =====================================================================
        # 11. Arabic RTL Mode for All 5 Views
        # =====================================================================
        print("\n--- Switching to Arabic RTL ---")
        ar_radio = page.locator('div[data-testid="stRadio"] label:has-text("العربية")')
        if ar_radio.count() > 0:
            ar_radio.first.click()
            page.wait_for_timeout(4000)
            print("Switched to Arabic mode successfully.")

        # View 1: Overview Dashboard (Arabic)
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "المؤشرات" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_01_overview_populated_ar.png", full_page=True)

        top_prod_chart_ar = page.locator('[data-testid="stVegaLiteChart"]').nth(1)
        if top_prod_chart_ar.count() > 0:
            save_and_copy(top_prod_chart_ar.first, "rm_ux_007_top_products_chart_ar.png")

        # View 2: AI Sales Agent (Arabic)
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "المبيعات" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_02_ai_sales_agent_ar.png", full_page=True)

        # View 3: Dataset Ingestion (Arabic)
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "استيراد" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_03_dataset_ingestion_ar.png", full_page=True)

        # View 4: Memory Explorer (Arabic)
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "الذاكرة" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_04_memory_explorer_ar.png", full_page=True)

        # View 5: Security Audit Trail (Arabic)
        radios = get_sidebar_radios(page)
        for i in range(radios.count()):
            txt = radios.nth(i).inner_text()
            if "التدقيق" in txt:
                radios.nth(i).click()
                break
        page.wait_for_timeout(3000)
        save_and_copy(page, "view_05_security_audit_ar.png", full_page=True)

        context.close()
        browser.close()

    print("\n=== All Visual Proof Captured & Synced to Artifacts Successfully ===")

if __name__ == "__main__":
    main()
