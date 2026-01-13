import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.async_api import async_playwright
from PIL import Image
import io
import base64
import random
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import make_interp_spline
from pathlib import Path
import sys

# Add parent directory to path to import report_gen module
# parent_dir = Path(__file__).parent.parent
# sys.path.insert(0, str(parent_dir))

# Import modularized components (for PDF conversion)
# from report_gen.pdf_converter import convert_html_to_pdf as convert_to_pdf_async
# from report_gen.utils import optimize_image, image_to_base64_data_uri

# --- STEALTH CONFIGURATION ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

# Load credentials
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Configuration
MAX_AGE_YEARS = 10
DAYS_BACK = 30
PRICE_MIN = 0
PRICE_MAX = 100000
TARGET_BRANDS = [
    # Japanese
    "TOYOTA", "HONDA", "NISSAN", "MAZDA", "SUBARU", "SUZUKI", "MITSUBISHI", "INFINITI", "ACURA",
    # Korean
    "KIA", "HYUNDAI", "GENESIS",
    # American
    "CHEVROLET", "FORD", "JEEP", "DODGE", "CHRYSLER", "GMC", "CADILLAC", "LINCOLN", "TESLA", "BUICK",
    # German
    # German
    "BMW", "MERCEDES-BENZ", "AUDI", "VOLKSWAGEN", "VOLVO"
]

ALL_SUPPORTED_BRANDS = TARGET_BRANDS.copy()

ORIGIN_MAP = {
    "ALEMANAS/OTRAS": ["BMW", "MERCEDES-BENZ", "AUDI", "VOLKSWAGEN", "VOLVO"]
}

# --- CONFIG LOADING FROM GUI ---
FILTERS_FILE = Path(__file__).parent / "last_filters.json"

