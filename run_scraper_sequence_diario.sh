#!/bin/bash

# Termina el script inmediatamente si cualquier comando falla.
set -e

# --- Configuración ---
PROJECT_DIR="/home/richgutz/Scraper.Neoauto"
LOG_FILE="$PROJECT_DIR/scraper_sequence.log"
# Asegúrate de que la ruta a tu entorno virtual (venv) es correcta.
PYTHON_EXEC="$PROJECT_DIR/venv/bin/python"

# --- Logging ---
# Redirige toda la salida a un fichero de log y a la consola.
exec &> >(tee -a "$LOG_FILE")

# --- Lógica Principal ---
echo "=================================================="
echo "INICIANDO SECUENCIA DE SCRAPING"
date
echo "=================================================="

# Moverse al directorio del proyecto es crucial.
cd "$PROJECT_DIR"

# --- Función para ejecutar scripts de Python ---
run_python_script() {
    SCRIPT_PATH=$1
    echo ""
    echo "--> Ejecutando: $SCRIPT_PATH"
    $PYTHON_EXEC "$SCRIPT_PATH"
    echo "--> Finalizado: $SCRIPT_PATH"
}

# --- Secuencia de Ejecución ---
run_python_script "extractores/2.DIARIO.daily_urls_extraction.VCLI.py"
# --- Ejecución de una sola instancia del scraper ---
echo ""
echo "--> Ejecutando 1 instancia de SCRAPER.NEOAUTO..."
SCRIPT_TO_RUN="extractores/4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.SUPABASE.PARA.CRON.BETA.py"
$PYTHON_EXEC "$SCRIPT_TO_RUN"
echo "--> Finalizada la instancia."
# --- Fin de la ejecución de una sola instancia ---
run_python_script "extractores/5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py"
run_python_script "extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py"
# run_python_script "generador_reporte_beta.py"

# --- Generación de PDF para Richard Gutierrez ---
echo ""
echo "--> Generando Reporte PDF para Richard Gutierrez..."
"$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/Autos.Richard.Gutierrez/generate_autos_report.py"
RICHARD_GUTIERREZ_PDF_PATH="$PROJECT_DIR/Autos.Richard.Gutierrez/reporte_autos_final.pdf"
echo "--> PDF de Richard Gutierrez generado en: $RICHARD_GUTIERREZ_PDF_PATH"

# --- Envío de Correo de Reporte Richard Gutierrez ---
echo ""
echo "--> Enviando correo de Reporte Richard Gutierrez..."
"$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/gmail_sender/sender_richard_gutierrez.py" --enviar-correos --pdf-path "$RICHARD_GUTIERREZ_PDF_PATH"
echo "Proceso de envío de Richard Gutierrez finalizado."


# --- Generación de PDF ---
# echo ""
# echo "--> Generando PDF desde el reporte HTML..."
# HTML_REPORT_PATH="$PROJECT_DIR/outputs/gmail_reporte_beta.html"
# PDF_REPORT_PATH="$PROJECT_DIR/outputs/reporte_leads_unico_dueno.pdf"
# wkhtmltopdf "$HTML_REPORT_PATH" "$PDF_REPORT_PATH"
# echo "--> PDF generado en: $PDF_REPORT_PATH"

# --- Subida a Google Drive y Captura de Enlace ---
# echo ""
# echo "--> Subiendo a Google Drive y capturando el enlace..."
# DRIVE_LINK=$($PYTHON_EXEC "google_drive/drive_uploader.py")
# if [ -n "$DRIVE_LINK" ]; then
#     echo "Enlace de Drive obtenido: $DRIVE_LINK"
# else
#     echo "ADVERTENCIA: No se obtuvo enlace de Google Drive."
# fi

# --- Envío de Correo con Gmail y Adjuntos ---
# echo ""
# echo "--> Enviando correo con adjuntos vía Python (Gmail)..."
# if [ -n "$DRIVE_LINK" ]; then
#     $PYTHON_EXEC "/home/richgutz/Scraper.Neoauto/gmail_sender/gmail_sender.py" --enviar-correos --drive-link "$DRIVE_LINK" --pdf-path "$PDF_REPORT_PATH"
# else
#     echo "ADVERTENCIA: No se obtuvo enlace de Google Drive, enviando correo sin el enlace."
#     $PYTHON_EXEC "/home/richgutz/Scraper.Neoauto/gmail_sender/gmail_sender.py" --enviar-correos --pdf-path "$PDF_REPORT_PATH"
# fi
# echo "Proceso de envío finalizado." 

echo ""
echo "=================================================="
echo "SECUENCIA DE SCRAPING COMPLETADA"
date
echo "=================================================="

echo ""
# echo "--> APAGANDO EL EQUIPO..."
# sudo /sbin/shutdown -h now

exit 0
