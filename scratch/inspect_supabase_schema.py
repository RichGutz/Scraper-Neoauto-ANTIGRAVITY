import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def inspect_schema():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # Intentamos ver los tipos de datos de las columnas
    # Usamos una consulta que probablemente esté permitida o de un error informativo
    print("--- Inspección de Columnas ---")
    try:
        # Consultamos todos los registros (limite 1) para ver las llaves del dict
        res = supabase.table("crm_contactos").select("*").limit(1).execute()
        if res.data:
            print(f"Columnas detectadas: {list(res.data[0].keys())}")
            print(f"Ejemplo de datos: {res.data[0]}")
    except Exception as e:
        print(f"Error al leer datos: {e}")

    print("\n--- Buscando Restricciones (Check Constraints) ---")
    # Intentamos ejecutar un RPC común si existe, o forzar un error de validación
    # enviando un objeto con tipos incorrectos para ver qué dice el servidor.
    try:
        # Forzamos un error de tipo en una columna que sepamos el tipo (ej. fecha_actualizacion a un numero)
        # Esto a veces revela información del esquema en el mensaje de error de Postgres.
        print("Provocando error de tipo para ver mensajes del servidor...")
        supabase.table("crm_contactos").update({"fecha_actualizacion": 12345}).limit(1).execute()
    except Exception as e:
        print(f"Mensaje del Servidor: {str(e)}")

    print("\n--- Buscando Conjunto Cerrado (Valores Únicos) ---")
    try:
        res = supabase.table("crm_contactos").select("estado_embudo").execute()
        uniq_states = sorted(list(set([r['estado_embudo'] for r in res.data if r['estado_embudo']])))
        print(f"Valores únicos actuales en 'estado_embudo': {uniq_states}")
    except Exception as e:
        print(f"Error al obtener estados: {e}")

if __name__ == "__main__":
    inspect_schema()
