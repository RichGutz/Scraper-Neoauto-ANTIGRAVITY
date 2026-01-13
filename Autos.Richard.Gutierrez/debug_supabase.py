import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print(f"URL: {SUPABASE_URL}")
# Do not print KEY for security

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Fetching first 5 records...")
response = supabase.table("autos_detalles_diarios").select("*").limit(5).execute()

data = response.data
print(f"Count: {len(data)}")
if data:
    print("First record keys:", data[0].keys())
    print("First record sample:", data[0])
    
    # Check distinct makes
    print("Checking unique Makes...")
    res_makes = supabase.table("autos_detalles_diarios").select("Make").limit(100).execute()
    makes = set([r['Make'] for r in res_makes.data])
    print("Sample Makes:", makes)
else:
    print("Table is empty or access denied.")
