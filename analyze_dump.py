import re
from bs4 import BeautifulSoup
import json

with open("dump.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print("=== BUSCANDO PRECIO ===")
# El precio ahora suele estar en otras clases, buscamos S/ o US$
prices = soup.find_all(string=re.compile(r'S/\s*\d+|US\$\s*\d+'))
for p in prices[:5]:
    parent = p.parent
    print(f"[{parent.name}] class='{parent.get('class')}' -> {p.strip()}")

print("\n=== BUSCANDO KILOMETRAJE ===")
kms = soup.find_all(string=re.compile(r'km', re.IGNORECASE))
for k in kms:
    if len(k.strip()) < 15 and any(char.isdigit() for char in k):
        parent = k.parent
        print(f"[{parent.name}] class='{parent.get('class')}' -> {k.strip()}")

print("\n=== BUSCANDO DATOS ESPECÍFICOS EN LABELS ===")
# Usualmente Neoauto pone labels como 'Kilometraje', 'Transmisión'
for label in ['Kilometraje', 'Transmisión', 'Año']:
    elems = soup.find_all(string=re.compile(label, re.IGNORECASE))
    for e in elems:
        parent = e.parent
        # Podría estar en una lista dl/dt/dd o divs hermanos
        print(f"LABEL '{label}' -> Parent tag: {parent.name}, class: {parent.get('class')}")
        if parent.find_next_sibling():
            print(f"   Next Sibling: {parent.find_next_sibling().text.strip()}")

print("\n=== BUSCANDO DESCRIPCIÓN ===")
# En lugar de agarrar el schema json, buscamos un h2 o h3 o div que diga Descripción
headers = soup.find_all(['h2', 'h3', 'div', 'p', 'span'], string=re.compile(r'(?i)^descripci[oó]n$'))
for h in headers:
    print(f"Found header: <{h.name} class='{h.get('class')}'>{h.text}</{h.name}>")
    # Imprimir contenido cercano
    next_el = h.find_next_sibling()
    if next_el:
        print(f"  Next content: {next_el.text.strip()[:100]}...")
