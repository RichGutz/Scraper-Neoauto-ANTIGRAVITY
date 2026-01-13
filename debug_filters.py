import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client

# Load credentials
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Configuration
MAX_AGE_YEARS = 10
DAYS_BACK = 30
TARGET_BRANDS = [
    # Japanese
    "TOYOTA", "HONDA", "NISSAN", "MAZDA", "SUBARU", "SUZUKI", "MITSUBISHI", "LEXUS", "INFINITI", "ACURA",
    # Korean
    "KIA", "HYUNDAI", "GENESIS", "SSANGYONG",
    # American
    "CHEVROLET", "FORD", "JEEP", "DODGE", "CHRYSLER", "RAM", "GMC", "CADILLAC", "LINCOLN", "TESLA", "BUICK",
    # German
    "BMW", "MERCEDES-BENZ", "AUDI", "VOLKSWAGEN", "PORSCHE"
]

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_data(supabase):
    print("Fetching data from Supabase...")
    response = supabase.table("autos_detalles_diarios").select("*").order("DateTime", desc=True).execute()
    data = response.data
    df = pd.DataFrame(data)
    print(f"Fetched {len(df)} initial records.")
    return df

def debug_filter_data(df):
    if df.empty:
        return df
    
    print("\n--- DEBUG FILTERING ---")
    print(f"Initial count: {len(df)}")
    
    current_year = datetime.now().year
    min_year = current_year - MAX_AGE_YEARS
    
    # 1. Age Filter
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df[df['Year'] >= min_year]
    print(f"After Age filter ({min_year}+): {len(df)}")
    
    # 2. Brand Filter
    df.loc[:, 'Make'] = df['Make'].str.upper().str.strip()
    df = df[df['Make'].isin(TARGET_BRANDS)]
    print(f"After Brand filter: {len(df)}")
    
    # 3. Date Filter (Last 30 Days)
    print("Converting DateTime...")
    df.loc[:, 'DateTime'] = pd.to_datetime(df['DateTime'], format='mixed', utc=True, errors='coerce')
    print(f"Valid DateTime rows: {df['DateTime'].notnull().sum()}")
    
    if not df.empty:
        print(f"Date range in data: {df['DateTime'].min()} to {df['DateTime'].max()}")
    
    df = df.dropna(subset=['DateTime'])
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
        print(f"Cutoff date (UTC): {cutoff_date}")
        df_date = df[df['DateTime'] >= cutoff_date]
        print(f"After Date filter (UTC): {len(df_date)}")
        df = df_date
    except Exception as e:
        print(f"Date filter error: {e}. Trying naive datetime.")
        df['DateTime'] = df['DateTime'].dt.tz_localize(None)
        cutoff_date = datetime.now() - timedelta(days=DAYS_BACK)
        print(f"Cutoff date (Naive): {cutoff_date}")
        df = df[df['DateTime'] >= cutoff_date]
        print(f"After Date filter (Naive): {len(df)}")

    # 4. Transmission Filter (Exclude Mecanica)
    if 'Transmission' in df.columns:
        df = df[~df['Transmission'].astype(str).str.contains('Mecánica|Mecanica|Manual', case=False, na=False)]
    print(f"After Transmission filter: {len(df)}")

    # 5. Fuel Filter
    if 'Fuel Type' in df.columns:
        df = df[df['Fuel Type'] == 'Gasolina']
    print(f"After Fuel filter: {len(df)}")

    # 6. Single Owner Filter
    if 'unico_dueno' in df.columns:
        df = df[df['unico_dueno'] == True]
    print(f"After Single Owner filter: {len(df)}")

    # 7. Vehicle Type Filter (Pickup)
    if 'Model' in df.columns:
        df = df[df['Model'].str.contains('PICKUP', case=False, na=False)]
    print(f"After Model (PICKUP) filter: {len(df)}")
    
    return df

if __name__ == "__main__":
    supabase = get_supabase_client()
    df = fetch_data(supabase)
    debug_filter_data(df)
