import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def inspect_gyp():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    print("--- Inspección de crm_gyp ---")
    try:
        res = supabase.table("crm_gyp").select("*").limit(1).execute()
        if res.data:
            print(f"Columnas detectadas: {list(res.data[0].keys())}")
            print(f"Ejemplo de datos: {res.data[0]}")
        else:
            print("No hay datos en crm_gyp para inspeccionar columnas.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_gyp()
