"""
Importador de Datos JSON a Supabase.

Este script es el puente final entre los datos procesados localmente y la base
db de datos central en la nube. Su función es tomar los archivos JSON estructurados
y cargarlos en la tabla de Supabase correspondiente.

Funcionalidad Principal:
1.  **Búsqueda de Archivos JSON**: Escanea el directorio `results_json` en busca
    de nuevos archivos .json.

2.  **Conexión a Supabase**: Establece una conexión con el cliente de Supabase
    para poder realizar operaciones en la base de datos.

3.  **Validación y Mapeo de Datos**: Antes de la inserción, cada archivo JSON
    es validado para asegurar que contiene los campos mínimos requeridos (como
    URL y precio). Si faltan datos cruciales como Marca, Modelo o Año, intenta
    extraerlos de la propia URL del anuncio como un mecanismo de fallback.
    Luego, mapea los datos del JSON a la estructura de columnas de la tabla
    `autos_detalles_diarios` en Supabase.

4.  **Verificación de Duplicados**: Realiza una consulta a Supabase para verificar
    si la URL del anuncio ya existe en la tabla. Si ya existe, omite la
    inserción para evitar registros duplicados.

5.  **Inserción de Datos**: Si la validación es exitosa y no es un duplicado,
    inserta el nuevo registro en la tabla `autos_detalles_diarios`.

6.  **Movimiento de Archivos Procesados**: Tras el intento de procesamiento (exitoso o no),
    mueve el archivo .json a la subcarpeta `PROCESADO` para evitar que sea procesado
    nuevamente y mantener limpio el directorio de entrada.

Este script asegura que solo datos válidos, enriquecidos y no duplicados sean
cargados a la base de datos, completando el ciclo de extracción y carga (ETL).
"""
import os
import json
import re
import shutil
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, Any, Optional
from pathlib import Path

# --- Configuración ---
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Las variables de entorno SUPABASE_URL o SUPABASE_KEY no están configuradas.")
    exit(1)

SUPABASE_TABLE_NAME: str = 'autos_detalles_diarios'
SCRIPT_DIR = Path(__file__).resolve().parent
JSON_INPUT_FOLDER: Path = SCRIPT_DIR / 'results_json'
PROCESSED_FOLDER: Path = JSON_INPUT_FOLDER / 'PROCESADO'

# --- Inicialización de Supabase Client ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Conexión con Supabase establecida exitosamente.")
except Exception as e:
    print(f"Error al conectar con Supabase: {e}")
    exit(1)

# --- Funciones de Procesamiento ---

def extraer_datos_de_url(url: str) -> Dict[str, Optional[str]]:
    """Intenta extraer Marca, Modelo y Año de una URL de Neoauto."""
    datos_url = {'Marca': None, 'Modelo': None, 'Año de fabricación': None}
    
    match = re.search(r'/(?:seminuevo|usado)/([^/]+)-([^/]+)-(\d{4})-\d+', url)
    
    if match:
        datos_url['Marca'] = match.group(1).replace('-', ' ').title() if match.group(1) else None
        datos_url['Modelo'] = match.group(2).replace('-', ' ').title() if match.group(2) else None
        datos_url['Año de fabricación'] = match.group(3) if match.group(3) else None
        
        if datos_url['Modelo'] and 'auto' in datos_url['Modelo'].lower():
            datos_url['Modelo'] = None
        if datos_url['Marca'] and 'auto' in datos_url['Marca'].lower():
            datos_url['Marca'] = None

    return datos_url

