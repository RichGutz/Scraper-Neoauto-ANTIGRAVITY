import requests
import re

URL = "https://neoauto.com/venta-de-autos-usados?publicado=1dia"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print(f"Probando URL: {URL}")
response = requests.get(URL, headers=HEADERS, timeout=15)
raw_html = response.text

print(f"Tamaño del HTML: {len(raw_html)} bytes")

# Estrategia 1: JSON Escapado (Modificada con /? opcional)
slugs_json_escaped = re.findall(r'\\"slug\\":\\"/?(auto/(?:usado|seminuevo|nuevo)/[^"]+)\\"', raw_html)
print(f"Estrategia 1 (Escapado): Encontrados {len(slugs_json_escaped)}")
if slugs_json_escaped:
    print(f"Ejemplo: {slugs_json_escaped[0]}")

# Estrategia 2: JSON Simple (Modificada con /? opcional)
slugs_json_simple = re.findall(r'"slug":"/?(auto/(?:usado|seminuevo|nuevo)/[^"]+)"', raw_html)
print(f"Estrategia 2 (Simple): Encontrados {len(slugs_json_simple)}")
if slugs_json_simple:
    print(f"Ejemplo: {slugs_json_simple[0]}")

# Estrategia 3: HTML Anchor tags (Modificada para capturar sin el slash inicial)
hrefs_html = re.findall(r'href=["\']/?(auto/(?:usado|seminuevo|nuevo)/[^"\']+)["\']', raw_html)
print(f"Estrategia 3 (HTML): Encontrados {len(hrefs_html)}")
if hrefs_html:
    print(f"Ejemplo: {hrefs_html[0]}")

# Verificar contador de avisos
match = re.search(r'(\d+)\s*avisos', raw_html, re.IGNORECASE)
if match:
    print(f"Contador de avisos encontrado: {match.group(1)}")
else:
    print("No se encontró el contador de avisos")
