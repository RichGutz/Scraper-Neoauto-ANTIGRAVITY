import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

resp = supabase.table("autos_detalles").select("*").eq("URL", "https://neoauto.com/auto/usado/mazda-cx-9-2013-1832935").execute()
print("Data for URL 1832935:")
for r in resp.data:
    print(r)

resp2 = supabase.table("autos_detalles").select("*").eq("URL", "https://neoauto.com/auto/usado/mazda-cx-9-2013-1801886").execute()
print("\nData for URL 1801886:")
for r in resp2.data:
    print(r)
