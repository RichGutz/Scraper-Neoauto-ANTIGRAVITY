import os
import sys
import asyncio
import pandas as pd
import re
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright
import random

# Import WhatsApp sender
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'whatsapp_bot'))
from whatsapp_sender import send_whatsapp_message

# --- CONFIGURATION & SETUP ---
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY.")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 1. DATA RETRIEVAL (DB or SCRAPE) ---

def get_details_from_db(supabase, url):
    print(f"🔍 Checking database for: {url}")
    response = supabase.table("autos_detalles_diarios").select("*").eq("URL", url).execute()
    if response.data:
        data = response.data[0]
        # Normalize keys/types
        return {
            "Make": data.get("Make"),
            "Model": data.get("Model"),
            "Year": int(data.get("Year")) if data.get("Year") else None,
            "Price": float(data.get("Price")) if data.get("Price") else 0.0,
            "Kilometers": int(data.get("Kilometers")) if data.get("Kilometers") else 0,
            "Source": "DATABASE"
        }
    return None

async def scrape_neoauto_details(url):
    print("🕸️ URL not in DB. Scraping Neoauto (Stealth Mode)...")
    data = None
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            content = await page.content()
            
            # Basic WAF/Error detection
            if "blocked" in content.lower() or "error" in await page.title():
                print("❌ Blocked by WAF or Error loading page.")
                return None

            # --- Extract Data using Selectors ---
            # Title usually contains Make Model Year
            title = await page.title() # e.g. "Subaru Forester 2018 - NeoAuto"
            
            # Extract basic info from specific Neoauto selectors (heuristic)
            # This is simplified; accurate extraction depends on current DOM
            
            # Try to find Make/Model/Year from Title first
            # "Vendo Subaru Forester 2018..."
            
            make = "Desconocido"
            model = "Desconocido"
            year = 0
            price = 0.0
            km = 0
            
            # Attempt Regex on Title/Header
            h1 = await page.inner_text("h1")
            
            # Extract Price
            try:
                price_text = await page.locator(".price, .c-price").first.inner_text()
                price_text = price_text.replace("US$", "").replace("$", "").replace(",", "").strip()
                price = float(price_text)
            except:
                pass
                
            # Extract Year, Km from technical sheet if available
            # This part is tricky without robust selectors, we'll try best effor regex on body
            body_text = await page.inner_text("body")
            
            year_match = re.search(r'Año[:\s]+(\d{4})', body_text)
            if year_match: year = int(year_match.group(1))
            
            km_match = re.search(r'Kilometraje[:\s]+([\d,]+)', body_text)
            if km_match: km = int(km_match.group(1).replace(",", ""))

            # Identify Make (Simple list check)
            makes = ["SUBARU", "TOYOTA", "HONDA", "NISSAN", "BMW", "MERCEDES", "KIA", "HYUNDAI", "FORD"]
            for m in makes:
                if m in h1.upper():
                    make = m.capitalize()
                    break
            
            # Identify Model (Remove Make and Year from H1)
            model = h1.upper().replace(make.upper(), "").replace(str(year), "").strip()
            
            data = {
                "Make": make,
                "Model": model,
                "Year": year,
                "Price": price,
                "Kilometers": km,
                "Source": "SCRAPED"
            }
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
        finally:
            await browser.close()
            
    return data

def get_manual_input():
    print("\n⚠️  Could not retrieve data automatically (or not supported source).")
    print("   Please enter details manually:")
    make = input("   Make (e.g. Subaru): ").strip()
    model = input("   Model (e.g. Forester): ").strip()
    year = int(input("   Year (e.g. 2018): ").strip())
    price = float(input("   Price (USD): ").strip())
    km = int(input("   Kilometers: ").strip())
    return {
        "Make": make,
        "Model": model,
        "Year": year,
        "Price": price,
        "Kilometers": km,
        "Source": "MANUAL"
    }

# --- 2. MARKET ANALYSIS ---

