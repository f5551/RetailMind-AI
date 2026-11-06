import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="msedge")
    page = b.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://127.0.0.1:8501/?lang=ar&view=audit", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # Fill visible password input
    vis_pw = page.locator("input[type='password']:visible").first
    print("Found visible password input:", vis_pw.is_visible())
    vis_pw.fill("WRONG_SECRET_999")
    
    # Target visible button
    vis_btns = page.locator("button:visible").all()
    print("Visible buttons count:", len(vis_btns))
    target_btn = None
    for btn in vis_btns:
        t = btn.inner_text()
        print("Visible button:", repr(t))
        if "فك قفل" in t or "تأكيد" in t or "دخول" in t:
            target_btn = btn
            break
            
    if target_btn:
        print("Clicking target button:", repr(target_btn.inner_text()))
        target_btn.click()
        page.wait_for_timeout(2500)
        post_c = page.content()
        has_err = "الرمز السري غير صحيح" in post_c or "غير صحيح" in post_c or "invalid" in post_c.lower()
        print("Error message displayed:", has_err)
    else:
        print("Target button not found among visible buttons!")
        
    b.close()
