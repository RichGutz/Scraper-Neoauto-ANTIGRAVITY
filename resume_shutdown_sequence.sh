#!/bin/bash
# resume_shutdown_sequence.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== RETOMANDO PROCESO FINAL ===${NC}"

# 1. AUTH
echo ""
echo -e "${GREEN}[PASO 1/3] Autenticación de Google${NC}"
echo "Se requiere renovar el token. Se abrirá el navegador o un link."
python3 /home/richgutz/Scraper-Neoauto-ANTIGRAVITY/auth_only.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Autenticado correctamente.${NC}"
else
    echo -e "${RED}X Falló la autenticación. No se puede continuar.${NC}"
    read -p "Presiona Enter para salir..."
    exit 1
fi

# 2. EMAIL
echo ""
echo -e "${GREEN}[PASO 2/3] Enviando Reporte PDF${NC}"
python3 /home/richgutz/Scraper-Neoauto-ANTIGRAVITY/Autos.Richard.Gutierrez/email_result.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Correo enviado.${NC}"
else
    echo -e "${RED}X Falló el envío de correo. Revisar logs.${NC}"
    read -p "¿Continuar con el apagado de todas formas? (s/n): " confirm
    if [[ $confirm != "s" ]]; then
        exit 1
    fi
fi

# 3. SHUTDOWN
echo ""
echo -e "${GREEN}[PASO 3/3] Apagando el Equipo${NC}"
echo "Se solicitará tu contraseña de sudo para apagar."
sudo shutdown -h now
