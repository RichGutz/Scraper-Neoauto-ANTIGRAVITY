#!/bin/bash

# Termina el script inmediatamente si cualquier comando falla.
set -e

# --- Configuración ---
PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
LOG_FILE="$PROJECT_DIR/scraper_sequence_semanal.log"
# Asegúrate de que la ruta a tu entorno virtual (venv) es correcta.
PYTHON_EXEC="python3"

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
# --- Secuencia de Ejecución ---
# run_python_script "extractores/1.SEMANAL.extractor_VCLI.py"  <-- OMITIDO (Funcionalidad integrada en V2)
run_python_script "extractores/2.SEMANAL.extractor_VCLI_v2.py" # <-- NUEVO EXTRACTOR V2 (Descarga las URLs)
# run_python_script "extractores/2.SEMANAL.car_urls_module_VCLI.py" <-- OMITIDO (Reemplazado por V2)
run_python_script "extractores/3.SEMANAL.randomize_urls_autos.py" # <-- Randomiza las URLs para los workers

# --- Ejecución del scraper (8 instancias en paralelo) ---
echo ""
echo "--> Ejecutando 8 instancias paralelas de SCRAPER.NEOAUTO..."
$PYTHON_EXEC "parallel_launcher_semanal.py"
echo "--> Finalizadas todas las instancias del scraper."
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

# --- Envío de Correo con SendGrid y Adjuntos ---
echo ""
echo "--> Enviando correo con adjuntos vía Python..."
SUBJECT="Reporte Semanal - $(date +'%Y-%m-%d')"
$PYTHON_EXEC "gmail_sender/gmail_sender.py" --enviar-correos --subject "$SUBJECT" --drive-link "$DRIVE_LINK"
echo "Proceso de envío finalizado."


echo ""
echo "=================================================="
echo "SECUENCIA DE SCRAPING SEMANAL COMPLETADA"
date
echo "=================================================="

echo ""
echo "--> APAGANDO EL EQUIPO..."
sudo /sbin/shutdown -h now

exit 0