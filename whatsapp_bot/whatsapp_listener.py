"""
WhatsApp Listener (Parte 1 del CRM Agent)

Este script:
1. Reutiliza la sesión de Chrome del bot de contacto.
2. Se mantiene abierto monitoreando WhatsApp Web.
3. (MVP) Imprime los títulos de los chats visibles en la lista lateral.
"""

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

# --- DATABASE CONNECTION ---
def init_db():
    try:
        current_script_dir = Path(__file__).resolve().parent
        dotenv_path = current_script_dir / ".env"
        
        load_dotenv(dotenv_path)
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print(f"ERROR: No se encontraron credenciales en {dotenv_path}")
            return None
            
        print(f"Conectando a Supabase ({url})... key prefix: {key[:5]}...")
        return create_client(url, key)
    except Exception as e:
        print(f"Conectando a Supabase ({url})... key prefix: {key[:5]}...")
        return create_client(url, key)
    except Exception as e:
        print(f"Error conectando a DB: {e}")
        return None

def check_message_exists(supabase, phone, content, sender):
    """Check if a message with same content and sender exists for this lead (simple de-dupe)"""
    try:
        # Check if identical message exists in the last 50 messages for this lead
        # This is a 'soft' check. Ideally we'd use a unique ID from WhatsApp.
        response = supabase.table("crm_messages").select("id").eq("lead_phone", phone).eq("content", content).eq("sender", sender).limit(1).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error verifying duplicate: {e}")
        return False


def start_driver():
    print("Iniciando Chrome Driver (Listener Mode)...")
    chrome_options = Options()
    
    # Reutilizar el MISMO perfil que el bot de contacto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(current_dir, "whatsapp_bot_profile")
    
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("detach", True) # Mantener abierto
    # chrome_options.add_argument("--headless") # Jamás headless para WhatsApp Web
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error fatal iniciando driver: {e}")
        return None

def force_kill_chrome():
    """Mata procesos de Chrome para liberar el perfil"""
    print("🧹 Limpiando sesiones anteriores de Chrome...")
    try:
        if os.name == 'nt': # Windows
            os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
            os.system("taskkill /F /IM chromedriver.exe /T >nul 2>&1")
        else: # Linux/Mac
            os.system("pkill -f chrome")
            os.system("pkill -f chromedriver")
        time.sleep(2) # Dar tiempo para liberar archivos
    except Exception as e:
        print(f"Advertencia matando Chrome: {e}")

