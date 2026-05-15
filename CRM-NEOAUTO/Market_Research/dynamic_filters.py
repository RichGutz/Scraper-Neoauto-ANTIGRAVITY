import pandas as pd
from supabase import Client
import markdown2
from weasyprint import HTML, CSS
import io
from datetime import datetime

def get_unique_brands(supabase: Client):
    """Obtiene la lista de todas las marcas únicas en la base de datos."""
    try:
        resp = supabase.table("autos_detalles_diarios").select("Make").execute()
        if not resp.data:
            return []
        df = pd.DataFrame(resp.data)
        return sorted(df['Make'].unique().tolist())
    except Exception as e:
        print(f"Error al obtener marcas: {e}")
        return []

def get_models_by_brand(supabase: Client, brand: str):
    """Obtiene los modelos únicos para una marca específica."""
    try:
        resp = supabase.table("autos_detalles_diarios").select("Model").eq("Make", brand).execute()
        if not resp.data:
            return []
        df = pd.DataFrame(resp.data)
        return sorted(df['Model'].unique().tolist())
    except Exception as e:
        print(f"Error al obtener modelos: {e}")
        return []

def get_years_by_model(supabase: Client, brand: str, model: str):
    """Obtiene los años disponibles para un modelo y marca específicos."""
    try:
        resp = supabase.table("autos_detalles_diarios").select("Year").eq("Make", brand).eq("Model", model).execute()
        if not resp.data:
            return []
        df = pd.DataFrame(resp.data)
        years = pd.to_numeric(df['Year'], errors='coerce').dropna().astype(int).unique().tolist()
        return sorted(years, reverse=True)
    except Exception as e:
        print(f"Error al obtener años: {e}")
        return []

def fetch_market_data(supabase: Client, brand: str, model: str, year: int):
    """Obtiene toda la data histórica para una combinación específica."""
    try:
        resp = supabase.table("autos_detalles_diarios") \
            .select("*") \
            .eq("Make", brand) \
            .eq("Model", model) \
            .eq("Year", year) \
            .execute()
        return resp.data
    except Exception as e:
        print(f"Error al obtener data de mercado: {e}")
        return []

def create_pdf_report(df: pd.DataFrame, brand: str, model: str, year: int):
    """Genera un reporte PDF premium de la data de mercado."""
    try:
        med_p = df['Price'].median()
        med_km = df['Kilometers'].median()
        count = len(df)
        md_text = f"# Reporte de Mercado: {brand} {model} ({year})\n"
        md_text += f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_text += f"## Resumen Ejecutivo\n- **Unidades en Muestra:** {count}\n- **Precio Mediano:** ${med_p:,.0f}\n- **Kilometraje Mediano:** {med_km:,.0f} km\n\n"
        md_text += "## Detalle de Unidades\n| URL | Precio ($) | KM | Distrito | Fecha |\n|---|---|---|---|---|\n"
        for _, row in df.head(20).iterrows():
            url_s = row['URL'][:30] + "..." if len(row['URL']) > 30 else row['URL']
            md_text += f"| [{url_s}]({row['URL']}) | ${row['Price']:,.0f} | {row['Kilometers']:,.0f} | {row['District']} | {str(row['DateTime'])[:10]} |\n"
        
        html_body = markdown2.markdown(md_text, extras=['tables'])
        STYLE = "@page { size: A4; margin: 2cm; } body { font-family: sans-serif; } table { width: 100%; border-collapse: collapse; } th, td { border: 1px solid #ddd; padding: 8px; } th { background: #1a3a5a; color: white; }"
        pdf_io = io.BytesIO()
        HTML(string=f"<html><body>{html_body}</body></html>").write_pdf(pdf_io, stylesheets=[CSS(string=STYLE)])
        return pdf_io.getvalue()
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return None
