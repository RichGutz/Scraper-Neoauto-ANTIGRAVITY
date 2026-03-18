"""
Extractor de URLs Diarias de NeoAuto.

Este script se especializa en raspar (scrape) la primera capa de información
de NeoAuto: las URLs de los anuncios de vehículos usados publicados en el día.

Funcionalidad Principal:
1.  **Conexión a Supabase**: Se inicializa una conexión segura con la base de
    datos de Supabase para leer y escribir información.
2.  **Carga de Mapeo de Marcas**: Lee un archivo JSON (`marcas_y_sinonimos.json`) 
    para estandarizar los nombres de las marcas de vehículos extraídas de las URLs.
3.  **Obtención de URLs Existentes**: Consulta la tabla `urls_autos_diarios` en
    Supabase para obtener un conjunto de todas las URLs ya registradas, con el
    fin de evitar la duplicación de datos.
4.  **Scraping de Páginas**: Navega a través de las páginas de resultados de
    NeoAuto que filtran por anuncios "publicado=hoy". Extrae el enlace (`href`)
    de cada anuncio.
5.  **Validación y Enriquecimiento**: Por cada URL nueva, extrae la marca, la
    valida contra el mapeo cargado y, si es válida, la prepara para ser
    insertada.
6.  **Inserción en Base de Datos**: Inserta el lote de URLs nuevas y validadas
    en la tabla `urls_autos_diarios` de Supabase, junto con la marca estandarizada, 
    la fecha de extracción y un booleano `procesado` inicializado en `False`.

El script está diseñado para ser el primer paso del pipeline diario, alimentando
la cola de URLs que serán procesadas en detalle por scripts posteriores.
"""
#!/usr/bin/env python3
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

