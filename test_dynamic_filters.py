import os
from dotenv import load_dotenv
from supabase import create_client
import sys

sys.path.append(os.path.dirname(__file__))
from CRM_NEOAUTO.Market_Research.dynamic_filters import fetch_market_data, get_models_by_brand

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

models = get_models_by_brand(supabase, "Mazda")
print(f"Modelos de Mazda disponibles (mostrados en app):")
for m in models:
    if "CX" in m:
        print(f" - {m}")

print("\nConsultando mercado para Mazda CX 9 2013...")
# Simulamos que el usuario seleccionó "CX 9"
data = fetch_market_data(supabase, "Mazda", "CX 9", 2013)

print(f"\nSe encontraron {len(data)} vehículos únicos para Mazda CX 9 2013.")
if len(data) > 0:
    print("Primeros 3 resultados:")
    for d in data[:3]:
        print(f" - {d.get('URL')} | Precio: {d.get('Price')} | KM: {d.get('Kilometers')}")