def validar_y_extraer_datos(json_data: Dict[str, Any], filename: str) -> Optional[Dict[str, Any]]:
    """Valida y extrae los datos para Supabase."""
    metadata = json_data.get('metadata', {})
    datos_vehiculo = json_data.get('datos_vehiculo', {})
    especificaciones = datos_vehiculo.get('especificaciones', {})
    ubicacion = datos_vehiculo.get('ubicacion', {})

    url = metadata.get('url_anuncio')
    price = datos_vehiculo.get('precio_usd')

    if not all([url, price is not None]):
        print(f"Descartando '{filename}': Faltan campos obligatorios (URL o Precio).")
        return None

    make = especificaciones.get('Marca')
    model = especificaciones.get('Modelo')
    year = especificaciones.get('Año de fabricación')

    if not all([make, model, year]):
        datos_de_url = extraer_datos_de_url(url)
        if not make:
            make = datos_de_url['Marca']
        if not model:
            model = datos_de_url['Modelo']
        if not year:
            year = datos_de_url['Año de fabricación']
        
        if not all([make, model, year]):
            print(f"Descartando '{filename}': No se pudo obtener Marca, Modelo o Año.")
            return None

    mapped_data: Dict[str, Any] = {
        'DateTime': metadata.get('fecha_extraccion'),
        'URL': url,
        'Make': make,
        'Model': model,
        'Price': price,
        'Year': year,
        'Kilometers': datos_vehiculo.get('kilometraje_km'),
        'Transmission': datos_vehiculo.get('transmision'),
        'Fuel Type': especificaciones.get('Combustible'),
        'Engine Size': especificaciones.get('Cilindrada'),
        'Model Version': especificaciones.get('Versión'),
        'District': ubicacion.get('distrito'),
        'Province': ubicacion.get('provincia'),
        'Department': ubicacion.get('departamento'),
        'unico_dueno': datos_vehiculo.get('es_unico_dueno', False)
    }

    return mapped_data

# --- Métricas de Auditoría ---
stats = {
    'total_procesados': 0,
    'nuevos_insertados': 0,
    'duplicados_omitidos': 0,
    'errores': 0,
    'marcas': {}
}

