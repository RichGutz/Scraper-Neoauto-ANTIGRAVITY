import re
from bs4 import BeautifulSoup
import sys

# Forzar utf-8 para la salida y evitar crash con emojis
sys.stdout.reconfigure(encoding='utf-8')

with open("dump.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print("=== TÍTULO Y PRECIO ===")
h1 = soup.find('h1')
if h1:
    print(f"H1: {h1.text.strip()}")
    # El precio suele estar cerca del H1 o en un componente de precio
    price_tags = soup.find_all(string=re.compile(r'(S/|US\$)\s*[\d,.]+'))
    for p in price_tags:
        parent = p.parent
        print(f"Posible Precio: <{parent.name} class='{parent.get('class')}'>{p.strip()}</{parent.name}>")

print("\n=== DESCRIPCIÓN ===")
headers = soup.find_all(['h2', 'h3', 'div', 'p', 'span'], string=re.compile(r'(?i)^descripci[oó]n$'))
for h in headers:
    next_el = h.find_next_sibling()
    if next_el:
        print(f"Header: <{h.name} class='{h.get('class')}'>")
        print(f"Content: {next_el.text.strip()[:200]}...\n")

print("\n=== UBICACIÓN ===")
locs = soup.find_all(string=re.compile(r'Lima|San Isidro|Surco|Miraflores', re.IGNORECASE))
for l in locs:
    parent = l.parent
    if parent.name not in ['script', 'style', 'html', 'body']:
        print(f"[{parent.name}] class='{parent.get('class')}' -> {l.strip()[:100]}")
