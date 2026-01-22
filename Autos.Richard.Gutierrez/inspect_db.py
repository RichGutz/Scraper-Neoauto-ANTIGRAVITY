
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get the specific car to see its columns
url = "https://neoauto.com/auto/usado/hyundai-tucson-2019-1861634"
print(f"Checking columns for: {url}")
response = supabase.table("autos_detalles_diarios").select("*").eq("URL", url).execute()

if response.data:
    row = response.data[0]
    print("Columns found:", row.keys())
    print("Values:", row)
else:
    print("Car not found in DB.")
