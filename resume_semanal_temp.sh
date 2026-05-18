#!/bin/bash
PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python"

cd "$PROJECT_DIR"
echo "--> Retomando desde main.py"
$PYTHON_EXEC "main.py"

echo "--> Subiendo archivo(s) a Google Drive..."
DRIVE_LINK=$($PYTHON_EXEC "google_drive/drive_uploader.py")
echo "Enlace de Drive: $DRIVE_LINK"

echo "--> Enviando correo de Gmail..."
SUBJECT="Reporte Semanal Retomado - $(date +'%Y-%m-%d')"
$PYTHON_EXEC "$PROJECT_DIR/gmail_sender/gmail_sender.py" --enviar-correos --drive-link "$DRIVE_LINK"
echo "=== TERMINADO ==="