def main():
    # 1. Verificar conexión a DB antes de abrir navegador
    supabase = init_db()
    if not supabase:
        print("ABORTANDO: Falló conexión a Supabase.")
        return

    # 2. Limpiar Chrome antes de empezar (Fix Profile Locked)
    force_kill_chrome()

    driver = start_driver()
    if not driver: return

    try:
        driver.get("https://web.whatsapp.com")
        
        print("Esperando login (Side Panel)...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "side"))
        )
        print("Login OK. Iniciando monitoreo de chats...")
        
        # --- ESCANEO UNICO (NO LOOP) ---
        print("Iniciando escaneo de chats (una sola vez)...")
        
        try:
            # 1. Obtener lista de chats (buscamos el panel lateral)
            # Selectores típicos de WWeb (pueden cambiar, usar con cuidado)
            chats = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
            
            print(f"\nDetectados {len(chats)} chats visibles.")
            
            for i in range(min(15, len(chats))): # Limitado a 15 chats para asegurar leer los 10 activos
                try:
                    # Re-capturar lista de chats para evitar StaleElementReferenceException
                    chats = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
                    if i >= len(chats):
                        break
                    
                    chat = chats[i]
                    
                    # Extraer info básica del preview
                    chat_text = chat.text.split('\n')
                    # Estructura usual: [Hora, Nombre, Mensaje, ...] o [Nombre, Hora, Mensaje...]
                    # Es difuso, pero intentamos pillar el nombre
                    possible_name = chat_text[0] 
                    
                    # Clic en el chat para abrirlo
                    chat.click()
                    time.sleep(2) # Esperar carga de mensajes
                    
                    # 2. Extraer teléfono/identificador
                    # Intentamos sacar el teléfono del header del chat activo
                    try:
                        header_title = driver.find_element(By.CSS_SELECTOR, "header div[role='button'] span[dirname]")
                        phone_or_name = header_title.text # Puede ser "51999..." o "Juan Perez"
                    except:
                        phone_or_name = possible_name

                    # Normalizar ID (Teléfono o Nombre)
                    # Si tiene letras, asumimos que es un NOMBRE guardado (ej: "Juan", "Toyota 2020")
                    # Si NO tiene letras, asumimos que es un TELEFONO (ej: "+51 999 999 999")
                    has_letters = any(c.isalpha() for c in phone_or_name)
                    
                    if has_letters:
                        # Es un nombre, lo usamos tal cual como ID
                        clean_phone = phone_or_name
                        is_phone = False
                    else:
                        # Es un numero, limpiamos todo lo que no sea digito
                        is_phone = True
                        clean_phone = ''.join(filter(str.isdigit, phone_or_name))
                        
                        # Normalizar Peru: Si tiene 11 digitos y empieza con 51, quitar el 51
                        if len(clean_phone) == 11 and clean_phone.startswith("51"):
                            clean_phone = clean_phone[2:]
                    
                    print(f"--> Analizando chat: {phone_or_name} (ID: {clean_phone})")

                    # IGNORAR mensajes de sistema de cifrado
                    if "end-to-end encrypted" in phone_or_name.lower():
                        print("   [SKIP] Chat de sistema ignorado.")
                        continue

                    # 3. Guardar/Actualizar LEAD en Supabase
                    try:
                        # Upsert lead
                        lead_data = {
                            "phone": clean_phone,
                            "name": phone_or_name if not is_phone else "Desconocido",
                            "status": "CONTACTED",
                            "last_interaction": datetime.now().isoformat()
                        }
                        supabase.table("crm_leads").upsert(lead_data).execute()
                    except Exception as e:
                        print(f"Error guardando lead: {e}")

                    # 4. Leer Mensajes (Scraping Mejorado)
                    # Intentar scrollear hacia arriba para cargar mas mensajes
                    try:
                        # Buscamos el div que tiene overflow-y: scroll
                        # Selector mas genérico para asegurar que lo encontramos
                        msg_scroll = driver.find_element(By.CSS_SELECTOR, "div[id='main'] div[data-testid='conversation-panel-messages']")
                        
                        print(f"   Scrolleando para cargar historial...")
                        # Scroll up (mas intentos para ir mas atras)
                        for _ in range(15):
                            driver.execute_script("arguments[0].scrollTop = 0;", msg_scroll)
                            time.sleep(1.5) # Dar tiempo a que cargue el spinner
                    except Exception as e:
                        print(f"   Advertencia scroll: {e}")

                    # Buscar contenedores de mensajes de nuevo
                    msg_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in') or contains(@class, 'message-out')]")
                    
                    total_found = len(msg_containers)
                    print(f"   Mensajes en DOM encontrados: {total_found}")
                    
                    new_msgs_count = 0
                    # Aumentamos limite a 100 mensajes
                    for msg in msg_containers[-100:]: 
                        try:
                            # Determinar sender y timestamp REAL usando metadata
                            # WhatsApp suele poner data-pre-plain-text="[10:30, 2/1/2026] +51 999: "
                            # Este atributo esta en un div interno
                            
                            real_timestamp = datetime.now().isoformat()
                            sender_type = "LEAD" # Default
                            
                            try:
                                # Buscar el elemento copyable para metadata
                                copyable = msg.find_element(By.CSS_SELECTOR, "div.copyable-text")
                                metadata = copyable.get_attribute("data-pre-plain-text")
                                
                                if metadata:
                                    # metadata format: "[14:24, 02/01/2026] Nombre: "
                                    # Extraer si soy yo o el lead
                                    if "You:" in metadata or "Tú:" in metadata: # Depende idioma WWeb
                                        # Alternativa: ver clase message-out
                                        pass
                                    
                                    # Timestamp parsing simple (guardamos el string crudo si falla parsing)
                                    # O mejor: usamos el sender de la clase CSS que es mas seguro
                                    pass
                            except:
                                pass

                            # Sender por CSS (Mas confiable que el texto)
                            classes = msg.get_attribute("class")
                            sender = "LEAD" if "message-in" in classes else "ME"
                            
                            # Extraer texto
                            content = ""
                            try:
                                # Estrategia 1: copyable-text (contiene el texto real seleccionable)
                                text_element = msg.find_element(By.CSS_SELECTOR, "span.selectable-text")
                                content = text_element.text
                            except:
                                try:
                                    # Estrategia 2: Cualquier span con texto
                                    content = msg.text.split('\n')[0]
                                except:
                                    pass
                            
                            if not content: continue

                            # Verificar duplicados
                            if check_message_exists(supabase, clean_phone, content, sender):
                                continue
                            
                            # Guardar en Supabase
                            msg_data = {
                                "lead_phone": clean_phone,
                                "sender": sender,
                                "content": content,
                                "timestamp": real_timestamp, # TODO: Mejorar esto con el timestamp real parseado
                                "processed": False
                            }
                            
                            supabase.table("crm_messages").insert(msg_data).execute()
                            new_msgs_count += 1
                            
                        except Exception as e:
                            pass
                    
                    print(f"   Mensajes guardados: {new_msgs_count}")
                    
                except Exception as e:
                    print(f"Error procesando chat {i}: {e}")
                    continue
            
            print("\n=== ESCANEO COMPLETADO ===")
            print("Todos los chats han sido procesados. La ventana quedara abierta.")
                
        except Exception as e:
            print(f"Error en escaneo: {e}")

    except Exception as e:
        print(f"Error general: {e}")
    finally:
        print("Manteniendo navegador abierto. Cierre manualmente si lo desea.")
        # driver.quit() # COMENTADO PARA NO CERRAR CHROME

if __name__ == "__main__":
    main()
