import re, json

with open('venta-de-autos-usados-honda.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Buscamos si usa Next.js (muy común en React moderno)
matches = re.findall(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', text)
if matches:
    print("Found __NEXT_DATA__")
    try:
        data = json.loads(matches[0])
        # Buscamos recursivamente palabras como 'total', 'pages', 'pagination'
        def find_keys(obj, target_keys):
            found = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(t in k.lower() for t in target_keys):
                        found.append({k: v if not isinstance(v, (dict, list)) else f"<{type(v).__name__}>"})
                    found.extend(find_keys(v, target_keys))
            elif isinstance(obj, list):
                for item in obj:
                    found.extend(find_keys(item, target_keys))
            return found
        
        results = find_keys(data, ['total', 'page', 'count'])
        # Filtramos para no imprimir demasiada basura
        unique_results = []
        for r in results:
            if r not in unique_results:
                unique_results.append(r)
        
        print("Posibles variables de paginación encontradas:")
        for r in unique_results[:20]: # limitamos a 20
            print(r)
            
    except Exception as e:
        print(f"Error parseando JSON: {e}")
else:
    print("No se encontró __NEXT_DATA__")
    # Buscaremos cualquier script con JSON state
    scripts = re.findall(r'<script.*?>(\{.*?\})</script>', text)
    print(f"Encontrados {len(scripts)} scripts con posible JSON")