def generar_reporte_auditoria_html():
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    total = stats['total_procesados']
    health_status = "SALUDABLE" if total >= 2000 else "REVISIÓN REQUERIDA"
    health_color = "#10b981" if total >= 2000 else "#f59e0b"
    health_bg = "rgba(16, 185, 129, 0.1)" if total >= 2000 else "rgba(245, 158, 11, 0.1)"
    
    if total < 2000:
        warning_msg = f"""
        <div style="background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 25px; border-radius: 4px; color: #ef4444;">
            <strong>⚠️ ADVERTENCIA DE VOLUMEN:</strong> Se procesaron solo {total:,} vehículos en esta sesión semanal. 
            El volumen esperado de un lunes saludable es mayor a 2,000 vehículos. Por favor, verifica si la sesión se interrumpió o si hubo bloqueos de IP en Neoauto.
        </div>
        """
    else:
        warning_msg = ""

    sorted_brands = sorted(stats['marcas'].items(), key=lambda x: x[1]['procesados'], reverse=True)
    
    table_rows = ""
    for brand, b_stats in sorted_brands:
        processed = b_stats['procesados']
        inserted = b_stats['insertados']
        omitidos = b_stats['omitidos']
        errores = b_stats['errores']
        
        if errores > 0:
            status_td = '<span style="color: #ef4444; font-weight: bold;">⚠️ Error</span>'
        elif processed == 0:
            status_td = '<span style="color: #6b7280;">Sin datos</span>'
        else:
            status_td = '<span style="color: #10b981; font-weight: bold;">✓ OK</span>'
            
        table_rows += f"""
        <tr style="border-bottom: 1px solid #2d3748;">
            <td style="padding: 12px; font-weight: bold; color: #e2e8f0;">{brand}</td>
            <td style="padding: 12px; text-align: center; color: #a0aec0;">{processed:,}</td>
            <td style="padding: 12px; text-align: center; color: #48bb78;">{inserted:,}</td>
            <td style="padding: 12px; text-align: center; color: #4299e1;">{omitidos:,}</td>
            <td style="padding: 12px; text-align: center; color: #f56565;">{errores:,}</td>
            <td style="padding: 12px; text-align: center;">{status_td}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auditoría de Salud - Scraper Semanal</title>
    <style>
        body {{
            font-family: 'Outfit', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f1f5f9;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 900px;
            margin: 40px auto;
            padding: 30px;
            background-color: #1e293b;
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
            border: 1px solid #334155;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .title h1 {{
            font-size: 24px;
            margin: 0;
            color: #38bdf8;
            font-weight: 700;
        }}
        .title p {{
            font-size: 14px;
            color: #94a3b8;
            margin: 5px 0 0 0;
        }}
        .status-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .card {{
            background-color: #0f172a;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            border: 1px solid #334155;
        }}
        .card .value {{
            font-size: 28px;
            font-weight: 700;
            margin-top: 5px;
        }}
        .card .label {{
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .table-container {{
            margin-top: 25px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            background-color: #0f172a;
            color: #38bdf8;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            padding: 12px;
            border-bottom: 2px solid #334155;
        }}
        tr:hover {{
            background-color: #1e293b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <h1>Reporte de Auditoría Scraper Semanal</h1>
                <p>Fecha de ejecución: {today_str}</p>
            </div>
            <div class="status-badge" style="background-color: {health_bg}; color: {health_color}; border: 1px solid {health_color};">
                {health_status}
            </div>
        </div>

        {warning_msg}

        <div class="grid">
            <div class="card" style="border-top: 4px solid #38bdf8;">
                <div class="label">Procesados</div>
                <div class="value" style="color: #38bdf8;">{stats['total_procesados']:,}</div>
            </div>
            <div class="card" style="border-top: 4px solid #10b981;">
                <div class="label">Nuevos</div>
                <div class="value" style="color: #10b981;">{stats['nuevos_insertados']:,}</div>
            </div>
            <div class="card" style="border-top: 4px solid #3b82f6;">
                <div class="label">Duplicados</div>
                <div class="value" style="color: #3b82f6;">{stats['duplicados_omitidos']:,}</div>
            </div>
            <div class="card" style="border-top: 4px solid #ef4444;">
                <div class="label">Errores</div>
                <div class="value" style="color: #ef4444;">{stats['errores']:,}</div>
            </div>
        </div>

        <div class="table-container">
            <h2 style="font-size: 18px; margin-bottom: 15px; color: #38bdf8; font-weight: 600;">Detalle por Marca</h2>
            <table>
                <thead>
                    <tr>
                        <th style="text-align: left;">Marca</th>
                        <th>Total Procesados</th>
                        <th>Nuevos Insertados</th>
                        <th>Duplicados Omitidos</th>
                        <th>Errores</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #64748b;">
            Sistema de Monitoreo Scraper-Neoauto. Generado automáticamente.
        </div>
    </div>
</body>
</html>
"""
    outputs_dir = Path(__file__).resolve().parent.parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    report_path = outputs_dir / "scraper_audit_report.html"
    report_path.write_text(html_content, encoding="utf-8")
    print(f"Reporte de auditoría de salud generado en: {report_path}")

