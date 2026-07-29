from bs4 import BeautifulSoup
import re

with open("mercedes_gla_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print("--- Análisis de Precio ---")
# El precio suele tener S/ o U$S
prices = soup.find_all(string=re.compile(r'(S/|US\$)'))
for p in prices:
    parent = p.parent
    print(f"Parent tag: {parent.name}, classes: {parent.get('class')}, text: {parent.text.strip()}")

print("\n--- Análisis de Kilometraje ---")
# Kilometraje suele decir "km" o "Kilometraje"
kms = soup.find_all(string=re.compile(r'km|Kilometraje', re.IGNORECASE))
for k in kms:
    parent = k.parent
    print(f"Parent tag: {parent.name}, classes: {parent.get('class')}, text: {parent.text.strip()}")

print("\n--- Análisis de Ubicación ---")
# Buscar por "Lima" o icono map-pin
locs = soup.find_all(string=re.compile(r'Lima|San Isidro|Surco|Miraflores', re.IGNORECASE))
for l in locs:
    parent = l.parent
    print(f"Parent tag: {parent.name}, classes: {parent.get('class')}, text: {parent.text.strip()}")

print("\n--- Análisis de Descripción ---")
desc_tags = soup.find_all(string=re.compile(r'descripci.n', re.IGNORECASE))
for d in desc_tags:
    parent = d.parent
    # Check parent and grandparent
    print(f"Parent: {parent.name}, {parent.get('class')}, text: {parent.text[:50]}")
    grand = parent.parent
    print(f"Grandparent: {grand.name}, {grand.get('class')}, text length: {len(grand.text)}")

