import asyncio
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=True)
        page = await b.new_page()
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle")
        await asyncio.sleep(3)
        html = await page.content()
        print("Length of html:", len(html))
        print("Has متصل بالذكاء الاصطناعي:", "متصل بالذكاء الاصطناعي" in html)
        print("Has ر.س:", "ر.س" in html)
        print("Has Dollar sign:", "$" in html)
        print("Has العمليات التجارية:", "العمليات التجارية" in html)
        print("Has مرحباً بك:", "مرحباً بك" in html)
        print("Has أحمد:", "أحمد" in html)

        # Let's search where ر.س is if present
        if "ر.س" in html:
            idx = html.find("ر.س")
            print("Found ر.س around:", html[max(0, idx-50):min(len(html), idx+50)])
        await b.close()

if __name__ == "__main__":
    asyncio.run(check())
