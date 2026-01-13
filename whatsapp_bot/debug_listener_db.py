
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
    print("=" * 60)
    print("DIAGNOSTICO DE BASE DE DATOS")
    print("=" * 60)
    
    supabase = init_db()
    
    # 1. Contar Leads
    leads = supabase.table("crm_leads").select("*", count="exact").execute()
    print(f"Total Leads: {len(leads.data)}")
    for l in leads.data:
        print(f" - {l['name']} ({l['phone']})")
        
    print("-" * 30)
    
    # 2. Contar Mensajes
    msgs = supabase.table("crm_messages").select("*", count="exact").execute()
    print(f"Total Mensajes: {len(msgs.data)}")
    
    # 3. Contar Mensajes NO procesados
    unprocessed = supabase.table("crm_messages").select("*", count="exact").eq("processed", False).execute()
    print(f"Mensajes NO procesados (pendientes): {len(unprocessed.data)}")
    
    if len(unprocessed.data) > 0:
        print("Ejemplos de pendientes:")
        for m in unprocessed.data[:5]:
            print(f" - [{m['lead_phone']}] {m['content'][:30]}...")

if __name__ == "__main__":
    main()
