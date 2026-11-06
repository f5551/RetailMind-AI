import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(r"c:\Users\HP\Desktop\RetailMind A")
AUDIT_IMG_DIR = WORKSPACE_ROOT / "docs" / "audit_ui" / "end_user_audit"
AUDIT_IMG_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\HP\.gemini\antigravity\brain\1c7d81ed-4bea-496f-bf76-9bdfffeebb00")

def run_audit():
    print("🔍 Starting Comprehensive End-User Product & UX Audit via Playwright...")
    findings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        # -------------------------------------------------------------
        # 1. First-time user / Empty State (No dataset loaded)
        # -------------------------------------------------------------
        print("\n--- 1. Testing Empty State Across Views ---")
        context_empty = browser.new_context(viewport={"width": 1440, "height": 900})
        page_empty = context_empty.new_page()

        # View 1: Overview Empty State
        page_empty.goto("http://127.0.0.1:8501/?view=overview", timeout=30000)
        page_empty.wait_for_selector("h1", timeout=15000)
        time.sleep(2.0)
        img_empty_overview = AUDIT_IMG_DIR / "audit_01_empty_overview.png"
        page_empty.screenshot(path=str(img_empty_overview), full_page=True)
        print(f"📸 Captured Empty Overview: {img_empty_overview.name}")

        # View 2: Agent Empty State
        page_empty.goto("http://127.0.0.1:8501/?view=agent", timeout=30000)
        page_empty.wait_for_selector("h1", timeout=15000)
        time.sleep(2.0)
        img_empty_agent = AUDIT_IMG_DIR / "audit_02_empty_agent.png"
        page_empty.screenshot(path=str(img_empty_agent), full_page=True)
        print(f"📸 Captured Empty Agent: {img_empty_agent.name}")

        # View 3: Dataset Empty State
        page_empty.goto("http://127.0.0.1:8501/?view=dataset", timeout=30000)
        page_empty.wait_for_selector("h1", timeout=15000)
        time.sleep(2.0)
        img_empty_dataset = AUDIT_IMG_DIR / "audit_03_empty_dataset.png"
        page_empty.screenshot(path=str(img_empty_dataset), full_page=True)
        print(f"📸 Captured Empty Dataset: {img_empty_dataset.name}")

        # View 4: Memory Empty State
        page_empty.goto("http://127.0.0.1:8501/?view=memory", timeout=30000)
        page_empty.wait_for_selector("h1", timeout=15000)
        time.sleep(2.0)
        img_empty_memory = AUDIT_IMG_DIR / "audit_04_empty_memory.png"
        page_empty.screenshot(path=str(img_empty_memory), full_page=True)
        print(f"📸 Captured Empty Memory: {img_empty_memory.name}")

        # View 5: Audit Empty State
        page_empty.goto("http://127.0.0.1:8501/?view=audit", timeout=30000)
        page_empty.wait_for_selector("h1", timeout=15000)
        time.sleep(2.0)
        img_empty_audit = AUDIT_IMG_DIR / "audit_05_empty_audit.png"
        page_empty.screenshot(path=str(img_empty_audit), full_page=True)
        print(f"📸 Captured Empty Audit: {img_empty_audit.name}")

        # -------------------------------------------------------------
        # 2. Populated State (Sample Dataset Loaded)
        # -------------------------------------------------------------
        print("\n--- 2. Testing Populated State Across Views ---")
        context_loaded = browser.new_context(viewport={"width": 1440, "height": 900})
        page_loaded = context_loaded.new_page()

        # View 1: Overview Populated
        page_loaded.goto("http://127.0.0.1:8501/?view=overview&load_sample=1", timeout=30000)
        page_loaded.wait_for_selector("h1", timeout=15000)
        time.sleep(2.5)
        img_loaded_overview = AUDIT_IMG_DIR / "audit_06_loaded_overview.png"
        page_loaded.screenshot(path=str(img_loaded_overview), full_page=True)
        print(f"📸 Captured Loaded Overview: {img_loaded_overview.name}")

        # View 2: Agent Mock Conversation & Approval State
        page_loaded.goto("http://127.0.0.1:8501/?view=agent&mock_agent_view=1", timeout=30000)
        page_loaded.wait_for_selector("h1", timeout=15000)
        time.sleep(2.5)
        img_loaded_agent = AUDIT_IMG_DIR / "audit_07_loaded_agent.png"
        page_loaded.screenshot(path=str(img_loaded_agent), full_page=True)
        print(f"📸 Captured Loaded Agent: {img_loaded_agent.name}")

        # View 3: Dataset Ingestion Populated
        page_loaded.goto("http://127.0.0.1:8501/?view=dataset&load_sample=1", timeout=30000)
        page_loaded.wait_for_selector("h1", timeout=15000)
        time.sleep(2.5)
        img_loaded_dataset = AUDIT_IMG_DIR / "audit_08_loaded_dataset.png"
        page_loaded.screenshot(path=str(img_loaded_dataset), full_page=True)
        print(f"📸 Captured Loaded Dataset: {img_loaded_dataset.name}")

        # Expand upload details & dev secret
        uploader_expander = page_loaded.locator("details:has-text('رفع ملف مبيعات') summary, div[data-testid='stExpander']:has-text('رفع ملف مبيعات')").first
        if uploader_expander.is_visible():
            uploader_expander.click()
            time.sleep(1.0)
            img_dataset_expander = AUDIT_IMG_DIR / "audit_09_dataset_expanded.png"
            page_loaded.screenshot(path=str(img_dataset_expander), full_page=True)
            print(f"📸 Captured Dataset Ingestion Expander: {img_dataset_expander.name}")

        # View 4: Memory Populated
        page_loaded.goto("http://127.0.0.1:8501/?view=memory&load_sample=1", timeout=30000)
        page_loaded.wait_for_selector("h1", timeout=15000)
        time.sleep(2.0)
        img_loaded_memory = AUDIT_IMG_DIR / "audit_10_loaded_memory.png"
        page_loaded.screenshot(path=str(img_loaded_memory), full_page=True)
        print(f"📸 Captured Loaded Memory: {img_loaded_memory.name}")

        # View 5: Security Audit Populated
        page_loaded.goto("http://127.0.0.1:8501/?view=audit&load_sample=1", timeout=30000)
        page_loaded.wait_for_selector("h1", timeout=15000)
        time.sleep(2.0)
        img_loaded_audit = AUDIT_IMG_DIR / "audit_11_loaded_audit.png"
        page_loaded.screenshot(path=str(img_loaded_audit), full_page=True)
        print(f"📸 Captured Loaded Audit: {img_loaded_audit.name}")

        # Sidebar Expanders Inspection
        sidebar_expander_dataset = page_loaded.locator("div[data-testid='stSidebar'] details summary, div[data-testid='stSidebar'] [data-testid='stExpander'] summary").all()
        print(f"Found {len(sidebar_expander_dataset)} expanders in sidebar.")
        for idx, exp in enumerate(sidebar_expander_dataset):
            try:
                exp.click()
                time.sleep(0.5)
            except Exception:
                pass
        img_sidebar_expanded = AUDIT_IMG_DIR / "audit_12_sidebar_expanded.png"
        page_loaded.screenshot(path=str(img_sidebar_expanded), full_page=True)
        print(f"📸 Captured Sidebar Expanded: {img_sidebar_expanded.name}")

        # Copy all audit screenshots to artifact directory for markdown embedding
        for s in AUDIT_IMG_DIR.glob("audit_*.png"):
            dst = ARTIFACT_DIR / s.name
            dst.write_bytes(s.read_bytes())
            print(f"📋 Copied to artifact dir: {s.name}")

        print("\n🎉 Comprehensive Audit Screenshots Captured Successfully!")

if __name__ == "__main__":
    run_audit()
