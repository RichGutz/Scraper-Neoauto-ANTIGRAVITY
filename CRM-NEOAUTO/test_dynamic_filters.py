import os
from dotenv import load_dotenv
from supabase import create_client
import sys

sys.path.append(os.path.dirname(__file__))
from Market_Research.dynamic_filters import fetch_market_data, get_models_by_brand

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

models = get_models_by_brand(supabase, "Mazda")
print(f"Modelos de Mazda disponibles (mostrados en app):")
for m in models:
    if "CX" in m:
        print(f" - {m}")

print("\nConsultando mercado para Mazda CX 9 2013...")
data = fetch_market_data(supabase, "Mazda", "CX 9", 2013)

print(f"\nSe encontraron {len(data)} vehículos únicos para Mazda CX 9 2013.")
if len(data) > 0:
    print("Resultados devueltos:")
    for d in data:
        print(f" - {d.get('URL')} | Precio: {d.get('Price')} | KM: {d.get('Kilometers')} | Modelo Orig: {d.get('Model')}")