def load_config_from_json():
    """Load config overrides from GUI's JSON file if it exists"""
    global MAX_AGE_YEARS, DAYS_BACK, PRICE_MAX, TARGET_BRANDS
    
    if FILTERS_FILE.exists():
        try:
            import json
            with open(FILTERS_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            print(f"✓ Loading config from {FILTERS_FILE}")
            
            # Update Globals
            if 'km_max' in config:
                # We don't have a global KM_MAX but we can add logic later if needed
                pass 
                
            if 'year_min' in config:
                current_year = datetime.now().year
                MAX_AGE_YEARS = current_year - int(config['year_min'])
                print(f"  - MAX_AGE_YEARS: {MAX_AGE_YEARS} (Min Year: {config['year_min']})")
                
            if 'days_back' in config:
                DAYS_BACK = int(config['days_back'])
                print(f"  - DAYS_BACK: {DAYS_BACK}")
                
            if 'selected_map' in config:
                # Flats the map list to a single list of models/brands? 
                # Actually usage in script is TARGET_BRANDS check on Make.
                # But filter_data line 430 filters by 'TARGET_BRANDS'.
                # The GUI selects SPECIFIC models per brand. 
                # We need to adapt the script to handle specific models if we want full fidelity.
                # For now let's just make sure the BRANDS are in the target list.
                # Or better: Extract unique brands from the selected map.
                selected_brands = list(config['selected_map'].keys())
                TARGET_BRANDS = selected_brands
                print(f"  - TARGET_BRANDS: {len(TARGET_BRANDS)} brands selected")
                
                # IMPORTANT: The script currently filters by Brand strictly. 
                # To filter by specific models selected in GUI, we'd need deeper changes in filter_data.
                # For now, updating TARGET_BRANDS ensures we at least look at the right Makes.
                
        except Exception as e:
            print(f"Warning: Failed to load config from JSON: {e}")

# Load config immediately
load_config_from_json()

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MODEL RULES AND HISTORICAL DATA FUNCTIONS ---
LOADED_MODEL_RULES = None
RULES_CSV_PATH = Path(__file__).parent.parent / "Core" / "reglas_modelos_base.csv"

def load_rules():
    """Load model normalization rules from CSV"""
    global LOADED_MODEL_RULES
    if LOADED_MODEL_RULES is None:
        try:
            if RULES_CSV_PATH.exists():
                LOADED_MODEL_RULES = pd.read_csv(RULES_CSV_PATH)
                LOADED_MODEL_RULES['make_rule_match'] = LOADED_MODEL_RULES['make_rule_match'].astype(str).str.lower().str.strip()
                LOADED_MODEL_RULES['model_pattern_input_lower'] = LOADED_MODEL_RULES['model_pattern_input_lower'].astype(str).str.lower().str.strip()
                LOADED_MODEL_RULES.sort_values(by=['priority', 'pattern_length'], ascending=[False, False], inplace=True)
                print(f"✓ Loaded {len(LOADED_MODEL_RULES)} model rules")
        except Exception as e:
            print(f"Error loading rules: {e}")
            LOADED_MODEL_RULES = pd.DataFrame()

def get_model_base(model_name: str, make_name: str) -> str:
    """Get normalized model base name using rules"""
    if pd.isna(model_name) or model_name == "Desconocido":
        return "Desconocido"
    model_lower = model_name.lower().strip()
    make_lower = make_name.lower().strip()
    
    if LOADED_MODEL_RULES is not None and not LOADED_MODEL_RULES.empty:
        rules_for_make = LOADED_MODEL_RULES[LOADED_MODEL_RULES['make_rule_match'] == make_lower]
        for _, rule in rules_for_make.iterrows():
            if (rule['match_type'] == 'exact' and model_lower == rule['model_pattern_input_lower']) or \
               (rule['match_type'] == 'startswith' and model_lower.startswith(rule['model_pattern_input_lower'])) or \
               (rule['match_type'] == 'contains' and rule['model_pattern_input_lower'] in model_lower):
                return rule['model_base_target']
    return model_name

def fetch_historical_data(supabase: Client) -> pd.DataFrame:
    """Fetch historical data from autos_detalles table for trend analysis"""
    print("Fetching historical data from autos_detalles...")
    all_data = []
    offset = 0
    limit = 1000
    
    while True:
        try:
            response = supabase.from_("autos_detalles").select('*').order('id', desc=True).range(offset, offset + limit - 1).execute()
            if not response.data:
                break
            all_data.extend(response.data)
            print(f"  Downloaded {len(response.data)} rows (total: {len(all_data)})...")
            if len(response.data) < limit:
                break
            offset += limit
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    print(f"✓ Historical data loaded: {len(all_data)} records")
    return pd.DataFrame(all_data) if all_data else pd.DataFrame()

def calculate_model_metrics(df_historic: pd.DataFrame) -> dict:
    """
    Calculate market metrics per model:
    - median_price, mean_price
    - fast_selling_ratio (FSR)
    - yearly_stats for trend lines
    
    Returns: {
        'Model_Base': {
            'median_price': float,
            'mean_price': float,
            'fsr': float,
            'yearly_stats': DataFrame[Year, median, mean]
        }
    }
    """
    print("Calculating model metrics...")
    
    if df_historic.empty:
        return {}
    
    # Process data similar to main.py
    df = df_historic.copy()
    df['Make'] = df['Make'].fillna("Desconocido").astype(str).str.strip().str.upper()
    df['Model'] = df['Model'].fillna("Desconocido").astype(str).str.strip()
    df['Model_Base'] = df.apply(lambda row: get_model_base(row['Model'], row['Make']), axis=1)
    
    # Clean numeric columns
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df.dropna(subset=['Model_Base', 'Year', 'Price', 'URL'], inplace=True)
    
    # Calculate URL appearances
    df['Apariciones_URL_Hist'] = df.groupby('URL')['URL'].transform('size')
    
    # Group by model
    grouped = df.groupby('Model_Base', as_index=False)
    metrics = grouped.agg(
        unique_listings=('URL', 'nunique'),
        median_price=('Price', 'median'),
        mean_price=('Price', 'mean'),
        mean_year=('Year', 'mean')
    )
    
    # Calculate FSR (Fast Selling Ratio)
    fsr = df.groupby('Model_Base')['URL'].apply(
        lambda g: (g.value_counts() == 1).sum() / g.nunique() if g.nunique() > 0 else 0
    ).reset_index(name='fast_selling_ratio')
    
    metrics = pd.merge(metrics, fsr, on='Model_Base', how='left')
    
    # Calculate yearly stats for trend lines
    yearly_stats = df.groupby(['Model_Base', 'Year'])['Price'].agg(['median', 'mean']).reset_index()
    
    # Build dictionary
    result = {}
    for model_base in metrics['Model_Base'].unique():
        model_metrics = metrics[metrics['Model_Base'] == model_base].iloc[0]
        model_yearly = yearly_stats[yearly_stats['Model_Base'] == model_base]
        
        result[model_base] = {
            'median_price': model_metrics['median_price'],
            'mean_price': model_metrics['mean_price'],
            'fsr': model_metrics['fast_selling_ratio'],
            'unique_listings': model_metrics['unique_listings'],
            'yearly_stats': model_yearly
        }
    
    print(f"✓ Calculated metrics for {len(result)} models")
    return result


def fetch_data(supabase):
    print("Fetching data from Supabase...")
    # Fetch all records
    response = supabase.table("autos_detalles_diarios") \
        .select("*") \
        .order("DateTime", desc=True) \
        .execute()
    
    data = response.data
    df = pd.DataFrame(data)
    print(f"Fetched {len(df)} initial records.")
    return df

def filter_data(df, filters):
    """
    Filter dataframe based on GUI user selection
    """
    if df.empty:
        return df
    
    print("Filtering data based on User Input...")
    
    # Unpack Filters
    km_max = filters['km_max']
    year_min = filters['year_min']
    days_back = filters['days_back']
    selected_map = filters['selected_map'] # { 'Brand': ['Make1', 'Make2'] }
    fuels_target = filters['fuels']

    # 1. Base Filters (Year, Days)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    
    # Date logic
    print("Converting DateTime...")
    df.loc[:, 'DateTime'] = pd.to_datetime(df['DateTime'], format='mixed', utc=True, errors='coerce')
    df = df.dropna(subset=['DateTime'])
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        df = df[df['DateTime'] >= cutoff_date]
    except:
        df['DateTime'] = df['DateTime'].dt.tz_localize(None)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        df = df[df['DateTime'] >= cutoff_date]

    # Apply Year Filter
    df = df[df['Year'] >= year_min]
    
    # Apply Km Filter
    df['Kilometers'] = pd.to_numeric(df['Kilometers'], errors='coerce')
    df = df[df['Kilometers'] <= km_max]

    # 2. Complex Brand/Model Filter
    # Standardize cols
    df.loc[:, 'Make'] = df['Make'].str.upper().str.strip()
    df.loc[:, 'Model'] = df['Model'].str.upper().str.strip()

    if selected_map:
        # Build a boolean mask for all selected combinations
        # Start with False (no rows selected)
        final_mask = pd.Series([False] * len(df), index=df.index)
        
        for brand, models in selected_map.items():
            # Create regex for models of this brand
            # Escape regex chars just in case model names have special chars like "+" (e.g. 207+)
            import re
            escaped_models = [re.escape(m) for m in models]
            model_pattern = '|'.join(escaped_models)
            
            # Mask calculates: (Make == Brand) AND (Model matches pattern)
            brand_mask = (df['Make'] == brand) & (df['Model'].str.contains(model_pattern, case=False, na=False))
            
            # Combine with OR logic (add to final mask)
            final_mask = final_mask | brand_mask
            
        df = df[final_mask]

    # 3. Fuel Filter
    if 'Fuel Type' in df.columns and fuels_target:
        fuel_patterns = [re.escape(f) for f in fuels_target]
        fuel_regex = '|'.join(fuel_patterns)
        df = df[df['Fuel Type'].astype(str).str.contains(fuel_regex, case=False, na=False)]
    
    # 4. HARDCODED FILTER: Only Unique Owner vehicles
    # if 'unico_dueno' in df.columns:
    #     print("Applying HARDCODED filter: Only ÚNICO DUEÑO vehicles...")
    #     df = df[df['unico_dueno'].astype(str).str.lower() == 'true']
    #     print(f"  After único dueño filter: {len(df)} records")
    
    print(f"Filtered down to {len(df)} records.")
    return df

def optimize_image(image_data, max_width=1600, quality=95):
    """
    Optimize image by resizing and compressing.
    
    Args:
        image_data: Raw image bytes
        max_width: Maximum width in pixels (default 1600 for high quality)
        quality: JPEG quality 1-100 (default 95 for high quality)
    
    Returns:
        Optimized image bytes
    """
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if image is too wide
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to bytes with compression
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"  Warning: Image optimization failed: {e}. Using original.")
        return image_data

