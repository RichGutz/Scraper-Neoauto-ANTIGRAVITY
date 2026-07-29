import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import re

# --- CONFIGURACIÓN DE LOGGING ---
log_dir = Path(__file__).parent
log_file_path = log_dir / "generador_reporte_mejorado.log"
root_logger = logging.getLogger()
if root_logger.hasHandlers(): root_logger.handlers.clear()
root_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)
file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)
logger = logging.getLogger(__name__)

# --- IMPORTACIONES DEL CORE ---
core_module_path = Path(__file__).parent / "Core"
if str(core_module_path) not in sys.path: sys.path.append(str(core_module_path))
from Core.lead_filter_beta import filter_attractive_leads_beta

# --- CONSTANTES Y REGLAS (Replicado de main.py) ---
RULES_CSV_PATH = core_module_path / "reglas_modelos_base.csv"
TABLE_NAME = "autos_detalles"
LOADED_MODEL_RULES = None
TARGET_MAKE_MAPPING = {
    'mercedes benz': 'mercedes', 'mercedes-benz': 'mercedes', 'mercedes': 'mercedes',
    'vw': 'volkswagen', 'volkswagen': 'volkswagen', 'toyota': 'toyota', 'bmw': 'bmw',
    'nissan': 'nissan', 'hyundai': 'hyundai', 'subaru': 'subaru', 'mazda': 'mazda',
    'ford': 'ford', 'kia': 'kia', 'jeep': 'jeep', 'audi': 'audi', 'honda': 'honda',
    'chevrolet': 'chevrolet', 'mitsubishi': 'mitsubishi', 'suzuki': 'suzuki', 'volvo': 'volvo'
}
STANDARDIZED_TARGET_MAKES = sorted(list(set(TARGET_MAKE_MAPPING.values())))

# --- FUNCIONES DE PROCESAMIENTO (Replicadas de main.py) ---

def load_rules():
    global LOADED_MODEL_RULES
    if LOADED_MODEL_RULES is None:
        try:
            if RULES_CSV_PATH.exists():
                LOADED_MODEL_RULES = pd.read_csv(RULES_CSV_PATH)
                LOADED_MODEL_RULES['make_rule_match'] = LOADED_MODEL_RULES['make_rule_match'].astype(str).str.lower().str.strip()
                LOADED_MODEL_RULES['model_pattern_input_lower'] = LOADED_MODEL_RULES['model_pattern_input_lower'].astype(str).str.lower().str.strip()
                LOADED_MODEL_RULES.sort_values(by=['priority', 'pattern_length'], ascending=[False, False], inplace=True)
        except Exception as e:
            logger.error(f"Error cargando reglas: {e}")
            LOADED_MODEL_RULES = pd.DataFrame()

def fetch_all_data(client: Client) -> pd.DataFrame:
    logger.info(f"Iniciando descarga de la tabla histórica: '{TABLE_NAME}'")
    all_data = []
    offset = 0
    limit = 1000
    while True:
        try:
            response = client.from_(TABLE_NAME).select('*').order('id', desc=True).range(offset, offset + limit - 1).execute()
            if not response.data: break
            all_data.extend(response.data)
            if len(response.data) < limit: break
            offset += limit
        except Exception as e:
            logger.error(f"Error durante la descarga histórica: {e}", exc_info=True)
            return pd.DataFrame()
    logger.info(f"Descarga histórica completada. Total de filas: {len(all_data)}")
    return pd.DataFrame(all_data) if all_data else pd.DataFrame()

def fetch_daily_leads_data(client: Client) -> pd.DataFrame:
    TABLE_NAME_DIARIOS = "autos_detalles_diarios"
    logger.info(f"Iniciando descarga de la tabla de leads diarios: '{TABLE_NAME_DIARIOS}'")
    all_data = []
    offset = 0
    limit = 1000
    while True:
        try:
            response = client.from_(TABLE_NAME_DIARIOS).select('*').order('id', desc=True).range(offset, offset + limit - 1).execute()
            if not response.data: break
            all_data.extend(response.data)
            if len(response.data) < limit: break
            offset += limit
        except Exception as e:
            logger.error(f"Error durante la descarga de leads diarios: {e}", exc_info=True)
            return pd.DataFrame()
    logger.info(f"Descarga de leads diarios completada. Total de filas: {len(all_data)}")
    return pd.DataFrame(all_data) if all_data else pd.DataFrame()

