"""
Ver exactamente qué nombres están guardados en Supabase
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables
current_script_dir = Path(__file__).resolve().parent
dotenv_path = current_script_dir / ".env"
load_dotenv(dotenv_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("=== NOMBRES EN SUPABASE ===\n")

response = supabase.table("crm_leads").select("*").execute()

for lead in response.data:
    print(f"Nombre: '{lead['name']}'")
    print(f"Teléfono: {lead['phone']}")
    print(f"URL: {lead.get('car_url', 'N/A')[:50]}...")
    print()
