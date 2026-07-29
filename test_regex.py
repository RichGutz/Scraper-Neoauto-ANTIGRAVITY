import re
with open('venta-de-autos-usados-honda.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Buscar en los JSON escapados
print("totalPages escapado:", set(re.findall(r'\\"totalPages\\":\s*(\d+)', text)))
print("total escapado:", set(re.findall(r'\\"total\\":\s*(\d+)', text)))
print("pages escapado:", set(re.findall(r'\\"pages\\":\s*(\d+)', text)))

# Buscar en el HTML plano si hay alguna etiqueta de número de avisos
print("Textos de 'avisos' en HTML:", set(re.findall(r'>(\d+)\s*avisos<', text, re.IGNORECASE)))
print("Textos de 'resultados' en HTML:", set(re.findall(r'>(\d+)\s*resultados<', text, re.IGNORECASE)))