def fetch_market_context(supabase, make, model, year):
    # Fetch comparative data
    response = supabase.table("autos_detalles_diarios") \
        .select("Price, Kilometers") \
        .eq("Make", make) \
        .ilike("Model", f"%{model}%") \
        .eq("Year", year) \
        .execute()
    
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['Kilometers'] = pd.to_numeric(df['Kilometers'], errors='coerce')
        df = df.dropna(subset=['Price'])
    return df

def analyze_price(target_data, market_df, url=None):
    target_price = target_data['Price']
    target_km = target_data['Kilometers']
    make = target_data['Make']
    model = target_data['Model']
    year = target_data['Year']
    
    if market_df.empty:
        print(f"\n⚠️  No historical data found for {make} {model} {year} to compare.")
        return

    median_price = market_df['Price'].median()
    median_km = market_df['Kilometers'].median()
    count = len(market_df)
    
    diff_price = target_price - median_price
    pct_diff_price = (diff_price / median_price) * 100
    
    diff_km = target_km - median_km
    pct_diff_km = (diff_km / median_km) * 100 if median_km > 0 else 0

    print("\n" + "="*60)
    print(f"📊  MARKET ANALYSIS: {make} {model} {year}")
    print("="*60)
    print(f"   ► Data Source: {target_data['Source']}")
    print(f"   ► Target Car:  ${target_price:,.0f} | {target_km:,.0f} km")
    print(f"   ► Market Median: ${median_price:,.0f} | {median_km:,.0f} km (Based on {count} units)")
    print("-" * 60)
    
    # VERDICT
    verdict = ""
    if pct_diff_price < -5:
        verdict = f"✅ GOOD DEAL ({abs(pct_diff_price):.1f}% BELOW market)"
        print(f"✅  VERDICT: GOOD DEAL (Price is {abs(pct_diff_price):.1f}% BELOW market)")
        print(f"    You save: ${abs(diff_price):,.0f} vs Median")
    elif pct_diff_price > 5:
        verdict = f"❌ BAD DEAL ({pct_diff_price:.1f}% ABOVE market)"
        print(f"❌  VERDICT: BAD DEAL (Price is {pct_diff_price:.1f}% ABOVE market)")
        print(f"    Overpriced by: ${diff_price:,.0f}")
    else:
        verdict = f"⚖️ FAIR DEAL ({abs(pct_diff_price):.1f}% of market)"
        print(f"⚖️  VERDICT: FAIR DEAL (Price is within {abs(pct_diff_price):.1f}% of market)")
    
    # KM Warning
    km_note = ""
    if diff_km > 10000:
        km_note = f" ⚠️ Alto kilometraje (+{diff_km:,.0f} km vs avg)"
        print(f"⚠️  WARNING: High Mileage! (+{diff_km:,.0f} km vs avg)")
    elif diff_km < -10000:
        km_note = f" 💎 Bajo kilometraje ({diff_km:,.0f} km vs avg)"
        print(f"💎  PLUS: Low Mileage! ({diff_km:,.0f} km vs avg)")
    
    print("="*60 + "\n")
    
    # Send WhatsApp notification
    if url:
        whatsapp_msg = f"""🚗 *ANÁLISIS DE LEAD*

{make} {model} {year}
💰 ${target_price:,.0f} | 🛣️ {target_km:,.0f} km

{verdict}
Mercado: ${median_price:,.0f} | {median_km:,.0f} km{km_note}

🔗 {url}"""
        
        try:
            success = send_whatsapp_message("991090016", whatsapp_msg, silent=True)
            if success:
                print("📱 Resultado enviado a WhatsApp")
            else:
                print("⚠️ No se pudo enviar WhatsApp (revisa que Chrome esté cerrado)")
        except Exception as e:
            print(f"⚠️ Error al enviar WhatsApp: {e}")
    target_price = target_data['Price']
    target_km = target_data['Kilometers']
    make = target_data['Make']
    model = target_data['Model']
    year = target_data['Year']
    
    if market_df.empty:
        print(f"\n⚠️  No historical data found for {make} {model} {year} to compare.")
        return

    median_price = market_df['Price'].median()
    median_km = market_df['Kilometers'].median()
    count = len(market_df)
    
    diff_price = target_price - median_price
    pct_diff_price = (diff_price / median_price) * 100
    
    diff_km = target_km - median_km
    pct_diff_km = (diff_km / median_km) * 100 if median_km > 0 else 0

    print("\n" + "="*60)
    print(f"📊  MARKET ANALYSIS: {make} {model} {year}")
    print("="*60)
    print(f"   ► Data Source: {target_data['Source']}")
    print(f"   ► Target Car:  ${target_price:,.0f} | {target_km:,.0f} km")
    print(f"   ► Market Median: ${median_price:,.0f} | {median_km:,.0f} km (Based on {count} units)")
    print("-" * 60)
    
    # VERDICT
    verdict = ""
    if pct_diff_price < -5:
        verdict = f"✅ GOOD DEAL ({abs(pct_diff_price):.1f}% BELOW market)"
        print(f"✅  VERDICT: GOOD DEAL (Price is {abs(pct_diff_price):.1f}% BELOW market)")
        print(f"    You save: ${abs(diff_price):,.0f} vs Median")
    elif pct_diff_price > 5:
        verdict = f"❌ BAD DEAL ({pct_diff_price:.1f}% ABOVE market)"
        print(f"❌  VERDICT: BAD DEAL (Price is {pct_diff_price:.1f}% ABOVE market)")
        print(f"    Overpriced by: ${diff_price:,.0f}")
    else:
        verdict = f"⚖️ FAIR DEAL ({abs(pct_diff_price):.1f}% of market)"
        print(f"⚖️  VERDICT: FAIR DEAL (Price is within {abs(pct_diff_price):.1f}% of market)")
    
    # KM Warning
    km_note = ""
    if diff_km > 10000:
        km_note = f" ⚠️ Alto kilometraje (+{diff_km:,.0f} km vs avg)"
        print(f"⚠️  WARNING: High Mileage! (+{diff_km:,.0f} km vs avg)")
    elif diff_km < -10000:
        km_note = f" 💎 Bajo kilometraje ({diff_km:,.0f} km vs avg)"
        print(f"💎  PLUS: Low Mileage! ({diff_km:,.0f} km vs avg)")
    
    print("="*60 + "\n")
    
    # Send WhatsApp notification
    if url:
        whatsapp_msg = f"""🚗 *ANÁLISIS DE LEAD*

{make} {model} {year}
💰 ${target_price:,.0f} | 🛣️ {target_km:,.0f} km

{verdict}
Mercado: ${median_price:,.0f} | {median_km:,.0f} km{km_note}

🔗 {url}"""
        
        try:
            success = send_whatsapp_message("991090016", whatsapp_msg, silent=True)
            if success:
                print("📱 Resultado enviado a WhatsApp")
            else:
                print("⚠️ No se pudo enviar WhatsApp (revisa que Chrome esté cerrado)")
        except Exception as e:
            print(f"⚠️ Error al enviar WhatsApp: {e}")

# --- MAIN LOOP ---

async def main_async():
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    if not url:
        print("\n🚗  CRM LEAD ANALYZER v1.0")
        url = input("👉  Paste Neoauto URL (or 'exit'): ").strip()
    
    if url.lower() in ['exit', 'quit']:
        return

    supabase = get_supabase_client()
    
    # 1. Get Details
    data = get_details_from_db(supabase, url)
    
    if not data:
        if "neoauto.com" in url:
            data = await scrape_neoauto_details(url)
            if not data or data['Year'] == 0:
                print("   (Scraping incomplete, falling back to manual input)")
                data = get_manual_input()
        else:
            print("   (Non-Neoauto URL detected, requesting manual input)")
            data = get_manual_input()

    if not data:
        print("❌ Could not get car data.")
        return

    # 2. Analyze
    market_df = fetch_market_context(supabase, data['Make'], data['Model'], data['Year'])
    analyze_price(data, market_df, url)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
