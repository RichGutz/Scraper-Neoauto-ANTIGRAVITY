
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

supabase = init_db()

# Obtener los últimos 20 mensajes
msgs = supabase.table("crm_messages").select("id").order("timestamp", desc=True).limit(20).execute()
ids = [m['id'] for m in msgs.data]

if ids:
    supabase.table("crm_messages").update({"processed": False}).in_("id", ids).execute()
    print(f"Reseteados {len(ids)} mensajes a processed=False")
else:
    print("No hay mensajes para resetear")
