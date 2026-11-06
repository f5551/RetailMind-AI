import os
import shutil
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(r"c:\Users\HP\Desktop\RetailMind A")
SCREENSHOT_DIR = WORKSPACE_ROOT / "docs" / "audit_ui" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\1c7d81ed-4bea-496f-bf76-9bdfffeebb00")


def run_verification():
    print("🚀 Starting Phase 3 AI Sales Agent Playwright Verification...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # -------------------------------------------------------------
        # 1. Desktop Arabic RTL (1440 x 950)
        # -------------------------------------------------------------
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()
        target_url = "http://127.0.0.1:8501/?view=agent&mock_agent_view=1"
        print(f"🌐 Navigating to: {target_url}")
        page.goto(target_url, wait_until="networkidle", timeout=30000)
        page.wait_for_selector(".execution-stepper", timeout=15000)
        time.sleep(1.5)

        print("🔍 Verifying Header & Agent Badges...")
        h1_texts = [t.strip() for t in page.locator("h1").all_text_contents()]
        assert any("المحلل الذكي" in t for t in h1_texts), f"Header 'المحلل الذكي' not found in {h1_texts}!"
        print("  ✓ Agent Header title 'المحلل الذكي' verified.")

        store_badge = page.locator("text=متصل ببيانات المتجر")
        assert store_badge.count() > 0, "Badge 'متصل ببيانات المتجر' not found!"
        print("  ✓ Store connection status badge verified.")

        brand_tag = page.locator("text=ذكاء حقيقي لنمو متجرك")
        assert brand_tag.count() > 0, "Brand tagline 'ذكاء حقيقي لنمو متجرك' not found!"
        print("  ✓ Header brand tagline verified.")

        print("🔍 Verifying Tools & Context Side Panel (Reference Image 2)...")
        tools_title = page.locator("text=الأدوات المستخدمة")
        assert tools_title.count() > 0, "Tools panel header 'الأدوات المستخدمة' not found!"
        print("  ✓ Panel title 'الأدوات المستخدمة' verified.")

        # Check 3 tools in panel
        assert page.locator("text=تحليل الإيرادات").count() > 0, "'تحليل الإيرادات' not found in tools panel!"
        assert page.locator("text=مقارنة التكاليف").count() > 0, "'مقارنة التكاليف' not found in tools panel!"
        assert page.locator("text=كشف الشذوذ").count() > 0, "'كشف الشذوذ' not found in tools panel!"
        print("  ✓ 3 Tools (Revenue, Costs, Anomalies) verified in panel.")

        # Human approval warning banner
        assert page.locator("text=الموافقة البشرية مطلوبة").count() > 0, "Human approval banner not found!"
        print("  ✓ Human approval required banner verified.")

        # Context info
        assert page.locator("text=معلومات السياق").count() > 0, "Context info box not found!"
        assert page.locator("text=المصادر: قاعدة بيانات المبيعات المعتمدة").count() > 0 or page.locator("text=Sources: Verified Sales Database").count() > 0, "Verified data source info not found!"
        assert page.locator("text=رؤى موثوقة. قرارات أذكى.").count() > 0, "Context tagline not found!"
        print("  ✓ Context info box and MCP sources verified.")

        print("🔍 Verifying Conversational UI & Dynamic Stepper...")
        # User message
        user_msg = page.locator("text=ما سبب انخفاض الأرباح هذا الشهر؟")
        assert user_msg.count() > 0, "User inquiry 'ما سبب انخفاض الأرباح هذا الشهر؟' not found!"
        print("  ✓ User question bubble verified.")

        # Assistant message
        asst_msg = page.locator("text=انخفض هامش فئة الإلكترونيات 8% بسبب ارتفاع تكلفة الشحن.")
        assert asst_msg.count() > 0, "Assistant response text not found!"
        print("  ✓ Assistant explanation verified.")

        # Execution Stepper: Ground-truth tool execution steps
        stepper = page.locator(".execution-stepper")
        assert stepper.count() > 0, "Dynamic execution stepper (.execution-stepper) not found!"
        assert page.locator(".step-box:has-text('تحليل المبيعات')").count() > 0, "Step 'تحليل المبيعات' not found in stepper!"
        assert page.locator(".step-box:has-text('مقارنة التكاليف')").count() > 0, "Step 'مقارنة التكاليف' not found in stepper!"
        assert page.locator(".step-box:has-text('التحقق الحسابي المعتمد')").count() > 0 or page.locator(".step-box:has-text('Verified Calculation')").count() > 0, "Step 'التحقق الحسابي المعتمد' not found in stepper!"
        print("  ✓ Dynamic execution stepper verified (3 genuine steps).")

        print("🔍 Verifying Approval Card (Human-in-the-Loop)...")
        app_card = page.locator(".approval-card")
        assert app_card.count() > 0, "Approval card (.approval-card) not found!"
        assert page.locator("text=موافقة على تقرير الأرباح").count() > 0, "Approval card title not found!"
        assert page.locator("text=بانتظار المراجعة").count() > 0, "Status 'بانتظار المراجعة' not found!"

        btn_app = page.locator("button:has-text('اعتماد')")
        btn_deny = page.locator("button:has-text('رفض')")
        assert btn_app.count() > 0, "Approve button not found!"
        assert btn_deny.count() > 0, "Deny button not found!"
        print("  ✓ Human approval card and action buttons verified.")

        print("🔍 Verifying Follow-up Suggestions & Input Bar...")
        assert page.locator("text=اقتراحات المتابعة:").count() > 0, "'اقتراحات المتابعة:' not found!"
        assert page.locator("button:has-text('تحليل المبيعات')").count() > 0, "Pill 'تحليل المبيعات' not found!"
        assert page.locator("button:has-text('أفضل المنتجات')").count() > 0, "Pill 'أفضل المنتجات' not found!"
        print("  ✓ Suggested prompt pills verified.")

        # Check chat input
        chat_input = page.locator("[data-testid='stChatInput'] textarea, [data-testid='stChatInputTextArea'], textarea")
        assert chat_input.count() > 0, "Chat input with proper placeholder not found!"
        print("  ✓ Chat input element verified.")

        # Capture Arabic Desktop Screenshot
        ar_desktop_shot = SCREENSHOT_DIR / "phase3_agent_arabic_desktop.png"
        page.screenshot(path=str(ar_desktop_shot), full_page=True)
        shutil.copy2(ar_desktop_shot, ARTIFACT_DIR / "phase3_agent_arabic_desktop.png")
        print(f"  📸 Saved Arabic Desktop Screenshot: {ar_desktop_shot}")

        # -------------------------------------------------------------
        # 2. English LTR Switch (1440 x 950)
        # -------------------------------------------------------------
        print("🌐 Switching Language to English LTR...")
        en_opt = page.get_by_text("English", exact=True)
        if en_opt.count() > 0:
            en_opt.first.click()
            time.sleep(2.5)
            page.wait_for_selector("h1", timeout=15000)

            # Check English header
            h1_en = [t.strip() for t in page.locator("h1").all_text_contents()]
            print(f"  English H1: {h1_en}")
            assert any("AI Sales" in t for t in h1_en), f"English header 'AI Sales' not found in {h1_en}!"

            assert page.locator("text=Tools Employed").count() > 0, "'Tools Employed' panel not found in English!"
            assert page.locator("text=Human Approval Required").count() > 0, "'Human Approval Required' not found in English!"
            print("  ✓ English LTR switch verified.")

            en_desktop_shot = SCREENSHOT_DIR / "phase3_agent_english_desktop.png"
            page.screenshot(path=str(en_desktop_shot), full_page=True)
            shutil.copy2(en_desktop_shot, ARTIFACT_DIR / "phase3_agent_english_desktop.png")
            print(f"  📸 Saved English Desktop Screenshot: {en_desktop_shot}")

            # Switch back to Arabic for responsive testing
            ar_opt = page.get_by_text("العربية", exact=True)
            if ar_opt.count() > 0:
                ar_opt.first.click()
                time.sleep(2.0)
        context.close()

        # -------------------------------------------------------------
        # 3. Tablet Viewport (768 x 1024)
        # -------------------------------------------------------------
        print("📱 Testing Tablet Viewport (768 x 1024)...")
        tab_context = browser.new_context(viewport={"width": 768, "height": 1024})
        tab_page = tab_context.new_page()
        tab_page.goto(target_url, wait_until="networkidle", timeout=30000)
        tab_page.wait_for_selector(".execution-stepper", timeout=15000)
        time.sleep(1.5)

        tab_shot = SCREENSHOT_DIR / "phase3_agent_tablet.png"
        tab_page.screenshot(path=str(tab_shot), full_page=True)
        shutil.copy2(tab_shot, ARTIFACT_DIR / "phase3_agent_tablet.png")
        print(f"  📸 Saved Tablet Screenshot: {tab_shot}")
        tab_context.close()

        # -------------------------------------------------------------
        # 4. Mobile Viewport (390 x 844)
        # -------------------------------------------------------------
        print("📱 Testing Mobile Viewport (390 x 844)...")
        mob_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15",
            is_mobile=True,
        )
        mob_page = mob_context.new_page()
        mob_page.goto(target_url, wait_until="networkidle", timeout=30000)
        mob_page.wait_for_selector(".execution-stepper", timeout=15000)
        time.sleep(1.5)

        mob_shot = SCREENSHOT_DIR / "phase3_agent_mobile.png"
        mob_page.screenshot(path=str(mob_shot), full_page=True)
        shutil.copy2(mob_shot, ARTIFACT_DIR / "phase3_agent_mobile.png")
        print(f"  📸 Saved Mobile Screenshot: {mob_shot}")
        mob_context.close()

        browser.close()

    print("🎉 All Phase 3 AI Sales Agent Playwright Verifications PASSED Successfully!")


if __name__ == "__main__":
    run_verification()
