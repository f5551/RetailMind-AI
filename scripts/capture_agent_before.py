import sys
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
SCREENSHOT_DIR = Path("docs/audit_ui/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\1c7d81ed-4bea-496f-bf76-9bdfffeebb00")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501", wait_until="networkidle")
    time.sleep(2)

    # Click navigation item 'المحلل الذكي'
    agent_nav = page.locator("section[data-testid='stSidebar'] label:has-text('المحلل الذكي')")
    if agent_nav.count() > 0:
        agent_nav.first.click()
        time.sleep(2.5)
        page.wait_for_load_state("networkidle")

    shot_path = SCREENSHOT_DIR / "phase3_agent_before.png"
    page.screenshot(path=str(shot_path), full_page=True)
    shutil.copy(shot_path, ARTIFACT_DIR / "phase3_agent_before.png")
    print("📸 Saved Before screenshot:", shot_path)
    browser.close()
