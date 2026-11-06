import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501")
    page.wait_for_timeout(3000)

    # Screenshot password input area in sidebar
    pwd = page.locator('[data-testid="stTextInput"]')
    if pwd.count() > 0:
        pwd.screenshot(path="docs/audit_ui/screenshots/test_pwd_icon.png")
        print("Captured test_pwd_icon.png")

    # Navigate to dataset view
    radios = page.locator('[data-testid="stSidebar"] [data-testid="stRadio"] label')
    radios.nth(3).click()
    page.wait_for_timeout(2000)

    # Screenshot uploader browse button
    uploader = page.locator('[data-testid="stFileUploader"]')
    if uploader.count() > 0:
        uploader.screenshot(path="docs/audit_ui/screenshots/test_uploader_icon.png")
        print("Captured test_uploader_icon.png")

    b.close()
