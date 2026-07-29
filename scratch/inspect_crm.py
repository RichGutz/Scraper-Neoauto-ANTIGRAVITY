import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

lead_url = 'https://neoauto.com/auto/usado/subaru-crosstrek-2025-1874231'
response = supabase.table("crm_contactos").select("*").eq("url", lead_url).execute()
print(json.dumps(response.data, indent=2, default=str))
