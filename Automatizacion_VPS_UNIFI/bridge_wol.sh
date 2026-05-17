#!/bin/bash
# Script Puente WOL en UniFi Cloud Gateway Ultra
# Ubicación persistente: /data/bridge_wol.sh

SUPABASE_URL="https://llrhimiivjpmxelffxef.supabase.co/rest/v1/control_wol"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxscmhpbWlpdmpwbXhlbGZmeGVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY0NzM0NDEsImV4cCI6MjA2MjA0OTQ0MX0.zxWg5wSANpUfCK5OeWvwK5xQbLqgcuegKPT6gDdH5F0"
DISPOSITIVO="thinkpad_t430s"

# 1. Consultar a Supabase si hay una orden de encendido
RESPONSE=$(curl -s -X GET "$SUPABASE_URL?dispositivo=eq.$DISPOSITIVO&select=solicitar_encendido" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY")

# 2. Si la respuesta contiene "solicitar_encendido":true, disparar el Magic Packet local en Python
if [[ "$RESPONSE" == *'"solicitar_encendido":true'* ]]; then
  echo "🚀 ¡Orden de encendido detectada para $DISPOSITIVO!"
  
  # Generar Magic Packet local usando Python nativo del router
  python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1); s.sendto(bytes.fromhex('ff'*6 + '3c970e7a9778'*16), ('192.168.0.255', 9))"
  
  # 3. Actualizar la base de datos de vuelta a FALSE y estado a 'booting'
  curl -s -X PATCH "$SUPABASE_URL?dispositivo=eq.$DISPOSITIVO" \
    -H "apikey: $SUPABASE_KEY" \
    -H "Authorization: Bearer $SUPABASE_KEY" \
    -H "Content-Type: application/json" \
    -d '{"solicitar_encendido": false, "estado": "booting"}'
  
  echo "✅ Magic Packet local inyectado con Python y base de datos actualizada."
fi
