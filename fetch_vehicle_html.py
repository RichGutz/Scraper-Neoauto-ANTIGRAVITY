from playwright.sync_api import sync_playwright
import time

url = "https://neoauto.com/auto/seminuevo/mercedes-benz-gla-200-2015-1875009"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=60000, wait_until="domcontentloaded")
    
    # Scroll to load dynamic content
    for _ in range(3):
        page.mouse.wheel(0, 800)
        time.sleep(1)
        
    html = page.content()
    
    with open("mercedes_gla_test.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("HTML saved to mercedes_gla_test.html")
    browser.close()
