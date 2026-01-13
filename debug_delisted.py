import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://neoauto.com/auto/usado/mazda-bt-50-2019-1839494"
    print(f"Inspecting: {url}")
    
    async with async_playwright() as p:
        # Use same stealth args as main script
        browser = await p.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            title = await page.title()
            
            print(f"Page Title: {title}")
            
            keywords = ["finalizado", "vendido", "no disponible", "expirado"]
            print("\n--- Keyword Check ---")
            found = False
            for kw in keywords:
                if kw in content.lower():
                    print(f"Found keyword: '{kw}'")
                    found = True
                    # Try to find context (snippet)
                    idx = content.lower().find(kw)
                    snippet = content[max(0, idx-50):min(len(content), idx+50)]
                    print(f"  Context: ...{snippet}...")
            
            if not found:
                print("No obvious keywords found.")
                
            # Check for specific classes often used
            alert = await page.query_selector(".alert")
            if alert:
                text = await alert.inner_text()
                print(f"Found .alert: {text}")

        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
