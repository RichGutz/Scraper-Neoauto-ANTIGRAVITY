#!/bin/bash

# Secuencia Semanal Scraper NeoAuto - LINUX
# Basado en la versión de Windows creada hoy

PROJECT_DIR="/home/richgutz/Scraper.Neoauto" # Ajustar según ruta real en Linux
LOG_FILE="$PROJECT_DIR/scraper_sequence_semanal.log"
PYTHON_EXEC="$PROJECT_DIR/venv/bin/python"

echo "==================================================" >> "$LOG_FILE"
echo "INICIANDO SECUENCIA SEMANAL - $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit

# 1. Extraccion V2
echo "--> Paso 1: Ejecutando Extraccion Semanal V2..."
$PYTHON_EXEC "extractores/2.SEMANAL.extractor_VCLI_v2.py" >> "$LOG_FILE" 2>&1

# 2. Randomize URLs
echo "--> Paso 2: Aleatorizando URLs..."
$PYTHON_EXEC "extractores/3.SEMANAL.randomize_urls_autos.py" >> "$LOG_FILE" 2>&1

# 3. Scraper Principal (Paralelo)
echo "--> Paso 3: Lanzando instancias paralelas del SCRAPER..."
# Nota: parallel_launcher.py debe estar configurado para usar python3 en Linux
$PYTHON_EXEC -u "parallel_launcher.py" >> "$LOG_FILE" 2>&1

# 4. Procesamiento JSON y UBIGEO
echo "--> Paso 4: Procesando JSONs y UBIGEO..."
$PYTHON_EXEC "extractores/5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py" >> "$LOG_FILE" 2>&1

# 5. Carga a Supabase
echo "--> Paso 5: Cargando a Supabase..."
$PYTHON_EXEC "extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py" >> "$LOG_FILE" 2>&1

# 6. Generador de Reporte (Headless)
echo "--> Paso 6: Generando Reporte Semanal..."
$PYTHON_EXEC "main.py" >> "$LOG_FILE" 2>&1

# 7. Subir a Google Drive
echo "--> Paso 7: Subiendo a Google Drive..."
$PYTHON_EXEC "google_drive/drive_uploader.py" >> "$LOG_FILE" 2>&1

# 8. Envío de Correo Final
echo "--> Paso 8: Enviando correo semanal..."
# Usamos el gmail_sender optimizado con el reporte semanal generado
$PYTHON_EXEC "gmail_sender/gmail_sender.py" --enviar-correos --html-path "$PROJECT_DIR/outputs/gmail_latest_weekly.html" >> "$LOG_FILE" 2>&1

echo "==================================================" >> "$LOG_FILE"
echo "SECUENCIA SEMANAL COMPLETADA - $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"

echo "PROCESO FINALIZADO."
