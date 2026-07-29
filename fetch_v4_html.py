import importlib.util
from playwright.sync_api import sync_playwright
import time

spec = importlib.util.spec_from_file_location("v4", "extractores/4.DIARIO.SEMANAL.extractor_individual_v4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

url = "https://neoauto.com/auto/seminuevo/mercedes-benz-gla-200-2015-1875009"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768}
    )
    page = context.new_page()
    
    base_url = "https://neoauto.com/"
    print("Navegando a homepage...")
    page.goto(base_url, timeout=90000, wait_until="domcontentloaded")
    time.sleep(2)
    print("Navegando a seminuevos...")
    page.goto(f"{base_url}venta-de-autos-seminuevos", timeout=90000, wait_until="domcontentloaded")
    time.sleep(2)
    print("Navegando a URL final...")
    page.goto(url, timeout=90000, wait_until="domcontentloaded")
    
    for _ in range(3):
        page.mouse.wheel(0, 800)
        time.sleep(1.2)
        page.mouse.wheel(0, -400)
        time.sleep(0.8)
        
    v4.handle_cookie_popup(page)
    v4.handle_neopopups(page)
    v4.handle_all_popups(page)
    v4.handle_satisfaction_popup(page)
    
    html = page.content()
    with open("dump.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("DUMP OK")
    browser.close()
