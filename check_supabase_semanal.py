import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("C:/Users/rguti/Scraper.Neoauto/.env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Intentar buscar por DateTime
    print("Consultando 'autos_detalles' para el 2026-05-18...")
    res_18 = supabase.table('autos_detalles').select('*', count='exact').gte('DateTime', '2026-05-18T00:00:00').lt('DateTime', '2026-05-19T00:00:00').execute()
    print(f"Registros el lunes 18 (DateTime): {res_18.count}")
    
except Exception as e:
    print(f"Error con 'DateTime': {e}")
    try:
        # Si DateTime no existe, intentar created_at
        res_18_ca = supabase.table('autos_detalles').select('*', count='exact').gte('created_at', '2026-05-18T00:00:00').lt('created_at', '2026-05-19T00:00:00').execute()
        print(f"Registros el lunes 18 (created_at): {res_18_ca.count}")
    except Exception as e2:
        print(f"Error con 'created_at': {e2}")
