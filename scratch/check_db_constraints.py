import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def check_constraint():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    try:
        # Intentamos actualizar un registro a un estado inválido para ver la restricción
        print("Probando actualización a estado inválido...")
        # Usamos un filtro para que sea válido
        res = supabase.table("crm_contactos").update({"estado_embudo": "ESTADO_PRUEBA_INVALIDO"}).neq("url", "dummy").execute()
        print("RESULTADO: No hay restricción (actualización exitosa).")
    except Exception as e:
        print(f"RESULTADO: Restricción detectada!\nDetalles: {str(e)}")

if __name__ == "__main__":
    check_constraint()
