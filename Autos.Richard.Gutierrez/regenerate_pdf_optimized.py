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

# Load credentials
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Configuration
PRICE_MIN = 15000
PRICE_MAX = 16500
MAX_AGE_YEARS = 7
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

ORIGIN_MAP = {
    "JAPONESAS": ["TOYOTA", "HONDA", "NISSAN", "MAZDA", "SUBARU", "SUZUKI", "MITSUBISHI", "LEXUS", "INFINITI", "ACURA"],
    "COREANAS": ["KIA", "HYUNDAI", "GENESIS", "SSANGYONG"],
    "AMERICANAS": ["CHEVROLET", "FORD", "JEEP", "DODGE", "CHRYSLER", "RAM", "GMC", "CADILLAC", "LINCOLN", "TESLA", "BUICK"],
    "ALEMANAS": ["BMW", "MERCEDES-BENZ", "AUDI", "VOLKSWAGEN", "PORSCHE"]
}

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_data(supabase):
    print("Fetching data from Supabase...")
    response = supabase.table("autos_detalles_diarios") \
        .select("*") \
        .eq("unico_dueno", True) \
        .gte("Price", PRICE_MIN) \
        .lte("Price", PRICE_MAX) \
        .execute()
    
    data = response.data
    df = pd.DataFrame(data)
    print(f"Fetched {len(df)} initial records.")
    return df

def filter_data(df):
    if df.empty:
        return df
    
    print("Filtering data...")
    current_year = datetime.now().year
    min_year = current_year - MAX_AGE_YEARS
    
    # 1. Age Filter
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df[df['Year'] >= min_year]
    
    # 2. Brand Filter
    df.loc[:, 'Make'] = df['Make'].str.upper().str.strip()
    df = df[df['Make'].isin(TARGET_BRANDS)]
    
    # 3. Date Filter (Last 30 Days)
    print("Converting DateTime...")
    df.loc[:, 'DateTime'] = pd.to_datetime(df['DateTime'], format='mixed', utc=True, errors='coerce')
    
    df = df.dropna(subset=['DateTime'])
    
    # Filter last 30 days
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
        df = df[df['DateTime'] >= cutoff_date]
    except Exception as e:
        print(f"Date filter error: {e}. Trying naive datetime.")
        df['DateTime'] = df['DateTime'].dt.tz_localize(None)
        cutoff_date = datetime.now() - timedelta(days=DAYS_BACK)
        df = df[df['DateTime'] >= cutoff_date]
    
    # 4. Transmission Filter (Exclude Mecanica)
    if 'Transmission' in df.columns:
        df = df[~df['Transmission'].astype(str).str.contains('Mecánica|Mecanica|Manual', case=False, na=False)]

    # 5. Fuel Filter
    if 'Fuel Type' in df.columns:
        df = df[df['Fuel Type'] == 'Gasolina']
    
    print(f"Filtered down to {len(df)} records.")
    return df

def optimize_image(image_data, max_width=800, quality=75):
    """
    Optimize image by resizing and compressing.
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary
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
        print(f"  Warning: Image optimization failed: {e}")
        return image_data

def image_to_base64_data_uri(image_path, max_width=800, quality=75):
    """
    Convert image file to base64 data URI with compression for HTML embedding.
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

