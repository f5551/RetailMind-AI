import sys
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(r"c:\Users\HP\Desktop\RetailMind A")
SCREENSHOT_DIR = WORKSPACE_ROOT / "docs" / "audit_ui" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\1c7d81ed-4bea-496f-bf76-9bdfffeebb00")

def run_verification():
    print("🚀 Starting Phase 4 Data, Governance & Sidebar Playwright Verification...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # -------------------------------------------------------------
        # 1. Desktop Arabic RTL (1440 x 950)
        # -------------------------------------------------------------
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()
        page.goto("http://127.0.0.1:8501/?view=overview", timeout=30000)
        page.wait_for_selector("h1", timeout=15000)
        time.sleep(1.5)

        # Ensure sample dataset loaded
        sample_btn = page.get_by_role("button", name="تحميل البيانات المرجعية")
        if sample_btn.count() > 0 and sample_btn.first.is_visible():
            print("📥 Clicking sample data loading button...")
            sample_btn.first.click()
            time.sleep(3.0)
            page.wait_for_load_state("networkidle")

        # -------------------------------------------------------------
        # P1 VERIFICATION: Sidebar Collapse & Expand in Arabic RTL
        # -------------------------------------------------------------
        print("🔍 Testing Sidebar Collapse & Reopen Cycle (Arabic RTL)...")
        sb = page.locator('section[data-testid="stSidebar"]')
        assert sb.is_visible(), "Sidebar should be initially visible!"

        collapse_btn = page.locator('[data-testid="stSidebarCollapseButton"] button')
        collapse_btn.click()
        page.wait_for_timeout(1000)
        assert not sb.is_visible(), "Sidebar should be collapsed!"
        print("  ✓ Sidebar collapsed successfully.")

        expand_btn = page.locator('[data-testid="stExpandSidebarButton"]')
        assert expand_btn.is_visible(), "Sidebar expand button must remain visible after collapsing!"
        box = expand_btn.bounding_box()
        print(f"  ✓ Expand button visible at x={box['x']:.0f}, y={box['y']:.0f} (RTL expected right side: >1000px)")
        assert box['x'] > 1000, f"Expand button in RTL should be on the right, got x={box['x']}"

        expand_btn.click()
        page.wait_for_timeout(1000)
        assert sb.is_visible(), "Sidebar should be reopened!"
        print("  ✓ Sidebar reopened successfully.")

        # -------------------------------------------------------------
        # NAVIGATION: Navigate to View 3: Data & Governance (البيانات والحوكمة)
        # -------------------------------------------------------------
        print("🔍 Navigating to View 3: Data & Governance (البيانات والحوكمة)...")
        page.goto("http://127.0.0.1:8501/?view=dataset&load_sample=1", timeout=30000)
        page.wait_for_selector("h1", timeout=15000)
        page.wait_for_timeout(2000)

        # -------------------------------------------------------------
        # VERIFY VIEW 3 ELEMENTS (Reference Image 1 Fidelity)
        # -------------------------------------------------------------
        print("🔍 Verifying Header Bar & User Greeting...")
        # Check title and greeting
        h1_texts = [t.strip() for t in page.locator("h1").all_text_contents()]
        assert any("البيانات والحوكمة" in t for t in h1_texts), f"Expected 'البيانات والحوكمة' in h1: {h1_texts}"
        print("  ✓ Header title 'البيانات والحوكمة' verified.")

        greeting_count = page.locator("text=مرحباً بك").count()
        assert greeting_count > 0, "User greeting 'مرحباً بك' not found!"
        print("  ✓ User greeting 'مرحباً بك' found.")

        sub_greeting = page.locator("text=مستقبل التجزئة يبدأ بالبيانات").count()
        assert sub_greeting > 0, "Subtitle 'مستقبل التجزئة يبدأ بالبيانات' found."
        print("  ✓ Subtitle found.")

        print("🔍 Verifying Card 1: استيراد بيانات المبيعات & Column Matching...")
        upload_box_title = page.locator("text=استيراد بيانات المبيعات").count()
        assert upload_box_title > 0, "'استيراد بيانات المبيعات' title found!"

        verified_badge = page.locator("text=تم التحقق").count()
        assert verified_badge > 0, "'تم التحقق' badge found in active file box!"
        print("  ✓ Active file status 'تم التحقق' verified.")

        col_matching_title = page.locator("text=مطابقة الأعمدة").count()
        assert col_matching_title > 0, "'مطابقة الأعمدة' section found!"

        # Check 5 column pills
        for col_name in ["التاريخ", "المنتج", "الإيراد", "التكلفة", "الكمية"]:
            count = page.locator(f"text={col_name}").count()
            assert count > 0, f"Column pill '{col_name}' not found!"
        print("  ✓ All 5 column matching pills verified.")

        print("🔍 Verifying Card 2: حوكمة واعتماد التقارير (Governance Card)...")
        rep_approval_title = page.locator("text=إدارة تقارير الأرباح والموافقات").count() or page.locator("text=موافقة على تقرير الأرباح").count()
        assert rep_approval_title > 0, "Governance card title found!"
        print("  ✓ Governance report card verified.")

        print("🔍 Verifying Card 3: سجل التدقيق (Audit Trail Table)...")
        audit_title = page.locator("text=سجل التدقيق").count()
        assert audit_title > 0, "'سجل التدقيق' table header found!"

        # Verify table column headers (Time, Event, Details, User)
        assert page.locator("th:has-text('الوقت')").count() > 0, "Audit table header 'الوقت' found!"
        assert page.locator("th:has-text('الحدث')").count() > 0, "Audit table header 'الحدث' found!"
        assert page.locator("th:has-text('التفاصيل')").count() > 0, "Audit table header 'التفاصيل' found!"
        assert page.locator("th:has-text('المستخدم')").count() > 0, "Audit table header 'المستخدم' found!"
        print("  ✓ Audit table columns (الوقت, الحدث, التفاصيل, المستخدم) verified.")

        # Check user name or authentic empty state in table rows
        user_rows = page.locator("td:has-text('التاجر المعتمد')").count() or page.locator("td:has-text('لم يتم تسجيل')").count()
        assert user_rows > 0, "Authentic audit rows or empty state found!"
        print(f"  ✓ Authentic audit state verified.")

        # Capture Arabic Desktop Screenshot
        ar_desktop_path = SCREENSHOT_DIR / "phase4_dataset_arabic_desktop.png"
        page.screenshot(path=str(ar_desktop_path), full_page=True)
        print(f"📸 Saved Arabic Desktop Screenshot: {ar_desktop_path}")

        # -------------------------------------------------------------
        # 2. English LTR Desktop (1440 x 950)
        # -------------------------------------------------------------
        print("🔍 Testing English LTR Switch & Rendering...")
        # Toggle language to English
        en_opt = page.get_by_text("English", exact=True)
        if en_opt.count() > 0 and en_opt.first.is_visible():
            en_opt.first.click()
            page.wait_for_timeout(2000)

        en_h1_texts = [t.strip() for t in page.locator("h1").all_text_contents()]
        print(f"  English H1 texts: {en_h1_texts}")
        assert any("Data & Governance" in t for t in en_h1_texts), "English H1 'Data & Governance' not found!"

        # Verify Sidebar Expand button in LTR is on the left
        collapse_btn_en = page.locator('[data-testid="stSidebarCollapseButton"] button')
        collapse_btn_en.click()
        page.wait_for_timeout(1000)
        assert not sb.is_visible(), "Sidebar should be collapsed in English!"
        expand_btn_en = page.locator('[data-testid="stExpandSidebarButton"]')
        assert expand_btn_en.is_visible(), "Expand button in English LTR should be visible!"
        box_en = expand_btn_en.bounding_box()
        print(f"  ✓ LTR expand button at x={box_en['x']:.0f}, y={box_en['y']:.0f} (Expected left side: <100px)")
        assert box_en['x'] < 100, f"Expand button in English LTR should be on the left (x < 100), got {box_en['x']}"
        expand_btn_en.click()
        page.wait_for_timeout(1000)
        assert sb.is_visible(), "Sidebar should be reopened in English!"

        en_desktop_path = SCREENSHOT_DIR / "phase4_dataset_english_desktop.png"
        page.screenshot(path=str(en_desktop_path), full_page=True)
        print(f"📸 Saved English Desktop Screenshot: {en_desktop_path}")

        # Switch back to Arabic
        ar_opt = page.get_by_text("العربية", exact=True)
        if ar_opt.count() > 0 and ar_opt.first.is_visible():
            ar_opt.first.click()
            page.wait_for_timeout(2000)
        ar_btn = page.locator('button:has-text("العربية"), button:has-text("AR")').first
        if ar_btn.is_visible():
            ar_btn.click()
            time.sleep(2.5)
            page.wait_for_load_state("networkidle")

        # -------------------------------------------------------------
        # 3. Tablet Viewport (768 x 1024)
        # -------------------------------------------------------------
        print("🔍 Capturing Tablet Viewport (768 x 1024)...")
        context_tablet = browser.new_context(viewport={"width": 768, "height": 1024})
        page_tablet = context_tablet.new_page()
        page_tablet.goto("http://127.0.0.1:8501/?view=dataset&load_sample=1", timeout=30000)
        page_tablet.wait_for_selector("h1", timeout=15000)
        page_tablet.wait_for_timeout(2000)
        tablet_path = SCREENSHOT_DIR / "phase4_dataset_tablet.png"
        page_tablet.screenshot(path=str(tablet_path), full_page=True)
        print(f"📸 Saved Tablet Screenshot: {tablet_path}")

        # -------------------------------------------------------------
        # 4. Mobile Viewport (390 x 844)
        # -------------------------------------------------------------
        print("🔍 Capturing Mobile Viewport (390 x 844)...")
        context_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        page_mobile = context_mobile.new_page()
        page_mobile.goto("http://127.0.0.1:8501/?view=dataset&load_sample=1", timeout=30000)
        page_mobile.wait_for_selector("h1", timeout=15000)
        page_mobile.wait_for_timeout(2000)
        mobile_path = SCREENSHOT_DIR / "phase4_dataset_mobile.png"
        page_mobile.screenshot(path=str(mobile_path), full_page=True)
        print(f"📸 Saved Mobile Screenshot: {mobile_path}")

        # -------------------------------------------------------------
        # 5. Verify View 4 (Memory) & View 5 (Audit) Navigation
        # -------------------------------------------------------------
        print("🔍 Verifying Navigation to View 4 (Memory Explorer) & View 5 (Security Audit)...")
        context_views = browser.new_context(viewport={"width": 1440, "height": 950})
        page_v = context_views.new_page()

        # View 4
        page_v.goto("http://127.0.0.1:8501/?view=memory", timeout=30000)
        page_v.wait_for_selector("h1", timeout=15000)
        page_v.wait_for_timeout(1000)
        mem_h1 = [t.strip() for t in page_v.locator("h1").all_text_contents()]
        print(f"  View 4 H1: {mem_h1}")
        assert any("الذاكرة" in t for t in mem_h1), "Memory title not found!"
        print("  ✓ View 4 (Memory Explorer) verified.")

        # View 5
        page_v.goto("http://127.0.0.1:8501/?view=audit", timeout=30000)
        page_v.wait_for_selector("h1", timeout=15000)
        page_v.wait_for_timeout(1000)
        audit_h1 = [t.strip() for t in page_v.locator("h1").all_text_contents()]
        print(f"  View 5 H1: {audit_h1}")
        assert any("التدقيق" in t for t in audit_h1), "Audit title not found!"
        print("  ✓ View 5 (Security Audit Trail) verified.")

        # Copy all screenshots to artifact directory
        for s in [ar_desktop_path, en_desktop_path, tablet_path, mobile_path]:
            if s.exists():
                dst = ARTIFACT_DIR / s.name
                shutil.copy2(s, dst)
                print(f"📋 Copied {s.name} to artifacts directory: {dst}")

        print("🎉 ALL PHASE 4 PLAYWRIGHT VERIFICATION CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_verification()
