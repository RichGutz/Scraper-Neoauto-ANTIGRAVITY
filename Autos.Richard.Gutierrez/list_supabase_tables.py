import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('whatsapp_bot/.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Listar todas las tablas
try:
    # Intentar obtener la lista de tablas consultando el esquema de información
    response = supabase.rpc('get_tables').execute()
    print("Tablas encontradas:")
    print(response.data)
except Exception as e:
    print(f"Error con RPC: {e}")
    print("\nIntentando método alternativo...")
    
    # Método alternativo: intentar consultar tablas conocidas
    tables_to_try = [
        'crm_leads', 'leads', 'contacts', 'whatsapp_leads', 
        'crm_contacts', 'neoauto_leads', 'autos_detalles_diarios',
        'crm_tasks', 'crm_messages'
    ]
    
    print("\nProbando tablas conocidas:")
    for table in tables_to_try:
        try:
            response = supabase.table(table).select('*').limit(1).execute()
            print(f"✓ {table} - EXISTE ({len(response.data)} registros de muestra)")
        except Exception as e:
            if 'does not exist' in str(e):
                print(f"✗ {table} - NO EXISTE")
            else:
                print(f"? {table} - Error: {e}")