# Configuración de logging
log_file_path = Path(__file__).parent / 'neoauto_scraper.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class NeoAutoDailyScraper:
    def __init__(self):
        # self.BASE_URL = "https://neoauto.com/venta-de-autos-usados?publicado=hoy"
        # self.BASE_URL = "https://neoauto.com/venta-de-autos-usados?publicado=hoy"
        self.BASE_URL = "https://neoauto.com/venta-de-autos-usados?publicado=1dia"
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.request_delay = 2
        self.supabase = self._init_supabase()
        self.brand_mapping = self._load_brand_mapping()
        logging.info(f"Marcos cargados: {len(self.brand_mapping)}")

    def _init_supabase(self):
        """Inicializa el cliente Supabase."""
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logging.critical("Variables de Supabase no configuradas")
            raise ValueError("Faltan credenciales de Supabase")
        
        try:
            client = create_client(supabase_url, supabase_key)
            client.table("urls_autos_diarios").select("count", count="exact").execute()
            return client
        except Exception as e:
            logging.critical(f"Fallo conexión Supabase: {str(e)}")
            raise

    def _load_brand_mapping(self) -> dict:
        """Carga el mapeo de marcas."""
        try:
            json_path = Path(__file__).parent / "marcas_y_sinonimos.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                return {k.lower().replace('-', '').replace(' ', ''): v.lower() for k,v in json.load(f).items()}
        except Exception as e:
            logging.critical(f"Error cargando marcas: {str(e)}")
            raise

    def _extract_brand_from_url(self, url: str) -> str:
        """Extrae marca de la URL sin validaciones estrictas."""
        match = re.search(r'/(usado|seminuevo)/([a-zA-Z0-9]+)-', url)
        return match.group(2).lower() if match else ""

    def _get_valid_brand(self, raw_brand: str) -> str:
        """Valida marca contra el mapeo."""
        clean_brand = raw_brand.lower().strip().replace('-', '').replace(' ', '')
        return self.brand_mapping.get(clean_brand, "")

    def _get_existing_urls(self) -> set:
        """Obtiene URLs existentes."""
        try:
            response = self.supabase.table('urls_autos_diarios').select('url').execute()
            return {item['url'] for item in response.data}
        except Exception as e:
            logging.error(f"Error obteniendo URLs existentes: {str(e)}")
            return set()

    def scrape_page(self, page: int) -> list:
        """Extrae URLs de una página usando múltiples estrategias (Regex/JSON/HTML)."""
        try:
            page_url = f"{self.BASE_URL}&page={page}"
            time.sleep(self.request_delay)
            response = requests.get(page_url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            
            raw_html = response.text
            found_slugs = set()
            
            # Estrategia 1: JSON Escapado (Next.js props usualmente)
            # Modificado: /? opcional y añadido seminuevo
            slugs_json_escaped = re.findall(r'\\"slug\\":\\"/?(auto/(?:usado|seminuevo|nuevo)/[^"]+)\\"', raw_html)
            found_slugs.update(slugs_json_escaped)
            
            # Estrategia 2: JSON Simple (fallback)
            # Modificado: /? opcional y añadido seminuevo
            slugs_json_simple = re.findall(r'"slug":"/?(auto/(?:usado|seminuevo|nuevo)/[^"]+)"', raw_html)
            found_slugs.update(slugs_json_simple)

            # Estrategia 3: HTML Anchor tags (Fallback a estructura clásica/SSR)
            # Modificado: /? opcional y añadido seminuevo
            hrefs_html = re.findall(r'href=["\']/?(auto/(?:usado|seminuevo|nuevo)/[^"\']+)["\']', raw_html)
            found_slugs.update(hrefs_html)

            # Normalizar slugs (asegurar slash inicial para la URL final)
            normalized_slugs = []
            for s in found_slugs:
                s = s.replace('\\', '') # Limpieza extra
                if not s.startswith('/'):
                    s = f"/{s}"
                normalized_slugs.append({'href': s})
            
            return normalized_slugs
        except Exception as e:
            logging.error(f"Error en página {page}: {str(e)}")
            return []

    def scrape_and_save(self):
        """Flujo principal simplificado."""
        try:
            existing_urls = self._get_existing_urls()
            new_urls = []
            
            # Procesar primera página para obtener total y primeros resultados
            links = self.scrape_page(1)
            # NOTA: Si la regex falla, links estará vacío
            
            # Lógica para encontrar el contador de resultados (Avisos)
            # Usamos BeautifulSoup para esto ya que el texto "X avisos" suele estar renderizado o en el JSON
            # En el debug vimos "54avisos" o similar en el texto plano
            soup = BeautifulSoup(requests.get(self.BASE_URL, headers=self.HEADERS).text, 'html.parser')
            total_pages = 1
            
            # Intento 1: Buscar texto "avisos" en el HTML raw para máxima cobertura
            # El texto puede decir "150 avisos" o estar en JSON {"total":150}
            total_items = 0
            count_match = re.search(r'(\d+)\s*avisos', soup.text, re.IGNORECASE)
            
            if count_match:
                total_items = int(count_match.group(1))
                total_pages = int(math.ceil(total_items / 20))
                logging.info(f"Total avisos: {total_items} - Total páginas: {total_pages}")
            else:
                # Intento 2: Buscar en el JSON (__NEXT_DATA__)
                total_json_match = re.search(r'"total":(\d+)', soup.text)
                if total_json_match:
                    total_items = int(total_json_match.group(1))
                    total_pages = int(math.ceil(total_items / 20))
                    logging.info(f"Total avisos (desde JSON): {total_items} - Total páginas: {total_pages}")
                else:
                    logging.warning("No se encontró total de avisos, asumiendo 1 página")
            
            # Si no encontramos links en pag 1, pero detectamos páginas, es posible que el scrape_page 1 fallara
            if not links and total_pages > 0:
                 logging.warning("Advertencia: No se detectaron links en página 1 con regex actual.")
            
            # Procesar todas las páginas
            for page in range(1, total_pages + 1):
                # Si es la página 1, ya tenemos los links (aunque podríamos re-escanear para ser consistentes, mejor reusar si no es costoso)
                if page == 1 and links:
                    page_links = links
                else:
                    page_links = self.scrape_page(page)
                
                if not page_links:
                    logging.info(f"Página {page}: cero autos encontrados. Terminando scraping.")
                    break
                
                logging.info(f"Página {page}: encontrados {len(page_links)} autos")
                
                for link in page_links:
                    href = link['href']
                    # Limpieza de slug si viene con comillas extra escapadas (safety check)
                    href = href.replace('\\', '') 
                    
                    full_url = f"https://neoauto.com{href}"
                    
                    if full_url in existing_urls:
                        continue
                        
                    brand = self._get_valid_brand(self._extract_brand_from_url(href))
                    if brand:
                        # Deduplicación local
                        if not any(u['url'] == full_url for u in new_urls):
                            new_urls.append({
                                "url": full_url,
                                "marca": brand,
                                "fecha_extraccion": datetime.now().isoformat(),
                                "procesado": False
                            })

            # Guardar resultados
            if new_urls:
                self.supabase.table('urls_autos_diarios').insert(new_urls).execute()
                logging.info(f"Guardadas {len(new_urls)} URLs nuevas")
            else:
                logging.info("No se encontraron URLs nuevas")

        except Exception as e:
            logging.critical(f"Error: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        scraper = NeoAutoDailyScraper()
        scraper.scrape_and_save()
    except KeyboardInterrupt:
        logging.warning("Proceso detenido manualmente")
    except Exception as e:
        logging.critical(f"Error: {str(e)}")
        sys.exit(1)
