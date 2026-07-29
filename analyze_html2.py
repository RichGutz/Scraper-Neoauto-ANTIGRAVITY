import re, json

with open('venta-de-autos-usados-honda.html', 'r', encoding='utf-8') as f:
    text = f.read()

scripts = re.findall(r'<script.*?>(\{.*?\})</script>', text)
if scripts:
    try:
        data = json.loads(scripts[0])
        # Buscamos en este JSON las llaves relacionadas con el total
        def find_total(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() in ['total', 'total_items', 'count', 'totalcount', 'totalpages', 'pages']:
                        print(f"ENCONTRADO: {path}.{k} = {v}")
                    find_total(v, path + "." + k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_total(item, path + f"[{i}]")
                    
        find_total(data, "root")
    except Exception as e:
        print("El script encontrado no era JSON válido:", e)
        print("Fragmento del script:")
        print(scripts[0][:500])
else:
    print("No se encontraron scripts con JSON.")
