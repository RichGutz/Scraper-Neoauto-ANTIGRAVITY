#!/bin/bash
# resume_semanal_post_scraping.sh
# Script para reanudar el procesamiento semanal una vez que termine el scraping paralelo.

set -e

PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python"

cd "$PROJECT_DIR"

# Redirigir salida al log principal
exec &> >(tee -a "$PROJECT_DIR/scraper_sequence_semanal.log")

echo ""
echo "=================================================="
echo "REANUDANDO SECUENCIA SEMANAL POST-SCRAPING"
date
echo "=================================================="

echo ""
echo "--> Ejecutando: extractores/5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py"
$PYTHON_EXEC "extractores/5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py"

echo ""
echo "--> Ejecutando: extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py"
$PYTHON_EXEC "extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py"

echo ""
echo "--> Ejecutando: main.py"
$PYTHON_EXEC "main.py"

# --- Subida a Google Drive y Captura de Enlace ---
echo ""
echo "--> Subiendo a Google Drive y capturando el enlace..."
DRIVE_LINK=$($PYTHON_EXEC "google_drive/drive_uploader.py")
if [ -n "$DRIVE_LINK" ]; then
    echo "Enlace de Drive obtenido: $DRIVE_LINK"
else
    echo "ADVERTENCIA: No se obtuvo enlace de Google Drive."
fi

# --- Envío de Correo con Gmail ---
echo ""
echo "--> Enviando correo con adjuntos vía Python (Gmail)..."
SUBJECT="Reporte Semanal - $(date +'%Y-%m-%d')"
$PYTHON_EXEC "$PROJECT_DIR/gmail_sender/gmail_sender.py" --enviar-correos --drive-link "$DRIVE_LINK"
echo "Proceso de envío finalizado."

echo ""
echo "=================================================="
echo "SECUENCIA DE SCRAPING SEMANAL COMPLETADA CON ÉXITO"
date
echo "=================================================="

# Opcional: Apagado si el usuario lo desea. Por seguridad no se ejecuta automáticamente aquí.
# echo "--> APAGANDO EL EQUIPO..."
# sudo /sbin/shutdown -h now

exit 0
