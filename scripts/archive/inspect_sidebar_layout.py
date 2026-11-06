from playwright.sync_api import sync_playwright
import json

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page()
        page.goto("http://127.0.0.1:8501")
        page.wait_for_selector('[data-testid="stSidebar"]', timeout=20000)
        
        info = page.evaluate("""() => {
            const app = document.querySelector('[data-testid="stAppViewContainer"]');
            app.style.flexDirection = 'row-reverse';
            const sb = app.children[1];
            const main = app.children[2];
            const sbRect = sb.getBoundingClientRect();
            const mainRect = main.getBoundingClientRect();
            return {
                windowWidth: window.innerWidth,
                sb: { left: sbRect.left, right: sbRect.right, width: sbRect.width },
                main: { left: mainRect.left, right: mainRect.right, width: mainRect.width }
            };
        }""")
        print(json.dumps(info, indent=2))
        b.close()

if __name__ == "__main__":
    main()
