#!/bin/bash
PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
LOG_FILE="$PROJECT_DIR/nohup_scraper_semanal.out"

cd "$PROJECT_DIR"

echo "Iniciando secuencia semanal en segundo plano..."
echo "Los logs se guardarán en: $LOG_FILE"

# Ejecutar con nohup y desvincular
nohup ./run_scraper_semanal.sh > "$LOG_FILE" 2>&1 &

echo "Proceso iniciado con PID: $!"
echo "Puede cerrar esta ventana sin detener el scraper."
