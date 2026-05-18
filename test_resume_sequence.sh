#!/bin/bash
PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
PYTHON_EXEC="python3"

cd "$PROJECT_DIR" || exit 1

echo "=================================================="
echo "PRUEBA DE SECUENCIA FINAL (UPLOAD -> EMAIL -> SHUTDOWN)"
echo "=================================================="

# --- Subida a Google Drive y Captura de Enlace ---
echo ""
echo "--> Subiendo a Google Drive y capturando el enlace..."
DRIVE_LINK=$($PYTHON_EXEC "google_drive/drive_uploader.py")
if [ -n "$DRIVE_LINK" ]; then
    echo "Enlace de Drive obtenido: $DRIVE_LINK"
else
    echo "ADVERTENCIA: No se obtuvo enlace de Google Drive (o script falló/no retornó nada)."
    # Fallback for testing if upload fails or returns nothing, to ensure email is tested
    # DRIVE_LINK="https://drive.google.com/drive/folders/TEST_LINK_PLACEHOLDER"
fi

# --- Envío de Correo con SendGrid y Adjuntos ---
echo ""
echo "--> Enviando correo con adjuntos vía Python..."
SUBJECT="TEST Reporte Semanal - $(date +'%Y-%m-%d %H:%M')"
echo "Ejecutando gmail_sender.py con drive-link: '$DRIVE_LINK'"

# Pass DRIVE_LINK logic carefully
if [ -n "$DRIVE_LINK" ]; then
    $PYTHON_EXEC "gmail_sender/gmail_sender.py" --enviar-correos --subject "$SUBJECT" --drive-link "$DRIVE_LINK"
else
    $PYTHON_EXEC "gmail_sender/gmail_sender.py" --enviar-correos --subject "$SUBJECT"
fi

echo "Proceso de envío finalizado."

echo ""
echo "=================================================="
echo "SECUENCIA DE PRUEBA COMPLETADA"
date
echo "=================================================="

echo ""
echo "--> PRUEBA DE APAGADO (Simulado 1 minuto)..."
echo "Ejecutando: sudo shutdown -h +1 'Prueba de apagado del Scraper. Cancele con shutdown -c'"
sudo shutdown -h +1 "Prueba de apagado del Scraper. Cancele con shutdown -c si desea continuar usando el equipo."

echo "Shutdown programado en 1 minuto. Use 'sudo shutdown -c' para cancelar."