def get_model_base(model_name: str, make_name: str) -> str:
    if pd.isna(model_name) or model_name == "Desconocido": return "Desconocido"
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

def process_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Procesando {len(df_raw)} filas.")
    df = df_raw.copy()
    desconocido_str = "Desconocido"
    df['Make'] = df['Make'].fillna(desconocido_str).astype(str).str.strip().str.lower().map(TARGET_MAKE_MAPPING).fillna(df['Make'].str.lower()).str.title()
    df['Model'] = df['Model'].fillna(desconocido_str).astype(str).str.strip().str.title()
    df['Model_Base'] = df.apply(lambda row: get_model_base(row['Model'], row['Make']), axis=1)
    df['slug'] = (df['Make'] + ' ' + df['Model_Base']).str.lower().str.replace(r'[^a-z0-9\s-]', '', regex=True).str.replace(r'\s+', '-', regex=True)
    df_filtered = df[df['Make'].str.lower().isin(STANDARDIZED_TARGET_MAKES)].copy()
    df_clean = df_filtered.copy()
    for col in ['Price', 'Year']:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    df_clean.drop_duplicates(subset=['URL', 'DateTime'], inplace=True)
    indispensable_cols = ['URL', 'DateTime', 'Make', 'Model', 'Model_Base', 'Price', 'Year']
    df_clean.dropna(subset=indispensable_cols, inplace=True)
    if not df_clean.empty:
        df_clean['Year'] = df_clean['Year'].astype(int)
    return df_clean

def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    grouped = df.groupby(['Make', 'Model_Base', 'Year', 'slug'], as_index=False)
    metrics = grouped.agg(unique_listings=('URL', 'nunique'), median_price=('Price', 'median'), mean_price=('Price', 'mean'), mean_year=('Year', 'mean'))
    fsr = df.groupby('slug')['URL'].apply(lambda g: (g.value_counts() == 1).sum() / g.nunique() if g.nunique() > 0 else 0).reset_index(name='fast_selling_ratio')
    final_metrics = pd.merge(metrics, fsr, on='slug', how='left')
    final_metrics.rename(columns={'Make': 'make_original_case', 'Model_Base': 'model_original_case'}, inplace=True)
    return final_metrics

def format_dataframe_for_html(df: pd.DataFrame, is_attractive: bool) -> pd.DataFrame:
    """Prepara un DataFrame para su conversión a HTML, con formato condicional."""
    df_report = df.copy()

    # Asegurar y formatear columna 'Distrito' (usando el nombre correcto de la columna)
    if 'District' in df_report.columns:
        df_report['Distrito'] = df_report['District'].fillna('N/A').astype(str).str.title()
    else:
        df_report['Distrito'] = 'N/A' # Fallback if 'District' column is missing

    # Formato de Oportunidad
    if 'Oportunidad_Precio' in df_report.columns:
        df_report['Oportunidad_Precio'] = df_report['Oportunidad_Precio'].apply(lambda x: f'{x:.2%}' if isinstance(x, (int, float)) else x)
    
    # Formato común
    df_report['Price'] = df_report['Price'].map('{:,.0f}'.format)
    df_report['Kilometers'] = pd.to_numeric(df_report['Kilometers'], errors='coerce').fillna(0).astype(int).map('{:,.0f}'.format)
    df_report['DateTime'] = pd.to_datetime(df_report['DateTime']).dt.strftime('%Y-%m-%d')
    
    if 'unico_dueno' in df_report.columns:
        df_report['Unico_Dueno'] = df_report['unico_dueno'].apply(lambda x: 'SI' if str(x).lower() == 'true' else 'NO')
    else:
        df_report['Unico_Dueno'] = 'N/A'
        
    df_report['URL'] = df_report['URL'].apply(lambda x: f'<a href="{x}">Ver Anuncio</a>')
    
    # Definir columnas a mostrar
    # We keep Model_Base here for grouping later, but will drop it before rendering the table
    columns_to_display = ['Make', 'Model', 'Year', 'Price', 'Kilometers', 'Unico_Dueno', 'Oportunidad_Precio', 'URL', 'DateTime', 'Distrito', 'Model_Base']
    
    # Filtrar columnas para asegurar que existan en el DataFrame
    columns_to_display = [col for col in columns_to_display if col in df_report.columns]
        
    return df_report[columns_to_display]

