#!/bin/bash
# Script WOL en UniFi Cloud Gateway Ultra
# Ubicación persistente: /data/bridge_wol.sh
# Programado en Cronjob para encendidos automáticos:
#   - Diario a las 8:00 AM
#   - Lunes a las 00:00 AM (Medianoche)

DISPOSITIVO="thinkpad_t430s"

echo "⏰ Iniciando secuencia de encendido para $DISPOSITIVO por hardware..."

# Enviar Magic Packet local de forma 100% nativa con Python 3
python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1); s.sendto(bytes.fromhex('ff'*6 + '3c970e7a9778'*16), ('192.168.0.255', 9))"

echo "✅ Magic Packet local inyectado con éxito en la red física de casa."
