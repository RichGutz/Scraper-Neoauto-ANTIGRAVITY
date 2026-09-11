#!/bin/bash
# Script de auto-arranque Kiosk para Brave -> Netdata

# Asegurar que el servicio Netdata arranque siempre
sudo systemctl enable --now netdata 2>/dev/null || true

# Esperar a que Netdata tenga tiempo de iniciar
sleep 4

exec /usr/bin/brave-browser \
  --start-maximized \
  --no-first-run \
  --no-default-browser-check \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --check-for-update-interval=31536000 \
  --disable-component-update \
  --password-store=basic \
  "http://localhost:19999"