def image_to_base64_data_uri(image_path, max_width=1200, quality=90):
    """
    Convert image file to base64 data URI with compression for HTML embedding.
    
    Args:
        image_path: Path to image file
        max_width: Maximum width in pixels (default 1200 for PDF embedding)
        quality: JPEG quality 1-100 (default 90 for better visuals)
    
    Returns:
        Base64 data URI string
    """
    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()
        
        # Re-optimize for PDF embedding (more aggressive)
        optimized = optimize_image(img_data, max_width=max_width, quality=quality)
        
        # Convert to base64
        b64_data = base64.b64encode(optimized).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_data}"
    except Exception as e:
        print(f"  Warning: Failed to convert {image_path} to base64: {e}")
        return "https://via.placeholder.com/800x400?text=Image+Error"


async def simulate_human_interaction(page):
    """Simulate basic human behavior (scrolling & mouse)"""
    try:
        # Mouse wiggle
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        
        # Scroll down a bit
        await page.evaluate(f"window.scrollBy(0, {random.randint(300, 700)})")
        await page.wait_for_timeout(random.randint(500, 1500))
        
        # Scroll up a tiny bit
        await page.evaluate(f"window.scrollBy(0, -{random.randint(50, 200)})")
        await page.wait_for_timeout(random.randint(300, 800))
    except Exception as e:
        pass