def map_existing_images(df):
    """Map existing downloaded images to car IDs"""
    print("Mapping existing images...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "downloaded_images")
    
    results_map = {}
    
    for _, row in df.iterrows():
        car_id = row['id']
        local_images = []
        
        # Look for images matching this car_id
        for i in range(4):
            img_path = os.path.join(img_dir, f"{car_id}_{i}.jpg")
            if os.path.exists(img_path):
                local_images.append(img_path)
        
        # Dummy metadata (we don't have it without scraping)
        results_map[car_id] = {
            'images': local_images,
            'metadata': {'Potencia': 'N/A', 'Consumo': 'N/A'}
        }
        
        if local_images:
            print(f"  Found {len(local_images)} images for car ID {car_id}")
    
    return results_map

def generate_html(df, results_map):
    print("Generating HTML report with base64 images...")
    
    # Filter DF to only cars with images
    valid_ids = [car_id for car_id, data in results_map.items() if data['images']]
    df = df[df['id'].isin(valid_ids)]
    
    if df.empty:
        print("No cars with images found.")
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
                width: 210mm;
                height: 297mm;
                margin: 0 auto;
                padding: 40px;
                box-sizing: border-box;
                page-break-after: always;
                position: relative;
                display: flex;
                flex-direction: column;
            }
            .header {
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
            }
            .header h1 {
                font-size: 32px;
                margin: 0;
                color: #2c3e50;
                text-transform: uppercase;
            }
            .header h2 {
                font-size: 24px;
                margin: 5px 0 0 0;
                color: #e74c3c;
            }
            .sub-header {
                font-size: 14px;
                color: #7f8c8d;
            }
            
            .hero-image {
                width: 100%;
                height: 400px;
                background-color: #eee;
                object-fit: cover;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            
            .specs-grid {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 8px;
            }
            .spec-item {
                display: flex;
                flex-direction: column;
            }
            .spec-label {
                font-size: 12px;
                text-transform: uppercase;
                color: #7f8c8d;
                font-weight: 700;
            }
            .spec-value {
                font-size: 18px;
                color: #2c3e50;
                font-weight: 400;
            }
            
            .gallery {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-top: auto;
            }
            .gallery img {
                width: 100%;
                height: 150px;
                object-fit: cover;
                border-radius: 4px;
                background-color: #eee;
            }
            
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #7f8c8d;
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
    
    # --- COVER PAGE ---
    current_year = datetime.now().year
    present_brands = set(df['Make'].unique())
    
    brand_cols_html = ""
    for origin, brands in ORIGIN_MAP.items():
        found_brands = [b for b in brands if b in present_brands]
        if found_brands:
            brand_cols_html += f"""
            <div class="brand-col">
                <h4>{origin}</h4>
                <p>{', '.join(sorted(found_brands))}</p>
            </div>
            """
            
    cover_html = f"""
    <div class="page" style="justify-content: center; text-align: center; align-items: center;">
        <div style="margin-bottom: 50px;">
            <h1 style="font-size: 48px; color: #2c3e50; text-transform: uppercase; margin-bottom: 20px;">Búsqueda de Autos</h1>
            <h2 style="font-size: 24px; color: #7f8c8d; font-weight: 300;">Para Santiago Ganoza Recavarren</h2>
        </div>
        
        <div style="width: 80%; background: #f9f9f9; padding: 40px; border-radius: 12px; text-align: left; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; margin-top: 0;">Parámetros de Búsqueda</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <div>
                    <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Precio</strong>
                    <span style="font-size: 18px; color: #2c3e50;">${PRICE_MIN:,.0f} - ${PRICE_MAX:,.0f}</span>
                </div>
                <div>
                    <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Años</strong>
                    <span style="font-size: 18px; color: #2c3e50;">{current_year - MAX_AGE_YEARS} - {current_year + 1}</span>
                </div>
                 <div>
                    <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Combustible</strong>
                    <span style="font-size: 18px; color: #2c3e50;">Gasolina (Excl. Mecánica)</span>
                </div>
                 <div>
                    <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase;">Fecha de Extracción</strong>
                    <span style="font-size: 18px; color: #2c3e50;">Últimos 30 días</span>
                </div>
            </div>
            
            <div style="margin-top: 30px;">
                <strong style="display: block; color: #7f8c8d; font-size: 12px; text-transform: uppercase; margin-bottom: 10px;">Marcas Encontradas</strong>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    {brand_cols_html}
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
        
        data = results_map.get(car_id, {'images': [], 'metadata': {}})
        imgs = data.get('images', [])
        metadata = data.get('metadata', {})
        
        # Convert local image paths to base64 data URIs for PDF embedding
        print(f"Converting images to base64 for car ID {car_id}...")
        hero_img = image_to_base64_data_uri(imgs[0], max_width=600, quality=60) if imgs else "https://via.placeholder.com/800x400?text=No+Image"
        gallery_imgs = [image_to_base64_data_uri(img, max_width=400, quality=55) for img in imgs[1:4]] if len(imgs) > 1 else []
        
        # Fill missing gallery spots
        while len(gallery_imgs) < 3:
             gallery_imgs.append("https://via.placeholder.com/400x300?text=No+Image")

        make = row['Make']
        model = row['Model']
        year = row['Year']
        price = f"${row['Price']:,.0f}"
        km = f"{row['Kilometers']:,.0f} km"
        transmission = row['Transmission']
        fuel = row['Fuel Type']
        engine_size = row['Engine Size']
        location = f"{row['District']}, {row['Province']}"
        url = row['URL']
        unico_dueno = "ÚNICO DUEÑO" if row['unico_dueno'] else ""
        
        potencia = metadata.get('Potencia', 'N/A')
        consumo = metadata.get('Consumo', 'N/A')
        
        page_html = f"""
        <div class="page">
            <div class="header">
                <div>
                    <div style="color: #27ae60; font-weight: bold;">{unico_dueno}</div>
                    <h1>{make} {model}</h1>
                    <div class="sub-header">ID: {car_id} | Scraped: {row['DateTime'].strftime('%Y-%m-%d')}</div>
                </div>
                <h2>{year}</h2>
            </div>
            
            <img src="{hero_img}" class="hero-image" alt="{make} {model}">
            
            <div class="specs-grid">
                <div class="spec-item">
                    <span class="spec-label">Precio</span>
                    <span class="spec-value">{price}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Kilometraje</span>
                    <span class="spec-value">{km}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Ubicación</span>
                    <span class="spec-value">{location}</span>
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
                    <span class="spec-label">Rendimiento</span>
                    <span class="spec-value">{consumo}</span>
                </div>
            </div>
            
            <div style="text-align: right; margin-bottom: 20px;">
                <a href="{url}" class="button" target="_blank">VER AVISO ORIGINAL</a>
            </div>
            
            <div class="gallery">
                {"".join([f'<img src="{img}">' for img in gallery_imgs])}
            </div>
            
            <div class="footer">
                <span>Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                <span></span> 
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
    df = fetch_data(supabase)
    df_filtered = filter_data(df)
    
    if df_filtered.empty:
        print("No cars match the criteria.")
        return

    # Map existing images instead of scraping
    results_map = map_existing_images(df_filtered)
    
    # Generate HTML
    html_content = generate_html(df_filtered, results_map)
    if not html_content:
         print("Report generation skipped (empty content).")
         return

    with open("reporte_autos_optimized.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("HTML report saved to reporte_autos_optimized.html")
    
    # Convert to PDF
    print("Converting to PDF...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        abs_path = os.path.abspath("reporte_autos_optimized.html")
        await page.goto(f"file:///{abs_path}")
        await page.pdf(path="reporte_autos_optimized.pdf", format="A4", print_background=True)
        await browser.close()
    
    print("PDF report saved to reporte_autos_optimized.pdf")

if __name__ == "__main__":
    asyncio.run(main())
