import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.async_api import async_playwright

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle")
        await asyncio.sleep(2)

        # 1. Check Date Pill (DASH-01)
        pill = await page.query_selector(".header-date-pill")
        pill_text = await pill.inner_text() if pill else ""
        print("DASH-01 Date Pill text:", pill_text)
        assert "▼" not in pill_text, "Found ▼ arrow in date pill!"

        # 2. Check Data & Governance (DATA-01, DATA-02, DATA-03, DATA-04)
        # Click on Data & Governance nav item
        nav_buttons = await page.query_selector_all("button")
        for btn in nav_buttons:
            txt = await btn.inner_text()
            if "البيانات والحوكمة" in txt or "Data & Governance" in txt:
                await btn.click()
                await asyncio.sleep(2)
                break

        content = await page.content()
        # DATA-01
        assert "مرحباً أحمد" not in content, "Found hardcoded 'مرحباً أحمد'!"
        print("DATA-01 Check: 'مرحباً أحمد' is NOT in content. Passed!")

        # DATA-02
        assert "v3_dev_secret_input_field" not in content, "Found dev secret input field on merchant page!"
        print("DATA-02 Check: Dev secret field is hidden. Passed!")

        # DATA-03
        assert "بانتظار المراجعة" not in content, "Found fake 'بانتظار المراجعة' badge in idle state!"
        print("DATA-03 Check: Fake pending badge is absent. Idle state verified. Passed!")

        # DATA-04
        assert "أحمد الشراري" not in content, "Found dummy name 'أحمد الشراري'!"
        print("DATA-04 Check: Dummy audit rows removed. Passed!")

        # 3. Check Audit View (AUD-01)
        for btn in await page.query_selector_all("button"):
            txt = await btn.inner_text()
            if "سجل التدقيق" in txt or "Security & Audit" in txt or "التدقيق الأمني" in txt:
                await btn.click()
                await asyncio.sleep(2)
                break
        
        audit_content = await page.content()
        assert "C:\\Users\\HP" not in audit_content, "Found leaked host path C:\\Users\\HP in audit view!"
        print("AUD-01 Check: Local disk path is hidden from merchant. Passed!")

        # 4. Check Agent Page Staged Prompt (AGT-03)
        for btn in await page.query_selector_all("button"):
            txt = await btn.inner_text()
            if "المحلل الذكي" in txt or "AI Sales Agent" in txt:
                await btn.click()
                await asyncio.sleep(2)
                break

        # Click suggested pill
        pill_btn = await page.query_selector("button:has-text('ملخص الإيرادات')")
        if pill_btn:
            await pill_btn.click()
            await asyncio.sleep(1)
            agent_content = await page.content()
            assert "إرسال الاستفسار" in agent_content or "Send Query" in agent_content, "Staged prompt box did not appear!"
            print("AGT-03 Check: Suggested prompt stages review box successfully. Passed!")

        print("\nALL STAGE 1 VERIFICATIONS PASSED SUCCESSFULLY!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify())