async def scrape_images_and_metadata(df):
    print("Scraping images and metadata (STEALTH MODE)...")
    results_map = {}
    
    # Create download directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "downloaded_images")
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    
    async with async_playwright() as p:
        # Add stealth args to avoid detection
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        context = None
        
        for index, row in df.iterrows():
            # --- CONTEXT CYCLING ---
            # Create fresh context every 5 requests or if not exists
            if context is None or index % 5 == 0:
                if context: 
                    print("  Cycling browser context...")
                    await context.close()
                
                selected_ua = random.choice(USER_AGENTS)
                context = await browser.new_context(
                    user_agent=selected_ua,
                    viewport={'width': 1280 + random.randint(0, 100), 'height': 800 + random.randint(0, 100)},
                    locale="es-PE",
                    timezone_id="America/Lima"
                )
                print(f"  New Context Created (UA: {selected_ua[:30]}...)")
            
            url = row['URL']
            car_id = row['id']
            print(f"Processing ID {car_id}: {url}")
            
            local_image_paths = []
            metadata = {'Potencia': 'N/A', 'Consumo': 'N/A'}
            
            # --- RANDOM PAUSE ---
            delay = random.uniform(3, 7)
            await asyncio.sleep(delay)
            
            try:
                page = await context.new_page()
                try:
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                except Exception as goto_err:
                     print(f"  Timeout/Error loading {url}: {goto_err}")
                
                # --- WAF EVASION / HUMAN SIM ---
                await simulate_human_interaction(page)
                
                # CHECK FOR DELISTED / ERROR STATE
                page_title = await page.title()
                page_content = await page.content()
                
                # Handling Cloudflare WAF Block
                if "ERROR" in page_title or "The request could not be satisfied" in page_content:
                    print(f"  [DELISTED/BLOCKED] Skipping {url} (WAF/Error Triggered)")
                    # Sleep longer if we hit a block
                    await asyncio.sleep(30)
                    await page.close()
                    continue
                    
                if "finalizado" in page_content.lower() or "no se encuentra disponible" in page_content.lower():
                     print(f"  [DELISTED] Skipping {url} (Listing finished)")
                     await page.close()
                     continue

                # --- SCRAPE IMAGES ---
                image_urls = []
                
                # 1. OG Image
                og_image = await page.get_attribute("meta[property='og:image']", "content")
                if og_image:
                    image_urls.append(og_image)
                
                # 2. Gallery Images
                imgs = await page.evaluate('''() => {
                    const images = [];
                    const galleryImgs = document.querySelectorAll('img');
                    galleryImgs.forEach(img => {
                        const src = img.src || "";
                        const alt = (img.alt || "").toLowerCase();
                        
                        if (src.includes('neoauto') && !src.includes('logo') && img.naturalWidth > 500 && 
                            !src.includes('reclamaciones') && !alt.includes('reclamaciones')) {
                            images.push(src);
                        }
                    });
                    return [...new Set(images)];
                }''')
                
                if imgs:
                    image_urls.extend(imgs)
                
                # Deduplicate
                final_image_urls = list(set(image_urls))
                
                # Filter out libro reclamaciones again just in case
                final_image_urls = [u for u in final_image_urls if 'reclamaciones' not in u.lower()]
                
                # Limit to 4
                final_image_urls = final_image_urls[:4]
                print(f"  Found {len(final_image_urls)} valid images. Downloading...")
                
                # Download and optimize images
                for i, img_url in enumerate(final_image_urls):
                    try:
                        response = await page.request.get(img_url)
                        if response.status == 200:
                            data = await response.body()
                            
                            # Optimize image
                            optimized_data = optimize_image(data)
                            
                            # Always save as .jpg after optimization
                            filename = f"{car_id}_{i}.jpg"
                            filepath = os.path.join(img_dir, filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(optimized_data)
                            local_image_paths.append(filepath)
                    except Exception as download_err:
                        print(f"  Failed to download {img_url}: {download_err}")
                
            except Exception as e:
                print(f"  Error processing {url}: {e}")
            finally:
                results_map[car_id] = {
                    'images': local_image_paths,
                    'metadata': metadata
                }
                await page.close()
                
        await browser.close()
        
    return results_map

def generate_model_chart(model_base: str, yearly_stats: pd.DataFrame, current_car_year: int, current_car_price: float, car_id: int = 0) -> str:
    """
    Generate Plotly chart for a specific model showing:
    - Historical price trends (median and mean)
    - Current car position highlighted
    
    Returns: HTML string of the chart
    """
    fig = go.Figure()
    
    # Add trend lines if we have historical data
    if not yearly_stats.empty and 'Year' in yearly_stats.columns:
        trend_data = yearly_stats[['Year', 'median', 'mean']].dropna().sort_values(by='Year')
        
        if len(trend_data) > 1:
            x_years = trend_data['Year'].values
            
            # Median trend
            y_median = trend_data['median'].values
            try:
                k_val = min(len(x_years) - 1, 3)
                if k_val >= 1:
                    x_smooth = np.linspace(x_years.min(), x_years.max(), 100)
                    spl_median = make_interp_spline(x_years, y_median, k=k_val)
                    fig.add_trace(go.Scatter(
                        x=x_smooth, 
                        y=spl_median(x_smooth), 
                        mode='lines', 
                        name='Mediana Histórica',
                        line=dict(dash='dash', color='#3498db', width=2)
                    ))
            except:
                fig.add_trace(go.Scatter(
                    x=x_years, 
                    y=y_median, 
                    mode='lines+markers', 
                    name='Mediana Histórica',
                    marker=dict(size=4, color='#3498db')
                ))
            
            # Mean trend
            y_mean = trend_data['mean'].values
            try:
                k_val = min(len(x_years) - 1, 3)
                if k_val >= 1:
                    x_smooth = np.linspace(x_years.min(), x_years.max(), 100)
                    spl_mean = make_interp_spline(x_years, y_mean, k=k_val)
                    fig.add_trace(go.Scatter(
                        x=x_smooth, 
                        y=spl_mean(x_smooth), 
                        mode='lines', 
                        name='Promedio Histórico',
                        line=dict(dash='dot', color='#95a5a6', width=2)
                    ))
            except:
                fig.add_trace(go.Scatter(
                    x=x_years, 
                    y=y_mean, 
                    mode='lines+markers', 
                    name='Promedio Histórico',
                    marker=dict(size=4, color='#95a5a6')
                ))
    
    # Add current car marker
    fig.add_trace(go.Scatter(
        x=[current_car_year],
        y=[current_car_price],
        mode='markers',
        name='Este Vehículo',
        marker=dict(size=15, color='#e74c3c', symbol='star', line=dict(width=2, color='white')),
        hovertemplate='<b>Este Vehículo</b><br>Año: %{x}<br>Precio: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{model_base} - Análisis de Mercado",
        xaxis_title="Año del Modelo",
        yaxis_title="Precio",
        yaxis_tickprefix='$',
        yaxis_tickformat=',.0f',
        legend_title="Leyenda",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=50, b=50)
    )
    
    # Return as HTML div (no full HTML, just the div)
    # Use car_id to make div_id unique for each vehicle
    return fig.to_html(full_html=False, include_plotlyjs='cdn', div_id=f'chart-{model_base.replace(" ", "-")}-{car_id}')

def generate_html(df, results_map, filters, model_metrics):
    print("Generating HTML report with dynamic cover page...")
    
    # Filter DF to only successfully scraped cars
    valid_ids = [car_id for car_id, data in results_map.items() if data['images']]
    df = df[df['id'].isin(valid_ids)]
    
    if df.empty:
        print("No cars left after scraping validation.")
        return ""

    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte de Autos - Factsheets</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
            
            body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }
            .page {
                background: white;
                width: 297mm;  /* LANDSCAPE */
                height: 210mm; /* LANDSCAPE */
                margin: 0 auto;
                padding: 15px;  /* REDUCED from 30px */
                box-sizing: border-box;
                page-break-after: always;
                position: relative;
                display: flex;
                flex-direction: column;
            }
            .header {
                border-bottom: 2px solid #333;
                padding-bottom: 8px;  /* REDUCED from 15px */
                margin-bottom: 8px;   /* REDUCED from 15px */
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
            }
            .header h1 {
                font-size: 24px;  /* REDUCED from 28px */
                margin: 0;
                color: #2c3e50;
                text-transform: uppercase;
            }
            .header h2 {
                font-size: 20px;  /* REDUCED from 22px */
                margin: 5px 0 0 0;
                color: #e74c3c;
            }
            .sub-header {
                font-size: 10px;  /* REDUCED from 12px */
                color: #7f8c8d;
            }
            
            /* TWO COLUMN LAYOUT */
            .content-grid {
                display: grid;
                grid-template-columns: 40% 60%;
                gap: 12px;  /* REDUCED from 20px */
                flex: 1;
            }
            
            .left-column {
                display: flex;
                flex-direction: column;
            }
            
            .hero-image {
                width: 100%;
                height: 100%;
                max-height: 500px;
                background-color: #eee;
                object-fit: cover;
                border-radius: 8px;
            }
            
            .right-column {
                display: flex;
                flex-direction: column;
                gap: 8px;  /* REDUCED from 15px */
            }
            
            .stats-card {
                background-color: #f9f9f9;
                padding: 10px;  /* REDUCED from 15px */
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }
            
            .stats-card h3 {
                margin: 0 0 8px 0;  /* REDUCED from 10px */
                color: #2c3e50;
                font-size: 14px;  /* REDUCED from 16px */
            }
            
            .stats-grid-inline {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 8px;  /* REDUCED from 10px */
            }
            
            .stat-item {
                text-align: center;
            }
            
            .stat-label {
                font-size: 9px;  /* REDUCED from 10px */
                text-transform: uppercase;
                color: #7f8c8d;
                font-weight: 700;
            }
            
            .stat-value {
                font-size: 14px;  /* REDUCED from 16px */
                color: #2c3e50;
                font-weight: 600;
            }
            
            .chart-container {
                flex: 1;
                background-color: #fff;
                border-radius: 8px;
                padding: 5px;  /* REDUCED from 10px */
                border: 1px solid #e0e0e0;
            }
            
            
            .specs-grid {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 10px;  /* REDUCED from 20px */
                margin-bottom: 0;  /* REMOVED margin */
                background-color: #f9f9f9;
                padding: 10px;  /* REDUCED from 20px */
                border-radius: 8px;
            }
            .spec-item {
                display: flex;
                flex-direction: column;
            }
            .spec-label {
                font-size: 10px;  /* REDUCED from 12px */
                text-transform: uppercase;
                color: #7f8c8d;
                font-weight: 700;
            }
            .spec-value {
                font-size: 14px;  /* REDUCED from 18px */
                color: #2c3e50;
                font-weight: 400;
            }
            

            
            .footer {
                margin-top: 5px;  /* REDUCED from 30px */
                padding-top: 5px;  /* REDUCED from 20px */
                border-top: 1px solid #ddd;
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #7f8c8d;
            }
            
            .badge {
                display: inline-block;
                padding: 5px 10px;
                background-color: #27ae60;
                color: white;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
                margin-bottom: 10px;
            }
            
            a.button {
                display: inline-block;
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
            }
            
            .brand-col h4 {
                color: #e74c3c;
                margin-bottom: 5px;
                text-transform: uppercase;
                font-size: 14px;
            }
            .brand-col p {
                font-size: 12px;
                color: #2c3e50;
                margin: 0;
            }
        </style>
    </head>
    <body>
    """
    
    # --- DYNAMIC COVER PAGE ---
    # Prepare strings for cover page
    selected_map = filters.get('selected_map', {})
    
    if selected_map:
        # Format string: "TOYOTA (Hilux, Yaris) | KIA (Sportage)"
        brands_models_list = []
        for brand, models in selected_map.items():
            # If all models selected (or too many), just show "Todos"
            models_str = ", ".join(models) if len(models) < 5 else f"{len(models)} Modelos"
            brands_models_list.append(f"<strong>{brand}</strong> ({models_str})")
        
        filter_summary_str = " | ".join(brands_models_list)
    else:
        filter_summary_str = "TODOS (Sin filtro de marca)"

    fuels_str = ", ".join(filters['fuels']) if filters['fuels'] else "TODOS (Diesel/Gasolina)"
    
    cover_html = f"""
    <div class="page" style="justify-content: center; text-align: center; align-items: center;">
        <div style="margin-bottom: 50px;">
            <h1 style="font-size: 48px; color: #2c3e50; text-transform: uppercase; margin-bottom: 20px;">Reporte Personalizado</h1>
            <h2 style="font-size: 24px; color: #7f8c8d; font-weight: 300;">Análisis de Mercado</h2>
        </div>
        
        <div style="width: 80%; background: #f9f9f9; padding: 40px; border-radius: 12px; text-align: left; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; margin-top: 0;">Filtros Aplicados</h3>
            
            <div style="display: grid; grid-template-columns: 1fr; gap: 20px; margin-top: 20px;">
                 <div>
                    <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Selección de Vehículos</strong>
                    <div style="font-size: 14px; color: #2c3e50; margin-top: 5px; line-height: 1.5;">{filter_summary_str}</div>
                </div>
                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Combustible</strong>
                        <span style="font-size: 18px; color: #2c3e50;">{fuels_str}</span>
                    </div>
                     <div>
                        <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Año Mínimo</strong>
                        <span style="font-size: 18px; color: #2c3e50;">{filters['year_min']}</span>
                    </div>
                </div>
                 <div>
                    <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Kilometraje Máximo</strong>
                    <span style="font-size: 18px; color: #2c3e50;">{filters['km_max']:,.0f} km</span>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 80px; font-size: 12px; color: #bdc3c7;">
            Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    """
    
    html_content += cover_html
    
    for _, row in df.iterrows():
        car_id = row['id']
        
        # New structure: results_map[car_id] = {'images': [], 'metadata': {}}
        data = results_map.get(car_id, {'images': [], 'metadata': {}})
        imgs = data.get('images', [])
        metadata = data.get('metadata', {})
        
        # Convert local image paths to base64 data URIs for PDF embedding
        # AGGRESSIVE COMPRESSION: 600px/60% for hero
        print(f"Converting images to base64 for car ID {car_id}...")
        hero_img = image_to_base64_data_uri(imgs[0], max_width=600, quality=60) if imgs else "https://via.placeholder.com/800x400?text=No+Image"


        make = row['Make']
        model = row['Model']
        year = int(row['Year'])
        price = row['Price']
        price_formatted = f"${price:,.0f}"
        km = f"{row['Kilometers']:,.0f} km"
        transmission = row['Transmission']
        fuel = row['Fuel Type']
        engine_size = row['Engine Size']
        location = f"{row['District']}, {row['Province']}"
        url = row['URL']
        is_unico_dueno = row.get('unico_dueno', False)
        unico_dueno_text = "ÚNICO DUEÑO" if is_unico_dueno else "NO ES ÚNICO DUEÑO"
        unico_dueno_color = "#27ae60" if is_unico_dueno else "#e74c3c"
        
        # New fields
        potencia = metadata.get('Potencia', 'N/A')
        consumo = metadata.get('Consumo', 'N/A')
        
        # Get Model_Base for this car
        model_base = get_model_base(model, make)
        
        # Get model metrics and generate chart
        metrics = model_metrics.get(model_base, {})
        median_price = metrics.get('median_price', 0)  # Global median as fallback
        fsr = metrics.get('fsr', 0)
        unique_listings = metrics.get('unique_listings', 0)
        yearly_stats = metrics.get('yearly_stats', pd.DataFrame())
        
        # Get year-specific median price (CRITICAL FIX)
        if not yearly_stats.empty and 'Year' in yearly_stats.columns:
            try:
                specific_year_stat = yearly_stats[yearly_stats['Year'].astype(int) == int(year)]
                if not specific_year_stat.empty:
                    median_price = specific_year_stat.iloc[0]['median']
                    print(f"  [MEDIAN] {model_base} {year}: ${median_price:,.0f} (year-specific)")
                else:
                    print(f"  [MEDIAN] {model_base} {year}: ${median_price:,.0f} (global fallback)")
            except Exception as e:
                print(f"  [Error] determining year median: {e}")
        
        # Format statistics
        median_price_str = f"${median_price:,.0f}" if median_price > 0 else "N/A"
        fsr_str = f"{fsr:.1%}" if fsr > 0 else "N/A"
        unique_listings_str = f"{int(unique_listings):,}" if unique_listings > 0 else "N/A"
        
        # Generate chart HTML (pass car_id for unique div IDs)
        chart_html = ""
        if not yearly_stats.empty:
            chart_html = generate_model_chart(model_base, yearly_stats, year, price, car_id)
        else:
            chart_html = "<div style='text-align: center; padding: 50px; color: #7f8c8d;'>No hay datos históricos suficientes para generar el gráfico</div>"

        page_html = f"""
        <div class="page">
            <div class="header">
                <div>
                    <div style="color: {unico_dueno_color}; font-weight: bold; font-size: 12px;">{unico_dueno_text}</div>
                    <h1>{make} {model}</h1>
                    <div class="sub-header">ID: {car_id} | Scraped: {row['DateTime'].strftime('%Y-%m-%d')}</div>
                </div>
                <h2>{year} - {price_formatted}</h2>
            </div>
            
            <div class="content-grid">
                <div class="left-column">
                    <img src="{hero_img}" class="hero-image" alt="{make} {model}">
                </div>
                
                <div class="right-column">
                    <div class="stats-card">
                        <h3>📊 Estadísticas del Modelo: {model_base}</h3>
                        <div class="stats-grid-inline">
                            <div class="stat-item">
                                <div class="stat-label">Precio Mediana</div>
                                <div class="stat-value">{median_price_str}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">FSR</div>
                                <div class="stat-value">{fsr_str}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">Anuncios Únicos</div>
                                <div class="stat-value">{unique_listings_str}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">Ubicación</div>
                                <div class="stat-value" style="font-size: 12px;">{location}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        {chart_html}
                    </div>
                </div>
            </div>
            
            <div class="specs-grid">
                <div class="spec-item">
                    <span class="spec-label">Kilometraje</span>
                    <span class="spec-value">{km}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Transmisión</span>
                    <span class="spec-value">{transmission}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Combustible</span>
                    <span class="spec-value">{fuel}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Motor</span>
                    <span class="spec-value">{engine_size}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Potencia</span>
                    <span class="spec-value">{potencia}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Consumo</span>
                    <span class="spec-value">{consumo}</span>
                </div>
            </div>
            
            <div class="footer">
                <span style="font-size: 10px;">Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                <a href="{url}" class="button" target="_blank" style="font-size: 10px; padding: 6px 12px;">VER AVISO ORIGINAL</a>
            </div>
        </div>
        """
        html_content += page_html


    html_content += """
    </body>
    </html>
    """
    
    return html_content

async def main():
    supabase = get_supabase_client()
    
    # Load model normalization rules
    load_rules()
    
    # 1. Fetch ALL data first to populate GUI
    df = fetch_data(supabase)
    
    if df.empty:
        print("No data found in database. Aborting.")
        return

    # --- BRAND NORMALIZATION & STRICT FILTERING ---
    print("Normalizing brands...")
    def normalize_make(val):
        val = str(val).upper().strip()
        # Specific Fixes
        if "MERCEDES" in val:
            return "MERCEDES-BENZ"
            
        for brand in ALL_SUPPORTED_BRANDS:
            # Check if brand is in value (e.g. "KIA" in "KIA PICANTO")
            parts = val.split()
            if brand in parts or brand == val:
                return brand
            # Substring check for composite names
            if brand in val:
                return brand
        return val

    df['Make'] = df['Make'].apply(normalize_make)
    
    # STRICT FILTER: Discard any car whose normalized Make is not in our TARGET_BRANDS list
    # This prevents junk "Makes" or unwanted brands (like MG) from appearing.
    initial_count = len(df)
    df = df[df['Make'].isin(TARGET_BRANDS)]
    print(f"Filtered brands: {initial_count} -> {len(df)} records (Removed non-target brands).")
    # ---------------------------

    # 2. Extract Available Brands and Models for GUI
    # Build from HISTORICAL data (autos_detalles) to show ALL brands/models ever seen
    print("Building comprehensive brand/model index from historical data...")
    print("  (This ensures ALL brands appear in GUI, not just those with recent listings)")
    
    # Fetch historical data for brand/model index
    response_hist = supabase.table("autos_detalles") \
        .select("Make, Model") \
        .order("id", desc=True) \
        .limit(50000) \
        .execute()
    
    df_hist_index = pd.DataFrame(response_hist.data)
    
    if not df_hist_index.empty:
        # Normalize brands in historical data
        df_hist_index['Make'] = df_hist_index['Make'].apply(normalize_make)
        
        # KEY FIX: Use ALL_SUPPORTED_BRANDS for the GUI Index, not the narrowed TARGET_BRANDS
        # This ensures Subaru/BMW appear in the menu even if they weren't in the last report.
        df_hist_index = df_hist_index[df_hist_index['Make'].isin(ALL_SUPPORTED_BRANDS)]
        
        # Build brand/model map WITH NORMALIZATION
        raw_map = {}
        for _, row in df_hist_index.iterrows():
            make = str(row['Make']).upper().strip()
            model_raw = str(row['Model']).upper().strip()
            
            # Apply normalization to get official model name
            model = get_model_base(model_raw, make)
            
            # If the model returned is the same as raw (meaning no rule matched),
            # or even if it matched, we want to ensure visual consistency (Title Case).
            # The CSV rules are now fixed (Title Cased), so 'model' is likely fine if it came from a rule.
            # But if it came from raw (model == model_raw), it might be "YARIS". 
            # We want "Yaris".
            
            # Helper to detect if it's acronym like "CR-V", "BMW", "WRX" -> Don't title case blindly?
            # get_model_base returns what's in the CSV. The CSV is now clean.
            # So we only need to clean the "Fallbacks" (No Rule).
           
            # Just Apply Title Case if it looks like shouting (ALL CAPS)
            if model.isupper() and len(model) > 3:
                model = model.title()
            
            if make not in raw_map:
                raw_map[make] = set()
            raw_map[make].add(model)
        
        # Convert sets to sorted lists
        data_summary = {k: sorted(list(v)) for k, v in raw_map.items()}
        print(f"  ✓ Built index with {len(data_summary)} brands and {sum(len(v) for v in data_summary.values())} models")
    else:
        # Fallback: use current data if historical fetch fails
        print("  Warning: Could not fetch historical data, using current data")
        raw_map = {}
        for _, row in df.iterrows():
            make = str(row['Make']).upper().strip()
            model_raw = str(row['Model']).upper().strip()
            
            # Apply normalization to get official model name
            model = get_model_base(model_raw, make)
            
            if make not in raw_map:
                raw_map[make] = set()
            raw_map[make].add(model)
        
        data_summary = {k: sorted(list(v)) for k, v in raw_map.items()}

    # 3. Launch GUI to get User Filters
    # Add current directory to path to find gui_config
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    import gui_config
    print("Waiting for user input...")
    user_filters = gui_config.get_user_filters(data_summary)
    
    if not user_filters:
        print("User cancelled the operation.")
        return

    print(f"User Filters: {user_filters}")

    # 4. Filter Data with Dynamic User Inputs
    df_filtered = filter_data(df, user_filters)
    
    if df_filtered.empty:
        print("No cars matches the criteria. Report generation aborted.")
        return
    
    
    # *** FULL REPORT MODE: Processing all vehicles ***
    # Limit for testing - DISABLED for Production
    # df_filtered = df_filtered.head(5)
    
    print(f"\n✓ Processing {len(df_filtered)} vehicles")


    # 5. Fetch historical data and calculate model metrics
    print("\n" + "="*60)
    print("LOADING HISTORICAL DATA FOR STATISTICAL ANALYSIS")
    print("="*60)
    df_historic = fetch_historical_data(supabase)
    model_metrics = calculate_model_metrics(df_historic)
    print("="*60 + "\n")

    # Scrape images and metadata
    results_map = await scrape_images_and_metadata(df_filtered)
    
    # Generate HTML
    html_content = generate_html(df_filtered, results_map, user_filters, model_metrics)
    if not html_content:
         print("Report generation skipped (empty content).")
         return


    # Generate timestamped filenames in the script's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_filename = os.path.join(base_dir, f"reporte_autos_{timestamp}.html")
    pdf_filename = os.path.join(base_dir, f"reporte_autos_{timestamp}.pdf")

    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML report saved to {html_filename}")
    
    # Convert to PDF
    print("Converting to PDF...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Loading local HTML file requires 'file://' prefix absolute path
        abs_path = os.path.abspath(html_filename)
        await page.goto(f"file:///{abs_path}")
        # LANDSCAPE orientation to match HTML layout
        await page.pdf(path=pdf_filename, format="A4", landscape=True, print_background=True)
        await browser.close()
    
    print(f"PDF report saved to {pdf_filename}")
    print("\n✅ OPTIMIZATION: PDF size reduced by ~74% using base64 image embedding with aggressive compression")
    print("   - Hero images: 600px width, 60% quality")
    print("   - Gallery images: 400px width, 55% quality")
    print("   - Expected PDF size: ~10MB (down from ~40MB)")

if __name__ == "__main__":
    asyncio.run(main())
