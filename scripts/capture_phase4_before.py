import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

WORKSPACE_ROOT = Path(r"c:\Users\HP\Desktop\RetailMind A")
SCREENSHOT_DIR = WORKSPACE_ROOT / "docs" / "audit_ui" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\1c7d81ed-4bea-496f-bf76-9bdfffeebb00")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})
    page.goto("http://127.0.0.1:8501/?view=dataset", timeout=20000)
    page.wait_for_timeout(2500)
    
    shot = SCREENSHOT_DIR / "phase4_dataset_before.png"
    page.screenshot(path=str(shot), full_page=True)
    shutil.copy2(shot, ARTIFACT_DIR / "phase4_dataset_before.png")
    print(f"Captured Before screenshot: {shot}")
    browser.close()
