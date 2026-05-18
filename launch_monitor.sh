#!/bin/bash
# Launcher para el Monitor Unificado en nueva ventana
DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
CMD="python3 $DIR/monitor_unified.py $@"

# Detectar emulador de terminal disponible
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --title="MONITOR SCRAPER" -- bash -c "$CMD; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -T "MONITOR SCRAPER" -e "$CMD; bash"
elif command -v konsole &> /dev/null; then
    konsole -e "$CMD"
elif command -v terminal &> /dev/null; then
    terminal -e "$CMD"
else
    echo "No se detectó un emulador de terminal compatible para abrir ventana independiente."
    echo "Ejecutando en esta terminal..."
    $CMD
fi
