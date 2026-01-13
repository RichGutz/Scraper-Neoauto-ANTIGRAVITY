
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
    supabase = init_db()
    
    phone_to_delete = "51922285372"
    
    print(f"Eliminando lead duplicado: {phone_to_delete}")
    
    try:
        # 1. Eliminar tareas
        supabase.table("crm_tasks").delete().eq("lead_phone", phone_to_delete).execute()
        print("Tareas eliminadas.")
        
        # 2. Eliminar mensajes
        supabase.table("crm_messages").delete().eq("lead_phone", phone_to_delete).execute()
        print("Mensajes eliminados.")
        
        # 3. Eliminar lead
        supabase.table("crm_leads").delete().eq("phone", phone_to_delete).execute()
        print("Lead eliminado.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
