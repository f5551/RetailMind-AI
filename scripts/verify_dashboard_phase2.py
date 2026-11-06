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
    print("🚀 Starting Phase 2 Dashboard Playwright Visual & Functional Verification...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        # -------------------------------------------------------------
        # 1. Desktop Arabic RTL (1440 x 950)
        # -------------------------------------------------------------
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()
        page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        time.sleep(2.5)
        
        # If dataset is not loaded yet, load sample dataset
        sample_btn = page.get_by_role("button", name="تحميل البيانات المرجعية")
        if sample_btn.count() > 0 and sample_btn.first.is_visible():
            print("📥 Clicking sample data loading button...")
            sample_btn.first.click()
            time.sleep(3.5)
            page.wait_for_load_state("networkidle")
        
        time.sleep(1.5)
        
        print("🔍 Verifying Header & Badges...")
        # Header title
        h1_texts = [t.strip() for t in page.locator("h1").all_text_contents()]
        assert any("نظرة عامة على الأداء" in t for t in h1_texts), f"Header title 'نظرة عامة على الأداء' not found in {h1_texts}!"
        print("  ✓ Header title found.")
        
        # Active dataset badge
        badge_count = page.locator("text=synthetic_sales.csv").count()
        assert badge_count > 0, "Active dataset badge 'synthetic_sales.csv' not found!"
        print("  ✓ Active dataset badge found.")
        
        # Date span
        date_span_count = page.locator("text=5 يناير - 28 فبراير 2026").count()
        assert date_span_count > 0, "Real date span '5 يناير - 28 فبراير 2026' not found!"
        print("  ✓ Real date span found.")
        
        # Live update
        live_update_count = page.locator("text=آخر تحديث: اليوم").count()
        assert live_update_count > 0, "Live update label not found!"
        print("  ✓ Live update label found.")
        
        print("🔍 Verifying 4 KPI Cards & Ground-Truth Calculations...")
        # 4 KPI cards in .kpi-grid
        kpi_cards = page.locator(".kpi-grid .kpi-card, .kpi-grid .kpi-card-hero")
        assert kpi_cards.count() == 4, f"Expected 4 KPI cards, got {kpi_cards.count()}!"
        print("  ✓ 4 KPI cards found.")
        
        kpi_values = [t.strip() for t in page.locator(".kpi-value").all_text_contents()]
        kpi_footers = [t.strip() for t in page.locator(".kpi-footer").all_text_contents()]
        print(f"  Values: {kpi_values}")
        print(f"  Footers: {kpi_footers}")
        
        # Card 1: Margin
        assert "51.8%" in kpi_values, "Margin value '51.8%' not found!"
        assert any("+1.7%" in f for f in kpi_footers), "Margin delta '+1.7%' not found!"
        print("  ✓ Card 1 (Margin: 51.8%, delta: +1.7%) verified.")
        
        # Card 2: Net Revenue
        assert "$2,945.00" in kpi_values, "Revenue value '$2,945.00' not found!"
        assert any("+17.3%" in f for f in kpi_footers), "Revenue delta '+17.3%' not found!"
        print("  ✓ Card 2 (Revenue: $2,945.00, delta: +17.3%) verified.")
        
        # Card 3: Hero Net Profit Card
        hero_card = page.locator(".kpi-card-hero")
        assert hero_card.count() == 1, "Hero KPI Card (.kpi-card-hero) not found!"
        assert "$1,525.50" in kpi_values, "Hero profit value '$1,525.50' not found!"
        assert any("+21.2%" in f for f in kpi_footers), "Hero profit delta '+21.2%' not found!"
        print("  ✓ Card 3 (Hero Net Profit: $1,525.50, delta: +21.2%) verified.")
        
        # Card 4: Orders
        assert "15" in kpi_values, "Orders value '15' not found!"
        assert any("+23.1%" in f for f in kpi_footers), "Orders/units delta '+23.1%' not found!"
        print("  ✓ Card 4 (Orders: 15, delta: +23.1%) verified.")
        
        print("🔍 Verifying Analytics Charts & Action Menu Masking...")
        cat_title = page.locator(".analytics-card-title:has-text('أداء الفئات')")
        assert cat_title.count() > 0, "Category performance chart title not found!"
        trend_title = page.locator(".analytics-card-title:has-text('اتجاه الإيرادات')")
        assert trend_title.count() > 0, "Revenue trend chart title not found!"
        
        # Check VegaLite action buttons are hidden
        summary_menus = page.locator("[data-testid='stVegaLiteChart'] summary, [data-testid='stArrowVegaLiteChart'] summary")
        for i in range(summary_menus.count()):
            assert not summary_menus.nth(i).is_visible(), "VegaLite action menu should be hidden!"
        print("  ✓ Both charts rendered and VegaLite technical menus hidden.")
        
        print("🔍 Verifying Top Products Table...")
        top_prod_card = page.locator(".top-products-card")
        assert top_prod_card.count() > 0, "Top products card not found!"
        th_elements = top_prod_card.locator("th")
        assert th_elements.count() == 5, f"Expected 5 table headers, got {th_elements.count()}!"
        rows = top_prod_card.locator("tbody tr")
        assert rows.count() == 5, f"Expected 5 top products rows, got {rows.count()}!"
        print("  ✓ Top Products table has 5 verified rows.")
        
        # Capture Arabic Desktop Screenshot
        ar_shot_path = SCREENSHOT_DIR / "phase2_dashboard_arabic_desktop.png"
        page.screenshot(path=str(ar_shot_path), full_page=True)
        shutil.copy(ar_shot_path, ARTIFACT_DIR / "phase2_dashboard_arabic_desktop.png")
        print(f"  📸 Saved Arabic desktop screenshot: {ar_shot_path}")
        
        # -------------------------------------------------------------
        # 2. English LTR Desktop (1440 x 950)
        # -------------------------------------------------------------
        print("🌐 Switching to English...")
        en_opt = page.get_by_text("English", exact=True)
        if en_opt.count() > 0:
            en_opt.first.click()
            time.sleep(2.5)
            page.wait_for_load_state("networkidle")
        
        en_h1s = [t.strip() for t in page.locator("h1").all_text_contents()]
        assert any("Performance Overview" in t for t in en_h1s), f"English header 'Performance Overview' not found in {en_h1s}!"
        print("  ✓ English title found.")
        
        en_profit_title = page.locator(".kpi-card-hero .kpi-title:has-text('Net Profit')")
        assert en_profit_title.count() > 0, "English Hero 'Net Profit' not found!"
        print("  ✓ English Hero Net Profit found.")
        
        en_shot_path = SCREENSHOT_DIR / "phase2_dashboard_english_desktop.png"
        page.screenshot(path=str(en_shot_path), full_page=True)
        shutil.copy(en_shot_path, ARTIFACT_DIR / "phase2_dashboard_english_desktop.png")
        print(f"  📸 Saved English desktop screenshot: {en_shot_path}")
        
        # Switch back to Arabic
        ar_opt = page.get_by_text("العربية", exact=True)
        if ar_opt.count() > 0:
            ar_opt.first.click()
            time.sleep(2)
            page.wait_for_load_state("networkidle")
        
        context.close()
        
        # -------------------------------------------------------------
        # 3. Tablet Viewport (768 x 1024)
        # -------------------------------------------------------------
        print("📱 Testing Tablet Viewport (768x1024)...")
        tab_context = browser.new_context(viewport={"width": 768, "height": 1024})
        tab_page = tab_context.new_page()
        tab_page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        time.sleep(2)
        tab_shot_path = SCREENSHOT_DIR / "phase2_dashboard_tablet.png"
        tab_page.screenshot(path=str(tab_shot_path), full_page=True)
        shutil.copy(tab_shot_path, ARTIFACT_DIR / "phase2_dashboard_tablet.png")
        print(f"  📸 Saved Tablet screenshot: {tab_shot_path}")
        tab_context.close()
        
        # -------------------------------------------------------------
        # 4. Mobile Viewport (390 x 844)
        # -------------------------------------------------------------
        print("📱 Testing Mobile Viewport (390x844)...")
        mob_context = browser.new_context(viewport={"width": 390, "height": 844})
        mob_page = mob_context.new_page()
        mob_page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        time.sleep(2)
        mob_shot_path = SCREENSHOT_DIR / "phase2_dashboard_mobile.png"
        mob_page.screenshot(path=str(mob_shot_path), full_page=True)
        shutil.copy(mob_shot_path, ARTIFACT_DIR / "phase2_dashboard_mobile.png")
        print(f"  📸 Saved Mobile screenshot: {mob_shot_path}")
        mob_context.close()
        
        browser.close()
        
    print("🎉 All Phase 2 Dashboard Playwright Tests PASSED flawlessly!")
    return True

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
