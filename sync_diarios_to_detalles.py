import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path
from datetime import datetime

# --- CONFIGURACIÓN ---
current_script_dir = Path(__file__).resolve().parent
dotenv_path = current_script_dir / ".env"
load_dotenv(dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Variables de entorno no encontradas.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SOURCE_TABLE = "autos_detalles_diarios"
TARGET_TABLE = "autos_detalles"

def sync_data():
    print(f"Iniciando sincronización desde '{SOURCE_TABLE}' hacia '{TARGET_TABLE}'...")

    # 1. Obtener URLs existentes en la tabla destino (solo las de 2026 para agilizar)
    print(f"Buscando duplicados en '{TARGET_TABLE}'...")
    # Como la tabla es muy grande, buscamos URLs que ya podrían estar ahí en 2026
    # Pero sabemos que la tabla está estancada en 2025, así que probablemente no haya muchas.
    # Para ser seguros, descargamos las URLs de la tabla diaria y comparamos.
    
    # 2. Descargar datos de la tabla diaria (filas de 2026)
    print(f"Descargando datos de '{SOURCE_TABLE}' (año 2026)...")
    all_source_data = []
    offset = 0
    limit = 1000
    
    while True:
        # Filtramos por DateTime >= 2026-01-01
        response = supabase.table(SOURCE_TABLE).select("*").gte("DateTime", "2026-01-01").range(offset, offset + limit - 1).execute()
        if not response.data:
            break
        all_source_data.extend(response.data)
        print(f"  Descargados {len(all_source_data)} registros...")
        if len(response.data) < limit:
            break
        offset += limit

    if not all_source_data:
        print("No se encontraron registros de 2026 en la tabla fuente.")
        return

    print(f"Total de registros a procesar: {len(all_source_data)}")

    # 3. Filtrar los que ya existen en la tabla destino
    # Para evitar descargar 350k URLs, verificaremos en bloques o uno por uno
    # Dado que son pocos miles, podemos verificar por lotes de URLs
    
    records_to_insert = []
    
    for i in range(0, len(all_source_data), 100):
        batch = all_source_data[i:i+100]
        urls = [r['URL'] for r in batch]
        
        # Consultar si estas URLs ya existen en el destino
        existing_res = supabase.table(TARGET_TABLE).select("URL").in_("URL", urls).execute()
        existing_urls = {r['URL'] for r in existing_res.data}
        
        for record in batch:
            if record['URL'] not in existing_urls:
                # Limpiar el record (eliminar ID si es autoincremental en el destino)
                clean_record = record.copy()
                if 'id' in clean_record:
                    del clean_record['id']
                records_to_insert.append(clean_record)

    print(f"Registros nuevos identificados: {len(records_to_insert)}")

    if not records_to_insert:
        print("No hay registros nuevos para insertar.")
        return

    # 4. Insertar en la tabla destino
    print(f"Insertando {len(records_to_insert)} registros en '{TARGET_TABLE}'...")
    
    # Insertar en lotes para evitar errores de timeout o payload
    batch_size = 100
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i+batch_size]
        try:
            res = supabase.table(TARGET_TABLE).insert(batch).execute()
            print(f"  Insertados {i + len(batch)} / {len(records_to_insert)}...")
        except Exception as e:
            print(f"Error al insertar lote: {e}")

    print("Sincronización completada exitosamente.")

if __name__ == "__main__":
    sync_data()
