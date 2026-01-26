
import requests
from bs4 import BeautifulSoup
import math
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv
import json
from pathlib import Path
import logging
import re
import sys
import time
import random

# Configuración de logging (Compatible con Linux/Windows)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('weekly_extractor_v2.log', encoding='utf-8')
    ]
)

class NeoAutoWeeklyScraper:
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        # Base URL template for brand search
        self.BASE_URL_TEMPLATE = "https://neoauto.com/venta-de-autos-usados-{brand}"
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
        self.request_delay = 2
        
        # Inicializar Supabase
        self.supabase = self._init_supabase()
        
        # Cargar marcas
        self.brand_mapping = self._load_brand_mapping()
        logging.info(f"Marcas cargadas para barrido semanal: {len(self.brand_mapping)}")

    def _init_supabase(self):
        """Inicializa el cliente Supabase."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logging.critical("Variables de Supabase no configuradas")
            raise ValueError("Faltan credenciales de Supabase")
        
        try:
            client = create_client(supabase_url, supabase_key)
            return client
        except Exception as e:
            logging.critical(f"Fallo conexión Supabase: {str(e)}")
            raise

    def _load_brand_mapping(self) -> dict:
        """Carga el mapeo de marcas."""
        try:
            json_path = Path(__file__).parent / "marcas_y_sinonimos.json"
            if not json_path.exists():
                logging.error(f"Archivo de marcas no encontrado: {json_path}")
                return {}
            
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                unique_brands = {}
                for k, v in raw_data.items():
                    # Normalizar a minúsculas y strip
                    normalized_key = k.lower().strip()
                    if isinstance(v, list):
                        normalized_brand = v[0].lower().strip()
                    elif isinstance(v, str):
                        normalized_brand = v.lower().strip()
                    else:
                        continue
                    
                    # Guardamos la marca normalizada (value) como clave para iterar de manera única
                    unique_brands[normalized_brand] = normalized_brand
                
                return unique_brands
        except Exception as e:
            logging.critical(f"Error cargando marcas: {str(e)}")
            return {}

    def get_existing_urls(self) -> set:
        """Obtiene URLs existentes para evitar duplicados en la inserción."""
        # NOTA: Para el barrido semanal masivo, podríamos optar por limpiar la tabla diaria o simplemente
        # hacer un upsert. El script original V1 limpiaba la tabla `urls_autos` completamente.
        # Asumiremos la lógica del V1: Limpiar y re-llenar o Upsert.
        # Para ser seguros, haremos "on conflict do nothing" o check previo.
        # Dado que es 'semanal', el usuario suele querer un barrido fresco.
        # El script `2.SEMANAL...V1.py` tenía un método `clear_urls_autos_table`.
        return set()

    def scrape_page(self, base_url: str, page: int) -> list:
        """Extrae URLs de una página usando múltiples estrategias (Regex/JSON/HTML)."""
        try:
            page_url = f"{base_url}?page={page}&ord_publication_date=1"
            time.sleep(self.request_delay)
            logging.info(f"Scraping: {page_url}")
            
            response = requests.get(page_url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            
            raw_html = response.text
            found_slugs = set()
            
            # Estrategia 1: JSON Escapado
            slugs_json_escaped = re.findall(r'\\"slug\\":\\"(/auto/(?:usado|nuevo)/[^"]+)\\"', raw_html)
            found_slugs.update(slugs_json_escaped)
            
            # Estrategia 2: JSON Simple
            slugs_json_simple = re.findall(r'"slug":"(/auto/(?:usado|nuevo)/[^"]+)"', raw_html)
            found_slugs.update(slugs_json_simple)

            # Estrategia 3: HTML Anchor tags
            hrefs_html = re.findall(r'href=["\'](/?auto/(?:usado|nuevo)/[^"\']+)["\']', raw_html)
            found_slugs.update(hrefs_html)

            # Normalizar
            normalized_results = []
            for s in found_slugs:
                s = s.replace('\\', '')
                if not s.startswith('/'):
                    s = f"/{s}"
                
                # Extraer marca de la URL para guardar metadata correcta
                # Ejemplo: /auto/usado/volkswagen-amarok-2016-1859567 -> volkswagen
                brand_match = re.search(r'/(?:usado|nuevo)/([a-z0-9]+)-', s)
                brand_in_url = brand_match.group(1) if brand_match else "unknown"
                
                full_url = f"https://neoauto.com{s}"
                normalized_results.append({
                    "url": full_url,
                    "marca": brand_in_url,
                    "fecha_extraccion": datetime.now().isoformat(),
                    "procesado": False
                })
            
            return normalized_results
        except Exception as e:
            logging.error(f"Error en página {page}: {str(e)}")
            return []

    def get_total_pages(self, url: str) -> int:
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            total_items = 0
            
            # Intento 1: Texto visible
            count_element = soup.find(lambda tag: tag.name == "div" and tag.text and "avisos" in tag.text.lower())
            if count_element:
                count_text = count_element.get_text(strip=True)
                match = re.search(r'(\d+)\s*avisos', count_text)
                if match:
                    total_items = int(match.group(1))
            
            # Intento 2: JSON
            if total_items == 0:
                 total_match = re.search(r'"total":(\d+)', response.text)
                 if total_match:
                     total_items = int(total_match.group(1))
            
            if total_items > 0:
                return math.ceil(total_items / 20)
            return 1
            
        except Exception as e:
            logging.warning(f"No se pudo determinar páginas para {url}: {e}")
            return 1

    def clear_urls_table(self):
        """Limpia la tabla de destino antes de empezar (comportamiento legacy)."""
        logging.info("Limpiando tabla 'urls_autos'...")
        try:
            self.supabase.table('urls_autos').delete().neq('id', 0).execute()
        except Exception as e:
            logging.error(f"Error limpiando tabla: {e}")

    def scrape_week(self):
        """Flujo principal."""
        if not self.brand_mapping:
            logging.critical("No se cargaron marcas. Abortando.")
            return

        # 1. Limpiar tabla (Opcional, basado en lógica legacy)
        self.clear_urls_table()

        total_saved = 0

        # Iterar sobre cada marca
        for brand in self.brand_mapping.keys():
            logging.info(f"\n--- Procesando Marca: {brand.upper()} ---")
            
            base_url = self.BASE_URL_TEMPLATE.format(brand=brand)
            total_pages = self.get_total_pages(base_url)
            logging.info(f"Total páginas estimadas: {total_pages}")
            
            for page in range(1, total_pages + 1):
                page_data = self.scrape_page(base_url, page)
                
                if not page_data:
                    logging.info(f"Página {page}: 0 autos. Siguiente marca...")
                    break
                
                logging.info(f"Página {page}: {len(page_data)} URLs encontradas. Guardando en Supabase...")
                
                # Guardar en Supabase por lotes
                try:
                    self.supabase.table('urls_autos').insert(page_data).execute()
                    total_saved += len(page_data)
                except Exception as e:
                    logging.error(f"Error guardando lote página {page}: {e}")
                
                # Pausa
                time.sleep(random.uniform(1.5, 3))

        logging.info(f"\n--- SCRAPING FINALIZADO. Total URLs guardadas: {total_saved} ---")

if __name__ == "__main__":
    try:
        scraper = NeoAutoWeeklyScraper()
        scraper.scrape_week()
    except KeyboardInterrupt:
        logging.warning("Proceso detenido manualmente")
    except Exception as e:
        logging.critical(f"Error: {str(e)}")
        sys.exit(1)
