#!/bin/bash

# Termina el script inmediatamente si cualquier comando falla.
set -e

# --- Configuración ---
PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
LOG_FILE="$PROJECT_DIR/scraper_sequence_semanal.log"
# Asegúrate de que la ruta a tu entorno virtual (venv) es correcta.
PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python"

# --- Logging ---
# Redirige toda la salida a un fichero de log y a la consola.
exec &> >(tee -a "$LOG_FILE")

# --- Lógica Principal ---
echo "=================================================="
echo "INICIANDO SECUENCIA DE SCRAPING SEMANAL"
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
echo "--> Comprobando si hay URLs pendientes de una ejecución previa..."
PENDING_COUNT=$($PYTHON_EXEC -c "
import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv()
try:
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    res = supabase.table('urls_autos_random').select('id', count='exact').or_('procesado.is.null,procesado.eq.false').execute()
    print(res.count if res.count else 0)
except Exception as e:
    print(0)
")

# Limpiar espacios
PENDING_COUNT=$(echo "$PENDING_COUNT" | tr -d '[:space:]')

if [ -n "$PENDING_COUNT" ] && [ "$PENDING_COUNT" -gt 0 ]; then
    echo "¡Se detectaron $PENDING_COUNT URLs pendientes en 'urls_autos_random'!"
    echo "Reanudando el scraping directamente sin reiniciar la cola de URLs..."
else
    echo "Cola vacía o nueva ejecución. Iniciando desde cero..."
    run_python_script "extractores/2.SEMANAL.extractor_VCLI_v3.py" # <-- NUEVO EXTRACTOR V3 (Soporta Seminuevos)
    run_python_script "extractores/3.SEMANAL.randomize_urls_autos.py"
fi


# --- Ejecución del scraper ---
echo ""
echo "--> Ejecutando 1 instancia de SCRAPER.NEOAUTO..."
SCRIPT_TO_RUN="extractores/4.DIARIO.SEMANAL.extractor_individual_v4.py"
$PYTHON_EXEC "$SCRIPT_TO_RUN"
echo "--> Finalizada la instancia del scraper."
# --- Fin de la ejecución ---

run_python_script "extractores/5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py"
run_python_script "extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py"
run_python_script "main.py"

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

# --- Envío de Correo de Auditoría de Salud ---
echo ""
echo "--> Enviando reporte de auditoría y salud del scraper (Gmail)..."
$PYTHON_EXEC "$PROJECT_DIR/gmail_sender/gmail_sender.py" --enviar-correos --send-audit
echo "Proceso de auditoría de salud finalizado."
echo ""
echo "=================================================="
echo "SECUENCIA DE SCRAPING SEMANAL COMPLETADA"
date
echo "=================================================="

echo ""
echo "--> APAGANDO EL EQUIPO..."
sudo /sbin/shutdown -h now

exit 0