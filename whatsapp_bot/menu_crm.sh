#!/bin/bash

# Configuration
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
CURRENT_DIR="$(dirname "$(readlink -f "$0")")"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Set Title (may not work in all terminals)
echo -ne "\033]0;CRM Neoauto - Menu Principal\007"

function pause_script() {
    echo ""
    read -p "Presione Enter para continuar..."
}

function open_new_window() {
    local title="$1"
    local command="$2"
    
    # Try common terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" -- bash -c "$command; exec bash"
    elif command -v x-terminal-emulator &> /dev/null; then
        x-terminal-emulator -e bash -c "$command; exec bash"
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal --title="$title" -e "bash -c '$command; exec bash'"
    elif command -v konsole &> /dev/null; then
        konsole -e bash -c "$command; exec bash"
    else
        echo -e "${RED}No se encontró un emulador de terminal compatible (gnome-terminal, xfce4, etc).${NC}"
        echo -e "Ejecutando en esta ventana..."
        eval "$command"
    fi
}

while true; do
    clear
    echo -e "${GREEN}==================================================${NC}"
    echo -e "${GREEN}   CRM NEOAUTO - MENU PRINCIPAL (LINUX VERSION)${NC}"
    echo -e "${GREEN}==================================================${NC}"
    echo ""
    echo -e "  1. Procesar Correos y Enviar WhatsApps"
    echo -e "     (Parsea Gmail, crea contactos, envia saludos)"
    echo ""
    echo -e "  2. Activar Listener (Monitoreo Continuo)"
    echo -e "     (Lee conversaciones de WhatsApp en tiempo real)"
    echo ""
    echo -e "  3. Enviar Lead de Marketplace"
    echo -e "     (Manual: Ingresar lead de Facebook)" 
    echo ""
    echo -e "  4. Generar Resumen IA"
    echo -e "     (El cerebro analiza todo y genera reporte)"
    echo ""
    echo -e "  5. Analizar Lead (Precio vs Mercado)"
    echo -e "     (Pega link de Neoauto y obtiene valuacion IA)"
    echo ""
    echo -e "  6. RESET DB (Borrar todo)"
    echo -e "     (Elimina tareas, mensajes y leads)"
    echo ""
    echo -e "  7. Secuencia Diaria (1 DIA)"
    echo -e "     (Scrapea Neoauto [publicado=1dia] + Reportes + Email)"
    echo ""
    echo -e "  8. Kill Zombies (Limpiar Procesos)"
    echo ""
    echo -e "  9. Resetear Token Google (Solucion Error 403)"
    echo -e " 10. Responder a Acreedores"
    echo ""
    echo -e "${CYAN} 11. Ejecutar Proceso Semanal${NC}"
    echo -e "${CYAN}     (8 Workers Paralelos + Monitor)${NC}"
    echo ""
    echo -e "${YELLOW} 12. Secuencia Completa Semanal${NC}"
    echo -e "${YELLOW}     (Scraping + Procesamiento + Reportes + Email + Apagado)${NC}"
    echo ""
    echo -e "  0. Salir"
    echo ""
    echo -e "${GREEN}==================================================${NC}"
    echo ""
    
    read -p "Ingrese su opcion: " opcion
    
    case $opcion in
        1)
            # PROCESAR CORREOS
            clear
            echo -e "${GREEN}PROCESANDO CORREOS Y ENVIANDO WHATSAPPS${NC}"
            cd "$CURRENT_DIR"
            python3 auto_contact_neoauto.py
            pause_script
            ;;
        2)
            # LISTENER
            clear
            echo -e "${GREEN}ACTIVANDO LISTENER (Monitoreo Continuo)${NC}"
            echo "Presiona Ctrl+C para detener el listener"
            cd "$CURRENT_DIR"
            python3 whatsapp_listener.py
            pause_script
            ;;
        3)
            # MARKETPLACE
            clear
            echo -e "${GREEN}ENVIAR LEAD DE MARKETPLACE${NC}"
            cd "$CURRENT_DIR"
            python3 enviar_lead_marketplace.py
            pause_script
            ;;
        4)
            # RESUMEN IA
            clear
            echo -e "${GREEN}GENERANDO RESUMEN IA${NC}"
            cd "$CURRENT_DIR"
            python3 crm_brain.py
            pause_script
            ;;
        5)
            # ANALIZAR LEAD
            clear
            echo -e "${GREEN}ANALIZADOR DE PRECIOS CON IA${NC}"
            read -p "Pega el Link del Auto (Neoauto): " URL_LEAD
            cd "$PROJECT_ROOT" # Navigate to root if analyze_lead is there, or adjust path
            # Original bat: python "..\Autos.Richard.Gutierrez\analyze_lead.py" "%URL_LEAD%"
            python3 "$PROJECT_ROOT/Autos.Richard.Gutierrez/analyze_lead.py" "$URL_LEAD"
            pause_script
            ;;
        6)
            # RESET DB
            clear
            echo -e "${RED}RESET DATABASE (BORRADO TOTAL)${NC}"
            cd "$CURRENT_DIR"
            python3 reset_full_db.py
            pause_script
            ;;
        7)
            # SECUENCIA DIARIA
            clear
            echo -e "${GREEN}INICIANDO SECUENCIA DIARIA (Modo: 1 DIA)${NC}"
            cd "$PROJECT_ROOT"
            
            echo "Lanzando Worker..."
            open_new_window "Worker Scraper Daily" "cd '$PROJECT_ROOT' && bash run_scraper_sequence_diario.sh"
            
            echo "Lanzando Monitor Unificado (Diario)..."
            # Lanzar monitor unificado apuntando al log diario y 6 workers
            bash "$PROJECT_ROOT/launch_monitor.sh" "$PROJECT_ROOT/scraper_sequence.log" 6
            
            pause_script
            ;;
        8)
            # KILL ZOMBIES
            clear
            echo -e "${GREEN}KILL ZOMBIES (Limpiar Procesos)${NC}"
            # Linux equivalent of kill zombies
            pkill -f "chrome"
            pkill -f "python"
            pkill -f "firefox"
            echo "Procesos eliminados (si existian)."
            pause_script
            ;;
        9)
            # RESET GOOGLE TOKEN
            clear
            echo -e "${GREEN}RESETEAR TOKEN DE GOOGLE${NC}"
            TOKEN_PATH="$PROJECT_ROOT/gmail_sender/token.json"
            if [ -f "$TOKEN_PATH" ]; then
                rm "$TOKEN_PATH"
                echo "[OK] Token eliminado."
            else
                echo "[INFO] No se encontro token.json (ya estaba borrado)."
            fi
            
            echo ""
            read -p "¿Desea iniciar la autenticación ahora mismo? (s/n): " auth_confirm
            if [[ $auth_confirm == "s" || $auth_confirm == "S" ]]; then
                echo "Iniciando script de autenticación..."
                python3 "$PROJECT_ROOT/auth_only.py"
            else
                echo "Recuerde ejecutar la Opcion 1 o este script mas tarde para loguearse."
            fi
            
            pause_script
            ;;
        10)
            # RESPONDER ACREEDORES
            clear
            echo -e "${GREEN}RESPONDER A ACREEDORES${NC}"
            ACREEDORES_DIR="$PROJECT_ROOT/rpta.automatica.acreedores"
            
            open_new_window "AutoReply" "cd '$ACREEDORES_DIR' && python3 auto_reply_acreedores_v1.py"
            open_new_window "TailLog" "cd '$ACREEDORES_DIR' && python3 tail_auto_reply_log.py"
            
            pause_script
            ;;
        11)
            # PROCESO SEMANAL
            clear
            echo -e "${CYAN}==================================================${NC}"
            echo -e "${CYAN}  EJECUTAR PROCESO SEMANAL (PARALELO)${NC}"
            echo -e "${CYAN}==================================================${NC}"
            
            cd "$PROJECT_ROOT"
            
            echo ""
            echo "1. Lanzar Scraping (8 Workers)"
            echo "2. Abrir solo Monitor"
            echo "3. Ejecutar pasos posteriores (JSON, Upload, Reporte)"
            echo "0. Volver"
            echo ""
            read -p "Seleccione opcion: " subopcion
            
            case $subopcion in
                1)
                    echo "Lanzando workers en background..."
                    # Check if already running
                    if pgrep -f "parallel_launcher_semanal.py" > /dev/null; then
                        echo -e "${YELLOW}AVISO: Ya parece haber un proceso corriendo.${NC}"
                        read -p "¿Lanzar de todos modos? (s/n): " confirm
                        if [[ $confirm != "s" ]]; then break; fi
                    fi
                    
                    # Usar el script de background que creamos
                    bash "$PROJECT_ROOT/start_background_scraper.sh"
                    
                    echo "Abriendo monitor unificado..."
                    sleep 2
                    bash "$PROJECT_ROOT/launch_monitor.sh" "$PROJECT_ROOT/nohup_scraper_semanal.out" 8
                    ;;
                2)
                    bash "$PROJECT_ROOT/launch_monitor.sh" "$PROJECT_ROOT/nohup_scraper_semanal.out" 8
                    ;;
                3)
                    # Implement interactive sub-menu for steps 4-8? Or just run them?
                    echo "Pasos posteriores aun no automatizados en este menu."
                    echo "Ejecute manualmente los scripts python."
                    ;;
                *)
                    ;;
            esac
            pause_script
            ;;
        12)
            # SECUENCIA COMPLETA SEMANAL
            clear
            echo -e "${YELLOW}==================================================${NC}"
            echo -e "${YELLOW}  SECUENCIA COMPLETA SEMANAL${NC}"
            echo -e "${YELLOW}==================================================${NC}"
            echo ""
            echo -e "${YELLOW}Este proceso ejecutará:${NC}"
            echo "  - Scraping paralelo (8 workers)"
            echo "  - Procesamiento de datos (TXT a JSON)"
            echo "  - Subida a Supabase"
            echo "  - Generación de reportes (HTML y PDF)"
            echo "  - Subida a Google Drive"
            echo "  - Envío de correo con adjuntos"
            echo "  - Apagado del equipo (ACTIVADO)"
            echo ""
            echo -e "${RED}ADVERTENCIA: Este proceso puede tomar varias horas y APAGARA SU EQUIPO AL TERMINAR.${NC}"

            echo ""
            read -p "¿Desea continuar? (s/n): " confirm_semanal
            
            if [[ $confirm_semanal == "s" || $confirm_semanal == "S" ]]; then
                cd "$PROJECT_ROOT"
                echo "Lanzando secuencia completa semanal en nueva ventana..."
                open_new_window "Secuencia Semanal Completa" "cd '$PROJECT_ROOT' && bash run_scraper_semanal.sh"
                echo ""
                echo -e "${GREEN}Proceso lanzado en nueva ventana.${NC}"
                echo "Puede monitorear el progreso en: $PROJECT_ROOT/scraper_sequence_semanal.log"
            else
                echo "Operación cancelada."
            fi
            
            pause_script
            ;;
        0)
            echo "Hasta luego!"
            exit 0
            ;;
        *)
            echo -e "${RED}Opcion invalida.${NC}"
            sleep 1
            ;;
    esac
done
