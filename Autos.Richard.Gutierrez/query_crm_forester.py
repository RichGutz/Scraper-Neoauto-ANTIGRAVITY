import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('whatsapp_bot/.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Buscar leads con "forester" en el URL
response = supabase.table('crm_leads').select('name, phone, car_url').ilike('car_url', '%forester%').execute()

print(f"\nEncontrados {len(response.data)} leads con 'forester' en el URL:\n")
for lead in response.data:
    print(f"Nombre: {lead['name']}")
    print(f"Teléfono: {lead['phone']}")
    print(f"URL: {lead['car_url']}")
    print("-" * 60)
