import requests
from bs4 import BeautifulSoup

BASE_URL = "https://neoauto.com/venta-de-autos-usados?publicado=hoy"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Fetch URL: {BASE_URL}")
    response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    with open('debug_neoauto.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("HTML saved to debug_neoauto.html")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Test selectors
    links = soup.select('a[href*="/auto/usado/"], a[href*="/auto/nuevo/"]')
    print(f"Links found (new selector): {len(links)}")
    for i, link in enumerate(links[:3]):
        print(f"Link {i}: {link.get('href')}")
        
    old_links = soup.select('a.c-results__link[href]')
    print(f"Links found (old selector): {len(old_links)}")
    
    avisos_div = soup.find(lambda tag: tag.name == "div" and tag.text and "avisos" in tag.text.lower())
    if avisos_div:
        print(f"Avisos div text: {avisos_div.get_text(strip=True)}")
    else:
        print("Avisos div not found")

except Exception as e:
    print(f"Error: {e}")
