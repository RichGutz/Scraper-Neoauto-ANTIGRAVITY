import sys
import json
import importlib.util
from playwright.sync_api import sync_playwright

# Cargar el script v4 de forma dinámica
spec = importlib.util.spec_from_file_location("scraper4", "extractores/4.DIARIO.SEMANAL.extractor_individual_v4.py")
scraper4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper4)

def main():
    try:
        # Hardcodear la URL del Mercedes para no depender de supabase si falla
        test_url = "https://neoauto.com/auto/seminuevo/mercedes-benz-gla-200-2015-1875009"
        print(f"URL de Prueba seleccionada: {test_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768}
            )
            page = context.new_page()
            
            # Ejecutar la función core del script v4
            data = scraper4.advanced_scraping(test_url, page)
            
            # Fix unicode issues on windows console
            sys.stdout.reconfigure(encoding='utf-8')
            
            print("\n" + "="*50)
            print("RESULTADOS DE LA EXTRACCIÓN (V4)")
            print("="*50)
            if data:
                # Cortar la descripción para no inundar la terminal
                if data.get('descripcion'):
                    data['descripcion'] = data['descripcion'][:200] + "... (recortada para visualización)"
                print(json.dumps(data, indent=4, ensure_ascii=False))
            else:
                print("FALLÓ: La función devolvió None")
                
            browser.close()
            
    except Exception as e:
        print(f"Error en la prueba: {e}")

if __name__ == "__main__":
    main()
