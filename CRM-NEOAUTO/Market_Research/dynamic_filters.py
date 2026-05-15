import pandas as pd
from supabase import Client
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm


def clean_brand_name(brand: str) -> str:
    if not brand: return ""
    b = str(brand).upper().strip()
    # Mapeo de normalización para marcas comunes
    if b.startswith("MERCEDES"): return "MERCEDES-BENZ"
    if b.startswith("BMW"): return "BMW"
    if b.startswith("VW") or b.startswith("VOLKS"): return "VOLKSWAGEN"
    if b.startswith("TOYOTA"): return "TOYOTA"
    if b.startswith("NISSAN"): return "NISSAN"
    if b.startswith("HYUNDAI"): return "HYUNDAI"
    if b.startswith("KIA"): return "KIA"
    if b.startswith("MAZDA"): return "MAZDA"
    if b.startswith("SUBARU"): return "SUBARU"
    if b.startswith("SUZUKI"): return "SUZUKI"
    if b.startswith("HONDA"): return "HONDA"
    if b.startswith("AUDI"): return "AUDI"
    if b.startswith("CHEVRO"): return "CHEVROLET"
    if b.startswith("MITSUBI"): return "MITSUBISHI"
    if b.startswith("FORD"): return "FORD"
    if b.startswith("JEEP"): return "JEEP"
    if b.startswith("VOLVO"): return "VOLVO"
    if b.startswith("LAND"): return "LAND ROVER"
    if b.startswith("PORSCHE"): return "PORSCHE"
    if b.startswith("LEXUS"): return "LEXUS"
    return b

def get_unique_brands(supabase: Client):
    try:
        resp = supabase.table("autos_detalles").select("Make").execute()
        if not resp.data: return []
        df = pd.DataFrame(resp.data)
        # Limpiar y normalizar cada marca
        df['CleanMake'] = df['Make'].apply(clean_brand_name)
        # Filtrar ruidos cortos o marcas vacías
        valid_brands = df[df['CleanMake'].str.len() > 1]['CleanMake'].unique().tolist()
        return sorted([str(m) for m in valid_brands])
    except Exception as e:
        print(f"Error marcas: {e}")
        return []


def get_models_by_brand(supabase: Client, brand: str):
    try:
        # Consultar usando la marca original y posibles variaciones
        # Para simplificar, buscamos por ILIKE si es una marca normalizada
        resp = supabase.table("autos_detalles").select("Model").ilike("Make", f"{brand}%").execute()
        if not resp.data: return []
        df = pd.DataFrame(resp.data)
        # Limpiar modelos: todo a MAYÚSCULAS para agrupar XV y Xv
        df['CleanModel'] = df['Model'].str.upper().str.strip()
        return sorted([str(m) for m in df['CleanModel'].dropna().unique().tolist()])
    except Exception as e:
        print(f"Error modelos: {e}")
        return []


def get_years_by_model(supabase: Client, brand: str, model: str):
    try:
        resp = supabase.table("autos_detalles").select("Year") \
            .ilike("Make", f"{brand}%") \
            .ilike("Model", model) \
            .execute()
        if not resp.data: return []
        df = pd.DataFrame(resp.data)
        years = pd.to_numeric(df['Year'], errors='coerce').dropna().astype(int).unique().tolist()
        return sorted(years, reverse=True)
    except Exception as e:
        print(f"Error anios: {e}")
        return []


def fetch_market_data(supabase: Client, brand: str, model: str, year: int):
    try:
        resp = supabase.table("autos_detalles") \
            .select("*") \
            .ilike("Make", f"{brand}%") \
            .ilike("Model", model) \
            .eq("Year", year) \
            .execute()
        return resp.data
    except Exception as e:
        print(f"Error data mercado: {e}")
        return []


def create_pdf_report(df: pd.DataFrame, brand: str, model: str, year: int):
    """Genera PDF usando reportlab (ya instalado en el servidor)."""
    try:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        dark_blue = colors.HexColor("#1a3a5a")

        h1 = ParagraphStyle('h1', parent=styles['Heading1'], textColor=dark_blue, fontSize=18, spaceAfter=6)
        h2 = ParagraphStyle('h2', parent=styles['Heading2'], textColor=dark_blue, fontSize=13, spaceAfter=4)
        body = styles['Normal']

        med_p  = df['Price'].median()
        med_km = df['Kilometers'].median()
        count  = len(df)

        elements = []
        elements.append(Paragraph(f"Reporte de Mercado: {brand} {model} ({year})", h1))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body))
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("Resumen Ejecutivo", h2))
        elements.append(Paragraph(f"<b>Muestra:</b> {count} unidades", body))
        elements.append(Paragraph(f"<b>Precio Mediano:</b> ${med_p:,.0f}", body))
        elements.append(Paragraph(f"<b>KM Mediano:</b> {med_km:,.0f} km", body))
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("Detalle de Unidades (Top 20)", h2))

        table_data = [["URL", "Precio ($)", "KM", "Distrito", "Fecha"]]
        for _, row in df.head(20).iterrows():
            url_s = str(row.get('URL', ''))[:40]
            table_data.append([
                url_s,
                f"${row.get('Price', 0):,.0f}",
                f"{row.get('Kilometers', 0):,.0f}",
                str(row.get('District', '')),
                str(row.get('DateTime', ''))[:10]
            ])

        tbl = Table(table_data, colWidths=[6*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), dark_blue),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTSIZE',   (0, 0), (-1, -1), 8),
            ('GRID',       (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ('PADDING',    (0, 0), (-1, -1), 4),
        ]))
        elements.append(tbl)

        doc.build(elements)
        return buf.getvalue()
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return None