def generate_single_html_table(df: pd.DataFrame, title: str) -> str:
    """
    Genera una única tabla HTML para el DataFrame, con filas en blanco entre diferentes 'Make'.
    """
    if df.empty:
        return f'<h2 style="color: #0d47a1; text-align: center;">{title}</h2><p style="text-align: center;">No se encontraron datos.</p>'

    # Ordenar por Make para agrupar visualmente
    df_sorted = df.sort_values(by=['Make', 'Model_Base', 'Year']).copy()

    # Columnas a mostrar en la tabla final
    display_columns = ['Make', 'Model', 'Year', 'Price', 'Kilometers', 'Unico_Dueno', 'Oportunidad_Precio', 'URL', 'DateTime', 'Distrito']
    display_columns = [col for col in display_columns if col in df_sorted.columns]
    
    html_rows = []
    last_make = None
    for _, row in df_sorted.iterrows():
        current_make = row['Make']
        if last_make is not None and current_make != last_make:
            # Insertar fila en blanco con un padding sutil
            html_rows.append(f'<tr><td colspan="{len(display_columns)}" style="background-color: #ffffff; padding: 4px; border-bottom: none;"></td></tr>')
        
        html_row = "<tr>"
        for col in display_columns:
            html_row += f"<td>{row[col]}</td>"
        html_row += "</tr>"
        html_rows.append(html_row)
        last_make = current_make

    table_body = "".join(html_rows)
    
    # Encabezados de la tabla
    table_headers = "".join([f"<th>{col}</th>" for col in display_columns])

    style = '''
    <style>
        .dataframe-style {
            border-collapse: collapse;
            width: 90%;
            margin: 20px auto;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        .dataframe-style thead {
            background-color: #eef1f5;
            color: #333;
        }
        .dataframe-style th, .dataframe-style td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        .dataframe-style tbody tr:nth-of-type(even) {
            background-color: #f8f9fa;
        }
        .dataframe-style tbody tr:hover {
            background-color: #f1f1f1;
        }
        .dataframe-style a {
            color: #1a73e8;
            text-decoration: none;
            font-weight: bold;
        }
        .dataframe-style a:hover {
            text-decoration: underline;
        }
    </style>
    '''

    html_table = f'''
    {style}
    <h2 style="color: #0d47a1; text-align: center;">{title}</h2>
    <table class="dataframe-style">
        <thead>
            <tr>{table_headers}</tr>
        </thead>
        <tbody>
            {table_body}
        </tbody>
    </table>
    '''
    
    return html_table

