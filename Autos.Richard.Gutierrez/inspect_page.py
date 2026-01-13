
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Using one of the filtered URLs
        url = 'https://neoauto.com/auto/usado/toyota-yaris-2025-1859237'
        print(f"Navigating to {url}")
        await page.goto(url, timeout=60000)
        
        # Get all text content
        text = await page.inner_text("body")
        print("--- PAGE TEXT START ---")
        print(text)
        print("--- PAGE TEXT END ---")
        
        # Also try to specifically look for table or dl elements often used for specs
        specs = await page.evaluate('''() => {
            const data = [];
            document.querySelectorAll('li, div, p, span').forEach(el => {
                if(el.innerText && (el.innerText.includes('Potencia') || el.innerText.includes('Consumo') || el.innerText.includes('Rendimiento'))) {
                    data.push(el.innerText);
                }
            });
            return data;
        }''')
        print("--- SPECS FOUND ---")
        for s in specs:
            print(s)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
