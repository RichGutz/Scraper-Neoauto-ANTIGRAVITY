import pandas as pd
import os
import sys
import time
import subprocess
from colorama import init, Fore, Style

# Agregar directorio padre para importar modulos
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from whatsapp_bot.whatsapp_sender import send_whatsapp_message
# Importar localmente (ahora que copiamos el archivo)
from whatsapp_sender import send_whatsapp_message

init(autoreset=True)

BROCHURE_JACARANDA = "BROCHURE JACARANDA (9).pdf"
BROCHURE_LOMAS = "Brochure Lomas Park Tangible_ (2) (2).pdf"

def get_base_dir():
    # Detectar si estamos corriendo como ejecutable (PyInstaller)
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_brochure_path(proyecto):
    if not isinstance(proyecto, str):
        return None
    
    proyecto = proyecto.lower()
    base_dir = get_base_dir()
    
    if "jacaranda" in proyecto:
        return os.path.join(base_dir, BROCHURE_JACARANDA)
    elif "lomas" in proyecto:
        return os.path.join(base_dir, BROCHURE_LOMAS)
    return None

def main():
    print(f"{Fore.MAGENTA}===========================================")
    print(f"{Fore.MAGENTA}   ANNY BOT - ENVIO MASIVO WHATSAPP")
    print(f"{Fore.MAGENTA}===========================================")
    print("")

    # 1. Solicitar archivo
    base_dir = get_base_dir()
    while True:
        file_input = input(f"{Fore.YELLOW}Ingrese el nombre del archivo Excel (ej: lista.xlsx): {Style.RESET_ALL}").strip()
        # Permitir al usuario arrastrar el archivo (quita comillas)
        file_input = file_input.replace('"', '')
        
        if os.path.exists(file_input):
            excel_path = file_input
            break
        elif os.path.exists(os.path.join(base_dir, file_input)):
             excel_path = os.path.join(base_dir, file_input)
             break
        else:
            print(f"{Fore.RED}El archivo no existe. Intente nuevamente.")
    
    # 2. Modo Pruebas
    test_mode_input = input(f"{Fore.CYAN}Modo Pruebas? (S/N) [Default: S]: {Style.RESET_ALL}").strip().upper()
    is_test_mode = test_mode_input != 'N'
    
    test_phone = "977435838" # Default backup (User's number)
    if is_test_mode:
        phone_input = input(f"{Fore.CYAN}Ingrese celular para recibir TODAS las pruebas (Default: {test_phone}): {Style.RESET_ALL}").strip()
        if phone_input:
            test_phone = phone_input
        print(f"{Fore.GREEN}MODO PRUEBAS ACTIVADO. Todos los mensajes iran a: {test_phone}")
    else:
        print(f"{Fore.RED}!!! MODO PRODUCCION !!! Se enviaran mensajes a los clientes REALES.")
        confirm = input("Escriba 'CONFIRMAR' para continuar: ")
        if confirm != "CONFIRMAR":
            print("Cancelado.")
            return

    # 3. Leer Excel
    try:
        print(f"\nLeyendo archivo...")
        df = pd.read_excel(excel_path)
        print(f"Se encontraron {len(df)} registros.")
    except Exception as e:
        print(f"{Fore.RED}Error leyendo Excel: {e}")
    except Exception as e:
        print(f"{Fore.RED}Error leyendo Excel: {e}")
        return

    # 3.5 Configurar Mensaje (NUEVO)
    plantilla_path = os.path.join(get_base_dir(), 'plantilla_mensaje.txt')
    
    # Crear plantilla si no existe (recuperacion)
    if not os.path.exists(plantilla_path):
        default_msg = "Hola [NOMBRE], gracias por consultar por [PROYECTO]."
        with open(plantilla_path, 'w', encoding='utf-8') as f:
            f.write(default_msg)
            
    while True:
        with open(plantilla_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        print(f"\n{Fore.MAGENTA}--- VISTA PREVIA DEL MENSAJE ---{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{template_content}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}--------------------------------{Style.RESET_ALL}")
        print(f"(Se usarán [NOMBRE] y [PROYECTO] como comodines)")
        
        edit_choice = input(f"\n{Fore.YELLOW}¿Deseas modificar este mensaje? (S/N): {Style.RESET_ALL}").strip().upper()
        
        if edit_choice == 'S':
            print(f"Abriendo editor de texto... {Fore.CYAN}Haz tus cambios, GUARDA y CIERRA el editor.{Style.RESET_ALL}")
            # Abrir notepad y esperar a que se cierre (o solo lanzarlo)
            # subprocess.call es bloqueante, ideal para esperar que termine de editar
            try:
                subprocess.call(['notepad.exe', plantilla_path])
            except:
                # Fallback mac/linux o si falla notepad
                if os.name == 'posix':
                    subprocess.call(['open', '-a', 'TextEdit', plantilla_path])
                else:
                    print("No se pudo abrir el editor. Abre 'plantilla_mensaje.txt' manualmente.")
                    input("Presiona ENTER cuando hayas guardado los cambios...")
        else:
            break

    # 4. Procesar
    print(f"\n{Fore.YELLOW}Iniciando envio...{Style.RESET_ALL}")
    
    for index, row in df.iterrows():
        nombre = str(row.get('Nombre', 'Cliente')).strip().split()[0]
        celular = str(row.get('TelefonoCelular', '')).replace('.0', '').strip()
        proyecto = str(row.get('Proyecto', ''))
        
        if not celular or celular == 'nan':
            print(f"Fila {index+1}: Sin celular. Saltando.")
            continue

        # Mensaje Base desde Plantilla
        mensaje = template_content.replace('[NOMBRE]', nombre).replace('[PROYECTO]', proyecto)

        # Archivo adjunto
        brochure_path = get_brochure_path(proyecto)
        
        # Destino real o test
        target_phone = test_phone if is_test_mode else celular
        
        print(f"\n[{index+1}/{len(df)}] Procesando {nombre} ({proyecto}) -> {target_phone}")
        if brochure_path:
            print(f"   Adjunto: {os.path.basename(brochure_path)}")
        else:
            print(f"   {Fore.RED}NO SE ENCONTRO BROCHURE PARA PROYECTO: {proyecto}{Style.RESET_ALL}")

        # Enviar
        success = send_whatsapp_message(target_phone, mensaje, attachment_path=brochure_path, silent=False)
        
        if success:
            print(f"{Fore.GREEN}   Exito.")
        else:
            print(f"{Fore.RED}   Fallo.")
            
        # Pausa entre mensajes para no saturar
        time.sleep(5)

    print(f"\n{Fore.MAGENTA}Proceso completado.")
    input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()