def importar_json_a_supabase(filepath: str):
    """
    Procesa un archivo JSON, lo inserta en Supabase (autos_detalles para semanal,
    autos_detalles_diarios para diario) y finalmente lo mueve a la carpeta de procesados.
    """
    filename = os.path.basename(filepath)
    print(f"--- Iniciando procesamiento para: {filename} ---")
    
    global stats
    stats['total_procesados'] += 1
    
    make_name = "Desconocido"

    # Determinar dinámicamente la tabla destino basada en el prefijo del archivo
    if filename.startswith('semanal_result_'):
        table_name = 'autos_detalles'
    elif filename.startswith('diario_result_'):
        table_name = 'autos_detalles_diarios'
    else:
        table_name = SUPABASE_TABLE_NAME  # Fallback a la configurada por defecto

    try:
        # Paso 1: Leer y validar el archivo JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Error al leer o parsear JSON en '{filename}': {e}")
            stats['errores'] += 1
            stats['marcas'].setdefault("Desconocido", {"procesados": 0, "insertados": 0, "omitidos": 0, "errores": 0})
            stats['marcas']["Desconocido"]["errores"] += 1
            stats['marcas']["Desconocido"]["procesados"] += 1
            return

        data_to_insert = validar_y_extraer_datos(json_data, filename)
        if data_to_insert is None:
            stats['errores'] += 1
            # Intentar extraer marca de la URL para registrar el error por marca
            url_url = json_data.get('metadata', {}).get('url_anuncio')
            if url_url:
                datos_de_url = extraer_datos_de_url(url_url)
                make_name = datos_de_url.get('Marca') or "Desconocido"
            stats['marcas'].setdefault(make_name, {"procesados": 0, "insertados": 0, "omitidos": 0, "errores": 0})
            stats['marcas'][make_name]["errores"] += 1
            stats['marcas'][make_name]["procesados"] += 1
            return

        make_name = data_to_insert.get('Make') or "Desconocido"
        make_name = make_name.strip().title()
        
        stats['marcas'].setdefault(make_name, {"procesados": 0, "insertados": 0, "omitidos": 0, "errores": 0})
        stats['marcas'][make_name]["procesados"] += 1

        # Paso 2: Insertar los datos en Supabase (Se confía en la restricción UNIQUE de la base de datos)
        try:
            response = supabase.from_(table_name).insert(data_to_insert).execute()
            if response.data:
                print(f"Datos de '{filename}' insertados exitosamente en '{table_name}'.")
            else:
                print(f"Inserción de '{filename}' en '{table_name}' completada (la API no devolvió datos, lo cual es normal).")
            stats['nuevos_insertados'] += 1
            stats['marcas'][make_name]["insertados"] += 1
        except Exception as e:
            err_str = str(e)
            if "duplicate key" in err_str or "already exists" in err_str or "unique constraint" in err_str:
                print(f"URL ya existe en '{table_name}'. Omitiendo inserción (duplicado).")
                stats['duplicados_omitidos'] += 1
                stats['marcas'][make_name]["omitidos"] += 1
            else:
                print(f"Error al insertar datos de '{filename}' en '{table_name}': {e}")
                stats['errores'] += 1
                stats['marcas'][make_name]["errores"] += 1

    finally:
        # Paso final: Mover el archivo a la carpeta de procesados
        try:
            destination_path = PROCESSED_FOLDER / filename
            shutil.move(str(filepath), str(destination_path))
            print(f"Archivo '{filename}' movido a '{destination_path}'")
        except Exception as e:
            print(f"¡CRÍTICO! Error al mover el archivo procesado '{filename}': {e}")
            print("El archivo podría ser procesado de nuevo en la siguiente ejecución.")
        print(f"--- Fin del procesamiento para: {filename} ---")

# --- Flujo Principal ---
if __name__ == "__main__":
    if not JSON_INPUT_FOLDER.exists():
        print(f"Error: La carpeta de entrada '{JSON_INPUT_FOLDER}' no existe.")
        exit(1)

    # Crear la carpeta de destino para los archivos procesados si no existe
    PROCESSED_FOLDER.mkdir(exist_ok=True)

    # Obtener la lista de archivos JSON a procesar, asegurándose de que sean archivos y no directorios
    json_files = [
        f for f in os.listdir(JSON_INPUT_FOLDER) 
        if f.endswith('.json') and os.path.isfile(os.path.join(JSON_INPUT_FOLDER, f))
    ]

    if not json_files:
        print(f"No se encontraron archivos JSON nuevos en '{JSON_INPUT_FOLDER}'.")
    else:
        print(f"Se encontraron {len(json_files)} archivo(s) JSON nuevos. Iniciando importación...")
        for json_file in json_files:
            full_filepath = os.path.join(JSON_INPUT_FOLDER, json_file)
            importar_json_a_supabase(full_filepath)
        print("Proceso de importación finalizado.")
    
    # Generar reporte de auditoría siempre al finalizar (aunque sean 0 archivos)
    generar_reporte_auditoria_html()