def generate_combined_report():
    logger.info("=" * 60 + f"\nINICIANDO GENERADOR DE REPORTE BETA ({datetime.now()})\n" + "=" * 60)
    
    load_dotenv()
    load_rules()
    
    supabase_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    # 1. Obtener datos históricos y de leads
    df_raw_historic = fetch_all_data(supabase_client)
    df_raw_leads = fetch_daily_leads_data(supabase_client)

    if df_raw_leads.empty:
        logger.critical("No se descargaron datos de leads de 'autos_detalles_diarios'. Abortando.")
        return

    # 2. Procesar datos
    df_processed_historic = process_data(df_raw_historic)
    df_processed_leads = process_data(df_raw_leads)

    if df_processed_leads.empty:
        logger.critical("No quedaron datos de leads después del procesamiento. Abortando.")
        return

    # 3. Calcular métricas y aislar leads de la última sesión
    df_metrics = calculate_metrics(df_processed_historic)
    df_metrics.rename(columns={'model_original_case': 'Model', 'make_original_case': 'Make'}, inplace=True)
    
    df_processed_leads['DateTime'] = pd.to_datetime(df_processed_leads['DateTime'], errors='coerce', utc=True)
    max_timestamp_leads = df_processed_leads['DateTime'].dropna().max()
    df_leads_latest_session = df_processed_leads[df_processed_leads['DateTime'] >= (max_timestamp_leads - timedelta(days=15))].copy()
    logger.info(f"Se aislaron {len(df_leads_latest_session)} leads de la última sesión.")

    # 4. Calcular Oportunidad_Precio para todos los leads
    df_leads_with_metrics = pd.merge(df_leads_latest_session, df_metrics, on=['Make', 'Model', 'Year'], how='left')
    df_leads_with_metrics['Oportunidad_Precio'] = (df_leads_with_metrics['Price'] - df_leads_with_metrics['median_price']) / df_leads_with_metrics['median_price']
    df_leads_with_metrics['Oportunidad_Precio'] = df_leads_with_metrics['Oportunidad_Precio'].astype(object).fillna('No hay suficientes datos')

    # 5. Filtrar leads atractivos
    df_attractive_leads = filter_attractive_leads_beta(df_leads=df_leads_with_metrics, df_metrics=df_metrics)
    
    # FILTRAR POR UNICO DUEÑO
    if 'unico_dueno' in df_attractive_leads.columns:
        df_attractive_leads = df_attractive_leads[df_attractive_leads['unico_dueno'] == True].copy()
        logger.info(f"Filtrados leads atractivos por 'UNICO DUEÑO'. Quedan: {len(df_attractive_leads)}")
    
    # 6. Formatear ambos DataFrames
    df_attractive_formatted = pd.DataFrame()
    if not df_attractive_leads.empty:
        # Ordenar por oportunidad para agrupar
        df_attractive_leads.sort_values(by='Oportunidad_Precio', ascending=True, inplace=True)
        df_attractive_formatted = format_dataframe_for_html(df_attractive_leads, is_attractive=True)

    # Ordenar todos los leads por dueño
    if 'dueño' in df_leads_with_metrics.columns:
        df_leads_with_metrics.sort_values(by='Oportunidad_Precio', ascending=True, inplace=True, na_position='last')
    
    # FILTRAR POR UNICO DUEÑO
    if 'unico_dueno' in df_leads_with_metrics.columns:
        df_leads_with_metrics = df_leads_with_metrics[df_leads_with_metrics['unico_dueno'] == True].copy()
        logger.info(f"Filtrados todos los leads por 'UNICO DUEÑO'. Quedan: {len(df_leads_with_metrics)}")
    df_all_leads_formatted = format_dataframe_for_html(df_leads_with_metrics, is_attractive=False)

    # 6. Formatear ambos DataFrames (antes de agrupar)
    # Aplicar format_dataframe_for_html a los DataFrames filtrados
    df_attractive_leads_formatted = pd.DataFrame()
    if not df_attractive_leads.empty:
        df_attractive_leads_formatted = format_dataframe_for_html(df_attractive_leads, is_attractive=True)

    df_all_leads_formatted = pd.DataFrame()
    if not df_leads_with_metrics.empty:
        df_all_leads_formatted = format_dataframe_for_html(df_leads_with_metrics, is_attractive=False)

    # 7. Generar las tablas HTML
    attractive_html_table = generate_single_html_table(df_attractive_leads_formatted, "Leads Atractivos de Hoy (Único Dueño)")
    all_leads_html_table = generate_single_html_table(df_all_leads_formatted, "Todos los Leads de Hoy (Único Dueño)")

    # 8. Combinar en un solo reporte HTML
    today_str = datetime.now().strftime("%Y-%m-%d")
    final_html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte de Leads (BETA) {today_str}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f0f2f5; color: #333;">
        <div style="width: 95%; max-width: 1800px; margin: 20px auto; background-color: #ffffff; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1); border-radius: 8px; padding: 20px;">
            <header style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;">
                <h1 style="color: #0d47a1; margin: 0; font-size: 2.2em;">Reporte Diario de Vehículos (BETA)</h1>
            </header>
            <main>
                {attractive_html_table}
                <br><br>
                {all_leads_html_table}
            </main>
            <footer style="text-align: center; margin-top: 30px; padding-top: 10px; border-top: 1px solid #e0e0e0; font-size: 0.9em; color: #666;">
                <p>Reporte generado el {today_str}</p>
            </footer>
        </div>
    </body>
    </html>
    """

    # 9. Guardar el nuevo reporte
    base_output_dir = Path(__file__).parent / "outputs"
    base_output_dir.mkdir(exist_ok=True)
    final_report_path = base_output_dir / "gmail_reporte_beta.html"
    final_report_path.write_text(final_html_content, encoding="utf-8")
    
    logger.info("=" * 60)
    logger.info(f"Reporte BETA generado exitosamente en: {final_report_path}")
    logger.info("=" * 60)

if __name__ == "__main__":
    generate_combined_report()