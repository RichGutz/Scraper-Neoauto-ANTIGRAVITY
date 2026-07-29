import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

lead_url = 'https://neoauto.com/auto/usado/subaru-crosstrek-2025-1874231'

# 1. Fetch current record
response = supabase.table("crm_contactos").select("*").eq("url", lead_url).execute()
if len(response.data) == 0:
    print("Record not found.")
    exit(1)

record = response.data[0]
notas = record.get("notas_actividad", {})
if not isinstance(notas, dict):
    notas = {}

# 2. Update notas and estado
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
notas["Estado 6: Vendido"] = f"{now_str} - Revertido manualmente a Estado 6 por solicitud (posible bug en UI al editar)."

update_payload = {
    "estado_embudo": "Estado 6: Vendido",
    "notas_actividad": notas
}

update_resp = supabase.table("crm_contactos").update(update_payload).eq("url", lead_url).execute()

print("Reversión a Vendido exitosa. Datos nuevos:")
print(json.dumps(update_resp.data, indent=2, default=str))
