
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    response = supabase.table("autos_detalles_diarios").select("*").limit(1).execute()
    if response.data:
        print("Columns found:")
        for key in response.data[0].keys():
            print(f"- {key}")
        print("\nSample Data:")
        print(response.data[0])
    else:
        print("Table is empty or not accessible.")
except Exception as e:
    print(f"Error: {e}")
