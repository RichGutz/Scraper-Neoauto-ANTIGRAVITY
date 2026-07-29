import requests
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def test_url(url):
    print(f"\n--- Testing: {url} ---")
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"Status Code: {res.status_code}")
        
        if res.status_code != 200:
            print("Página bloqueada o no encontrada.")
            return
            
        html = res.text
        
        # Guardar una copia para revisión manual si es necesario
        filename = url.split('/')[-1] + '.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML guardado localmente como: {filename}")
        
        # Test Total Items
        total_match = re.search(r'"total":(\d+)', html)
        print(f"Match Regex 'total': {total_match.group(1) if total_match else 'NO ENCONTRADO'}")
        
        # Test Slugs
        # Nota: He agregado 'seminuevo' a las regex para ver si lo captura en caso de existir, 
        # aunque el código actual solo busca usado|nuevo.
        slugs_escaped = set(re.findall(r'\\"slug\\":\\"(/auto/(?:usado|nuevo|seminuevo)/[^"]+)\\"', html))
        print(f"Slugs escapados encontrados: {len(slugs_escaped)}")
        
        slugs_simple = set(re.findall(r'"slug":"(/auto/(?:usado|nuevo|seminuevo)/[^"]+)"', html))
        print(f"Slugs simples encontrados: {len(slugs_simple)}")
        
        hrefs = set(re.findall(r'href=["\'](/?auto/(?:usado|nuevo|seminuevo)/[^"\']+)["\']', html))
        print(f"Slugs href encontrados: {len(hrefs)}")

    except Exception as e:
        print(f"Error testeando {url}: {e}")

if __name__ == "__main__":
    test_url("https://neoauto.com/venta-de-autos-usados-honda")
    test_url("https://neoauto.com/venta-de-autos-seminuevos-honda")
