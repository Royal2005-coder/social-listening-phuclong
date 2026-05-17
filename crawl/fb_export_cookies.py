import time
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_FILE = Path("crawl/.cookies/fb_state.json")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Mo trinh duyet — DANG NHAP Facebook — quay lai nhan ENTER")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        viewport={"width": 390, "height": 844}, locale="vi-VN")
    page = context.new_page()
    page.goto("https://m.facebook.com/", wait_until="domcontentloaded")
    time.sleep(2)
    input(">>> Nhan ENTER sau khi dang nhap xong... ")
    context.storage_state(path=str(STATE_FILE))
    cookies = context.cookies()
    fb = [c for c in cookies if "facebook" in c.get("domain", "")]
    print(f"Saved {len(fb)} Facebook cookies to {STATE_FILE}")
    browser.close()
print("DONE!")
