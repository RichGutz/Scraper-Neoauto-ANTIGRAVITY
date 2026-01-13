
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

def init_db():
    current_script_dir = Path(__file__).resolve().parent
    dotenv_path = current_script_dir / ".env"
    load_dotenv(dotenv_path)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def main():
    print("Iniciando limpieza de leads inválidos...")
    supabase = init_db()
    
    # 1. Identificar leads invalidos (con texto largo típico de mensajes de sistema)
    # Buscamos leads cuyo phone contenga "Messages and calls" o sea muy largo
    
    try:
        # Obtener todos los leads para filtrar en python (es mas seguro)
        response = supabase.table("crm_leads").select("phone").execute()
        
        invalid_phones = []
        for r in response.data:
            phone = r['phone']
            if "Messages and calls" in phone or "end-to-end encrypted" in phone or len(phone) > 20:
                print(f"Lead inválido detectado: {phone[:30]}...")
                invalid_phones.append(phone)
        
        if invalid_phones:
            print(f"Eliminando {len(invalid_phones)} leads inválidos y sus mensajes...")
            
            # Eliminar tareas asociadas primero (Foreign Key constraint)
            try:
                supabase.table("crm_tasks").delete().in_("lead_phone", invalid_phones).execute()
                print("Tareas eliminadas.")
            except Exception as e:
                print(f"Advertencia eliminando tareas: {e}")

            # Eliminar mensajes asociados
            supabase.table("crm_messages").delete().in_("lead_phone", invalid_phones).execute()
            print("Mensajes eliminados.")
            
            # Eliminar leads
            supabase.table("crm_leads").delete().in_("phone", invalid_phones).execute()
            print("Leads eliminados.")
        else:
            print("No se encontraron leads inválidos.")
            
    except Exception as e:
        print(f"Error en limpieza: {e}")

if __name__ == "__main__":
    main()
