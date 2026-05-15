import os
import sys
import asyncio
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Import WhatsApp sender
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'whatsapp_bot'))
from whatsapp_sender import send_whatsapp_message

# --- CONFIGURATION & SETUP ---
load_dotenv()
SUPABASE_AUTOS_URL = os.environ.get("SUPABASE_URL")
SUPABASE_AUTOS_KEY = os.environ.get("SUPABASE_KEY")

def get_supabase_client():
    if not SUPABASE_AUTOS_URL or not SUPABASE_AUTOS_KEY:
        print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY for autos.")
        sys.exit(1)
    return create_client(SUPABASE_AUTOS_URL, SUPABASE_AUTOS_KEY)

# --- 1. DATA INPUT ---
def get_manual_input():
    print("=" * 60)
    print("🚗  ANALIZADOR MANUAL DE OFERTAS")
    print("=" * 60)
    print("\nPor favor ingresa los datos del vehículo (Presiona ENTER en la marca para cancelar):\n")
    make = input("   Marca (ej. Toyota): ").strip().capitalize()
    if not make: return None
    model = input("   Modelo (ej. Yaris): ").strip().upper()
    if not model: return None
    
    try:
        year = int(input("   Año (ej. 2018): ").strip())
        km = int(input("   Kilometraje: ").strip())
    except ValueError:
        print("❌ Error: Año y Kilometraje deben ser números enteros.")
        return None

    price_input = input("   Precio en USD (Opcional, deja vacío para obtener sugerencia): ").strip()
    price = None
    if price_input:
        try:
            price = float(price_input.replace(',', '').replace('$', ''))
        except ValueError:
            print("❌ Error: El precio debe ser un número válido.")
            return None

    trans_input = input("   Transmisión (M=Mecánica, A=Automática, Enter=Cualquiera): ").strip().upper()
    transmission = None
    if trans_input == 'M': transmission = "Mecánica"
    elif trans_input == 'A': transmission = "Automática"

    return {
        "Make": make,
        "Model": model,
        "Year": year,
        "Price": price,
        "Kilometers": km,
        "Transmission": transmission,
        "Source": "MANUAL DEAL"
    }

# --- 2. MARKET ANALYSIS ---
def fetch_market_context(supabase, make, model, year, transmission=None):
    query = supabase.table("autos_detalles_diarios") \
        .select("Price, Kilometers, Transmission") \
        .eq("Make", make) \
        .ilike("Model", f"%{model}%") \
        .eq("Year", year)
    
    if transmission:
        print(f"   (Filtrando por transmisión: {transmission})")
        query = query.eq("Transmission", transmission)
        
    response = query.execute()
    
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['Kilometers'] = pd.to_numeric(df['Kilometers'], errors='coerce')
        df = df.dropna(subset=['Price'])
    return df

def analyze_price(target_data, market_df):
    target_price = target_data['Price'] # Can be None
    target_km = target_data['Kilometers']
    target_trans = target_data.get('Transmission', 'Unknown')
    make = target_data['Make']
    model = target_data['Model']
    year = target_data['Year']
    
    if market_df.empty:
        print(f"\n[!] No hay datos historicos para {make} {model} {year} ({target_trans}).")
        return

    median_price = market_df['Price'].median()
    median_km = market_df['Kilometers'].median()
    count = len(market_df)
    
    diff_km = target_km - median_km
    pct_diff_km = (diff_km / median_km) * 100 if median_km > 0 else 0

    print("\n" + "="*60)
    print(f"MARKET ANALYSIS: {make} {model} {year}")
    print("="*60)
    print(f"   - Transmision: {target_trans}")
    if target_price is not None:
        print(f"   - Target Car:  ${target_price:,.0f} | {target_km:,.0f} km")
    else:
        print(f"   - Target Car:  Precio DESCONOCIDO | {target_km:,.0f} km")
    print(f"   - Mediana Mkt: ${median_price:,.0f} | {median_km:,.0f} km (Muestra: {count} unidades)")
    print("-" * 60)
    
    verdict = ""
    if target_price is not None:
        diff_price = target_price - median_price
        pct_diff_price = (diff_price / median_price) * 100
        
        if pct_diff_price < -5:
            verdict = f"GOOD DEAL (Precio es {abs(pct_diff_price):.1f}% DEBAJO del mercado)\n    Ahorro estimado: ${abs(diff_price):,.0f}"
        elif pct_diff_price > 5:
            verdict = f"BAD DEAL (Precio es {pct_diff_price:.1f}% SOBRE el mercado)\n    Sobreprecio de: ${diff_price:,.0f}"
        else:
            verdict = f"FAIR DEAL (Precio justo, dentro del {abs(pct_diff_price):.1f}% del mercado)"
    else:
        verdict = f"SUGERENCIA PRECIO JUSTO: Para que sea un trato justo, deberías apuntar a ${median_price:,.0f}\n"
        verdict += f"   * Buen trato: Menos de ${(median_price * 0.95):,.0f}\n"
        verdict += f"   * Mal trato: Mas de ${(median_price * 1.05):,.0f}"

    print(verdict)
    
    # KM Warning
    km_note = ""
    if diff_km > 10000:
        km_note = f"[!] ALTO KILOMETRAJE (+{diff_km:,.0f} km vs promedio)"
        print(km_note)
    elif diff_km < -10000:
        km_note = f"[*] BAJO KILOMETRAJE ({diff_km:,.0f} km vs promedio)"
        print(km_note)
    
    print("="*60 + "\n")
    
    # Opcional: Enviar por WhatsApp
    enviar = input("¿Deseas enviarte este reporte por WhatsApp? (S/N): ").strip().upper()
    if enviar == 'S':
        price_line = f"💰 ${target_price:,.0f} | 🛣️ {target_km:,.0f} km" if target_price else f"💰 SIN PRECIO | 🛣️ {target_km:,.0f} km"
        
        whatsapp_msg = f"""🚗 *ANÁLISIS MANUAL*
{make} {model} {year} ({target_trans})
{price_line}

{verdict}
Mercado: ${median_price:,.0f} | {median_km:,.0f} km (base: {count} un.)
{km_note}"""
        
        try:
            success = send_whatsapp_message("991090016", whatsapp_msg, silent=True)
            if success:
                print("📱 Resultado enviado a WhatsApp exitosamente.")
            else:
                print("⚠️ No se pudo enviar WhatsApp.")
        except Exception as e:
            print(f"⚠️ Error al enviar WhatsApp: {e}")

# --- MAIN LOOP ---
def main():
    data = get_manual_input()
    if not data:
        print("\nCancelado.")
        return

    supabase = get_supabase_client()
    market_df = fetch_market_context(
        supabase, 
        data['Make'], 
        data['Model'], 
        data['Year'], 
        transmission=data.get('Transmission')
    )
    analyze_price(data, market_df)

if __name__ == "__main__":
    main()
