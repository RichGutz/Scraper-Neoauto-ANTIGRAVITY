import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Load credentials
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_market_data(supabase, make, model, year):
    print(f"Fetching market data for {make} {model} {year}...")
    
    # Fetch data for the specific model and year (and adjacent years for better context if needed)
    # We will fetch exact year first.
    response = supabase.table("autos_detalles_diarios") \
        .select("Price, Kilometers, Year, URL, DateTime") \
        .eq("Make", make) \
        .ilike("Model", f"%{model}%") \
        .eq("Year", year) \
        .execute()
    
    df = pd.DataFrame(response.data)
    
    if df.empty:
        print(f"No data found for {year}. Trying broader search...")
        return pd.DataFrame()
        
    # Clean price
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df = df.dropna(subset=['Price'])
    return df

def evaluate_deal(make, model, year, target_price, target_km=None):
    supabase = get_supabase_client()
    df = fetch_market_data(supabase, make, model, year)
    
    if df.empty:
        print("Not enough data to evaluate.")
        return

    # Statistics
    market_median = df['Price'].median()
    market_mean = df['Price'].mean()
    market_min = df['Price'].min()
    market_max = df['Price'].max()
    count = len(df)
    
    print(f"\n--- MARKET ANALYSIS: {make} {model} {year} ---")
    print(f"Sample Size: {count} vehicles")
    print(f"Market Range: ${market_min:,.0f} - ${market_max:,.0f}")
    print(f"Median Price: ${market_median:,.0f}")
    print(f"Mean Price:   ${market_mean:,.0f}")
    
    # Valuation
    diff = target_price - market_median
    percent_diff = (diff / market_median) * 100
    
    print(f"\n--- VALUATION FOR TARGET (${target_price:,.0f}) ---")
    if percent_diff < -5:
        print(f"✅ GOOD DEAL! Price is {abs(percent_diff):.1f}% BELOW market median.")
        print(f"   You save approx: ${abs(diff):,.0f}")
    elif percent_diff > 5:
        print(f"❌ BAD DEAL. Price is {percent_diff:.1f}% ABOVE market median.")
        print(f"   Overpriced by approx: ${diff:,.0f}")
    else:
        print(f"⚖️ FAIR DEAL. Price is within market average ({percent_diff:.1f}%).")

    # KM analysis if provided
    if target_km:
         market_km_median = pd.to_numeric(df['Kilometers'], errors='coerce').median()
         print(f"\n   Market Median KM: {market_km_median:,.0f} km")
         print(f"   Target KM: {target_km:,.0f} km")


def main():
    print("Evaluating Subaru Forester Leads...\n")
    
    # Lead 1: 2018 Forester - $16,500 - 85,000km (From previous log)
    evaluate_deal("Subaru", "Forester", 2018, 16500, 85000)
    
    print("\n" + "="*50 + "\n")
    
    # Lead 2: 2023 Forester - $27,500 - 44,000km (From previous log)
    evaluate_deal("Subaru", "Forester", 2023, 27500, 44000)

if __name__ == "__main__":
    main()
