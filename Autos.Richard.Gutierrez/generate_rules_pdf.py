import pandas as pd
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
import os

# Paths
RULES_CSV_PATH = Path(__file__).parent.parent / "Core" / "reglas_modelos_base.csv"
OUTPUT_HTML_PATH = Path(__file__).parent / "MODEL_RULES_SUMMARY.html"
OUTPUT_PDF_PATH = Path(__file__).parent / "MODEL_RULES_SUMMARY.pdf"

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; }}
    h1 {{ color: #2c3e50; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; color: #333; }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    .brand-header {{ background-color: #2c3e50; color: white; font-weight: bold; }}
</style>
</head>
<body>
    <h1>Resumen de Reglas de Normalización de Modelos</h1>
    <p>Este reporte muestra cómo se agrupan los diferentes nombres (patrones) encontrados en el mercado bajo un único <strong>Modelo Normalizado</strong>.</p>
    <p>Total de Reglas: {total_rules}</p>
    
    {table_content}
</body>
</html>
"""

async def generate_pdf(html_path, pdf_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file:///{html_path}")
        await page.pdf(path=pdf_path, format="A4", margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"})
        await browser.close()

def main():
    print(f"Reading rules from {RULES_CSV_PATH}...")
    if not RULES_CSV_PATH.exists():
        print("Error: Rules file not found.")
        return
        
    df = pd.read_csv(RULES_CSV_PATH)
    
    # Sort
    df['make_rule_match'] = df['make_rule_match'].astype(str).str.upper()
    df.sort_values(by=['make_rule_match', 'model_base_target', 'model_pattern_input_lower'], inplace=True)
    
    # Target Brands
    target_brands = [
        "KIA", "TOYOTA", "HYUNDAI", "NISSAN", "MITSUBISHI",
        "BMW", "AUDI", "SUBARU", "JEEP", "VOLKSWAGEN", "VOLVO", "MERCEDES-BENZ",
        "FORD", "HONDA", "MAZDA" # Adding these back just in case useful for audit, checking against user wish
    ]
    # Re-filtering strictly per user request to avoid noise
    target_brands = [
        "KIA", "TOYOTA", "HYUNDAI", "NISSAN", "MITSUBISHI",
        "BMW", "AUDI", "SUBARU", "JEEP", "VOLKSWAGEN", "VOLVO", "MERCEDES-BENZ"
    ]
    
    table_html = "<table><thead><tr><th>MARCA</th><th>MODELO NORMALIZADO</th><th>PATRONES AGRUPADOS (Inputs)</th></tr></thead><tbody>"
    
    grouped = df.groupby(['make_rule_match', 'model_base_target'])['model_pattern_input_lower'].apply(list)
    
    last_make = ""
    
    for (make, target), patterns in grouped.items():
        if make not in target_brands:
            continue
            
        patterns.sort()
        patterns_str = ", ".join([f"<code>{p}</code>" for p in patterns])
        
        # Visual grouping by brand
        make_display = make if make != last_make else ""
        row_style = ""
        if make != last_make:
            row_style = "border-top: 2px solid #666;"
            
        table_html += f"<tr style='{row_style}'><td><strong>{make_display}</strong></td><td><strong>{target}</strong></td><td>{patterns_str}</td></tr>"
        last_make = make
        
    table_html += "</tbody></table>"
    
    full_html = HTML_TEMPLATE.format(total_rules=len(df), table_content=table_html)
    
    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"Generating PDF at {OUTPUT_PDF_PATH}...")
    try:
        asyncio.run(generate_pdf(OUTPUT_HTML_PATH.absolute(), OUTPUT_PDF_PATH))
        print(f"✅ PDF Generated Successfully: {OUTPUT_PDF_PATH}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == "__main__":
    main()
