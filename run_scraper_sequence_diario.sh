#!/bin/bash

# --- Configuración ---
# Use absolute path (adjust if necessary for your Linux environment)
PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
LOG_FILE="$PROJECT_DIR/scraper_sequence.log"
# Assuming virtualenv structure or system python
PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python"

# --- Logging Setup ---
# Redirect all output (stdout and stderr) to log file and console (tee)
exec > >(tee -a "$LOG_FILE") 2>&1

echo ""
echo "=================================================="
echo "INICIANDO SECUENCIA DE SCRAPING - $(date)"
echo "=================================================="

# Move to project dir
cd "$PROJECT_DIR" || { echo "ERROR: No se pudo acceder a $PROJECT_DIR"; exit 1; }

# --- Secuencia de Ejecución ---

# 1. Extraccion de URLs (1 dia)
echo ""
echo "--> Ejecutando Extraccion de URLs..."
$PYTHON_EXEC "extractores/2.DIARIO.daily_urls_extraction_v2.py"

if [ $? -ne 0 ]; then
    echo "ERROR en Extraccion de URLs."
    exit 1
fi

# 2. Scraper Principal (6 INSTANCIAS PARALELAS)
echo ""
echo "--> Lanzando 6 instancias paralelas del SCRAPER..."
# Usamos el launcher de Python para manejar la paralelizacion y el logging en tiempo real
# -u para unbuffered stdout
$PYTHON_EXEC -u "parallel_launcher.py"

echo "--> Scrapers finalizados."

# 4. Procesamiento JSON y Supabase
echo "--> Procesando JSONs..."
$PYTHON_EXEC "extractores/5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py"
$PYTHON_EXEC "extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py"

# 5. Generador de Reporte (General/Legado) - DESACTIVADO TEMPORALMENTE
# echo "--> Generando Reporte General..."
# $PYTHON_EXEC "generador_reporte_beta.py"

# --- Reporte Richard Gutierrez (PDF + Email) ---
echo "--> Reporte Richard Gutierrez..."
$PYTHON_EXEC "Autos.Richard.Gutierrez/generate_autos_report.py"

# Envio Correo Richard
echo "--> Enviando correo Richard a..."
$PYTHON_EXEC "Autos.Richard.Gutierrez/email_result.py"


# --- Reporte General (WKHTMLTOPDF + Drive + Email) --- DESACTIVADO
# echo "--> Reporte General..."
# HTML_REPORT="$PROJECT_DIR/outputs/gmail_reporte_beta.html"
# PDF_REPORT="$PROJECT_DIR/outputs/reporte_leads_unico_dueno.pdf"

# wkhtmltopdf "$HTML_REPORT" "$PDF_REPORT"

# echo "--> Subiendo a Drive..."
# DRIVE_LINK=$($PYTHON_EXEC "google_drive/drive_uploader.py")
# # Logic to capture output link would go here if uncommented

# echo "--> Enviando correo final..."
# if [ -n "$DRIVE_LINK" ]; then
#    $PYTHON_EXEC "gmail_sender/gmail_sender.py" --enviar-correos --drive-link "$DRIVE_LINK" --pdf-path "$PDF_REPORT"
# else
#    $PYTHON_EXEC "gmail_sender/gmail_sender.py" --enviar-correos --pdf-path "$PDF_REPORT"
# fi

echo ""
echo "=================================================="
echo "SECUENCIA COMPLETADA - $(date)"
echo "=================================================="

echo ""
echo "PROCESO FINALIZADO."

echo ""
echo "---> APAGANDO EL EQUIPO..."
sudo /sbin/shutdown -h now

exit 0
