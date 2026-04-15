"""
Script de Contacto Automático Neoauto (Gmail -> WhatsApp)

Este script:
1. Lee correos no leídos de 'contacto@neoauto.pe' en Gmail.
2. Extrae el número de teléfono y nombre del vendedor.
3. Envía un mensaje de WhatsApp automático (Usando Selenium).

NOTA: Para pruebas, el número de destino está HARCODEADO a 991090016.
"""

import os
import time
import base64
import re
import urllib.parse
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from supabase import create_client, Client

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Faltan librerías de Google. Instala: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib selenium webdriver-manager")
    exit()

# --- CONFIGURACIÓN ---
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/contacts', 'https://www.googleapis.com/auth/gmail.send']
NEOAUTO_EMAIL = 'contacto@neoauto.pe'
# TEST_MODE = True forces sending to the hardcoded number irrespective of what's in# TEST_PHONE_NUMBER = "918063088" 
# TEST_PHONE_NUMBER = "991090016"  # MODO PRUEBA DESACTIVADO - Envía a números reales 

# Directorios relativos para reutilizar credenciales existentes
BASE_DIR = Path(__file__).parent.parent # C:\Users\rguti\Scraper.Neoauto
CREDENTIALS_DIR = BASE_DIR / "gmail_sender" # Pointing to valid credentials location
TOKEN_PATH = CREDENTIALS_DIR / 'token.json'
CREDENTIALS_PATH = CREDENTIALS_DIR / 'credentials.json'

# --- LOGGING ---
import logging
LOG_FILE = Path(__file__).parent / 'auto_contact_neoauto.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def autenticar_google():
    """Reutiliza la lógica de autenticación existente"""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                logger.error(f"ERROR: 'credentials.json' no encontrado en {CREDENTIALS_PATH}")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds
    
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
            
        print(f"Conectando a Supabase ({url})...")
        return create_client(url, key)
    except Exception as e:
        print(f"Error conectando a DB: {e}")
        return None

def obtener_correos_neoauto(service):
    """Busca correos no leídos de Neoauto"""
    try:
        # Probar con filtros más amplios
        queries = [
            f'from:{NEOAUTO_EMAIL} is:unread',
            'from:neoauto.pe is:unread',
            'subject:neoauto is:unread'
        ]
        
        for query in queries:
            print(f"\nProbando query: {query}")
            results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
            messages = results.get('messages', [])
            print(f"  Resultados: {len(messages)} correos")
            
            if messages:
                print(f"  ✓ Usando este query")
                return messages
        
        print("\n⚠️  No se encontraron correos con ningún filtro")
        return []
        
    except Exception as e:
        logger.error(f"Error buscando correos: {e}")
        print(f"ERROR: {e}")
        return []

def extraer_datos_correo(service, msg_id):
    """Parsea el HTML del correo para sacar telefono, nombre y link"""
    try:
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        # Obtener cuerpo del mensaje
        payload = message.get('payload', {})
        parts = payload.get('parts', [])
        
        body = ""
        # Buscar el cuerpo HTML o Texto
        if not parts:
            body = payload.get('body', {}).get('data', "")
        else:
            for part in parts:
                if part['mimeType'] == 'text/html':
                    body = part['body'].get('data', "")
                    break
            if not body: # Fallback a texto plano
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        body = part['body'].get('data', "")
                        break
        
        if body:
            import base64
            body = base64.urlsafe_b64decode(body).decode('utf-8', errors='ignore')
        
        # --- HTML PARSING ---
        # Si parece HTML, usar BeautifulSoup para limpiar
        if "<html" in body.lower() or "<body" in body.lower():
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(body, 'html.parser')
                text_content = soup.get_text(separator=' ', strip=True)
            except ImportError:
                print("ERROR: Falta beautifulsoup4. Instala: pip install beautifulsoup4")
                text_content = body
        else:
            text_content = body

        # --- REGEX PARSING ---
        # Regex más flexible para soportar saltos de línea y espacios extra
        # Neoauto suele poner "Teléfono : 999999999" o similar
        telefono_match = re.search(r'Teléfono\s*[:\.]?\s*(\d{9})', text_content)
        telefono = telefono_match.group(1) if telefono_match else None

        # Nombre
        # Nombre (Extraemos nombre completo y primer nombre)
        contacto_match = re.search(r'Contacto\s*[:.]?\s*([^:\n\r]+)', text_content)
        if contacto_match:
            full_name = contacto_match.group(1).strip()
            # Limpiar: remover "Teléfono" si aparece al final
            full_name = re.sub(r'\s+Teléfono\s*$', '', full_name, flags=re.IGNORECASE)
            # Tomar solo la primera palabra para el saludo
            simple_name = full_name.split()[0]
        else:
            full_name = "Vendedor"
            simple_name = "Vendedor"
        
        if not telefono:
            print(f"ERROR PARSING {msg_id}: No se encontró teléfono.")
            print(f"TEXT CONTENT SNIPPET: {text_content[:200]}...") 
            return None
        
        # Link (Buscamos href en el HTML original o url en texto)
        # Regex mejorado para capturar la URL completa incluyendo subdirectorios (ej: /usado/slug)
        link_match = re.search(r'https?://neoauto\.com/auto/[\w\-/]+', body)
        link_auto = link_match.group(0) if link_match else "(Link no detectado)"
        
        # Extraer info del auto desde el link (slug)
        # Formato esperado: .../auto/usado/marca-modelo-ano-id
        # Ejemplo: .../hyundai-creta-2024-1860073
        info_auto = ""
        try:
            if link_auto and "neoauto.com" in link_auto:
                slug = link_auto.split('/')[-1] # "hyundai-creta-2024-1860073"
                parts = slug.split('-')
                # Quitamos el ID final si es numérico
                if parts and parts[-1].isdigit():
                    parts.pop()
                # Capitalizar
                info_auto = " ".join([p.capitalize() for p in parts])
        except:
            info_auto = "Auto Interes"

        return {
            'telefono_real': telefono,
            'nombre_completo': full_name,
            'nombre_simple': simple_name,
            'link': link_auto,
            'info_auto': info_auto,
            'msg_id': msg_id
        }

    except Exception as e:
        logger.error(f"Error parseando correo {msg_id}: {e}")
        return None

def create_google_contact(creds, contact_data):
    """Crea un contacto en Google usando People API"""
    try:
        service_people = build('people', 'v1', credentials=creds)
        
        # Formato: Nombre - Marca Modelo Año
        # info_auto viene del slug del link
        nombre_completo = contact_data['nombre_completo']
        info_auto = contact_data.get('info_auto', 'Auto')
        
        print(f"   Creando contacto Google: {nombre_completo} - {info_auto} (+51{contact_data['telefono_real']})...")
        
        # Estructura mejorada para mejor compatibilidad con WhatsApp Dual
        contact_body = {
            "names": [{
                "givenName": nombre_completo,
                "familyName": info_auto,  # Apellido = Info del auto
                "displayName": f"{nombre_completo} - {info_auto}"
            }],
            "phoneNumbers": [{
                "value": f"+51{contact_data['telefono_real']}",
                "type": "mobile"  # Tipo explícito
            }],
            "organizations": [{
                "name": "Neoauto Lead",
                "title": info_auto
            }],
            "memberships": [{
                "contactGroupMembership": {
                    "contactGroupResourceName": "contactGroups/myContacts"
                }
            }]
        }
        
        service_people.people().createContact(body=contact_body).execute()
        
        print(f"   -> Contacto creado exitosamente (+51{contact_data['telefono_real']}).")
        return True
    except Exception as e:
        print(f"   Error creando contacto Google: {e}")
        return False

from selenium.webdriver.common.keys import Keys

# ... (imports continue)

def enviar_whatsapp(driver, telefono, mensaje):
    """Envía mensaje por WhatsApp Web usando Selenium"""
    try:
        encoded_message = urllib.parse.quote(mensaje)
        url = f"https://web.whatsapp.com/send?phone={telefono}&text={encoded_message}"
        
        logger.info(f"Abriendo WhatsApp para {telefono}...")
        driver.get(url)
        
        # Esperar a que cargue la interfaz (buscamos el input de texto o el botón enviar)
        logger.info("Esperando carga del chat...")
        
        try:
            # Estrategia 1: Buscar botón enviar
            send_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send'] | //button[@aria-label='Enviar']"))
            )
            send_button.click()
            logger.info("Click en enviar (Botón).")
        except:
            logger.info("Botón no encontrado/clickeable. Intentando ENTER en el input del footer...")
            # Estrategia 2: Buscar caja de texto ESPECÍFICA (en el footer) y dar ENTER
            # WhatsApp Web suele tener el input en un footer
            text_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
            )
            text_box.send_keys(Keys.ENTER)
            logger.info("Enviado con ENTER en input del footer.")
        
        # Esperar un poco para asegurar que salga el mensaje
        time.sleep(20) # Aumentado a 20s por solicitud del usuario
        return True
        
    except Exception as e:
        logger.error(f"Error enviando WhatsApp a {telefono}: {e}")
        return False


def eliminar_correo(service, msg_id):
    """Mueve el correo a la papelera"""
    try:
        service.users().messages().trash(userId='me', id=msg_id).execute()
        logger.info(f"Correo {msg_id} movido a la papelera.")
    except Exception as e:
        logger.error(f"Error borrando correo {msg_id}: {e}")

def main():
    print("=== INICIANDO BOT GMAIL -> WHATSAPP ===")
    
    # 1. Autenticación Gmail y Supabase
    creds = autenticar_google()
    if not creds: return
    service = build('gmail', 'v1', credentials=creds)
    
    supabase = init_db()
    if not supabase:
        print("ADVERTENCIA: No se pudo conectar a Supabase. El bot continuará pero no guardará leads.")
    
    # 2. Buscar correos
    mensajes = obtener_correos_neoauto(service)
    print(f"Encontrados {len(mensajes)} correos nuevos de Neoauto.")
    
    if not mensajes:
        return

    # 3. Cerrar Chrome si está abierto (para evitar conflictos)
    print("\nCerrando Chrome y Brave si están abiertos...")
    import subprocess
    subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, capture_output=True)
    subprocess.run("taskkill /F /IM brave.exe /T", shell=True, capture_output=True)
    time.sleep(2)
    print("✓ Navegadores cerrados\n")


    # 3. Inicializar Selenium (Solo si hay mensajes)
    print("Iniciando Chrome Driver...")
    chrome_options = Options()
    # Usar perfil DEDICADO para el bot (creará la carpeta si no existe)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(current_dir, "whatsapp_bot_profile")
    chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("detach", True)  # Mantener Chrome abierto
    
    # chrome_options.add_argument("--headless") # NO usar headless para poder escanear QR
    
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            print(f"ADVERTENCIA: No se encontro Chrome en {chrome_path}")
            # Intentar sin ruta fija como fallback
        else:
            print(f"Usando binario de Chrome: {chrome_path}")
            chrome_options.binary_location = chrome_path

        selenium_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=selenium_service, options=chrome_options)
        
        print("\n" + "="*50)
        print("IMPORTANTE: Si es la primera vez, ESCANEA EL QR DE WHATSAPP AHORA.")
        print("El script esperará hasta 2 minutos a que inicies sesión...")
        print("="*50 + "\n")
        
        # Abrir WhatsApp Web primero para logueo
        driver.get("https://web.whatsapp.com")
        
        # Esperar intigentemente hasta que aparezca el panel lateral (indicador de login exitoso)
        try:
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "side"))
            )
            print("Login detectado exitosamente. Continuando...")
        except:
            print("Tiempo de espera agotado. Asegúrate de escanear el QR a tiempo.")
            # No cerramos aqui para permitir debug o reintentos en el loop, 
            # aunque los envíos fallarán si no hay login.
        
        # 4. Procesar Mensajes
        for msg in mensajes:
            datos = extraer_datos_correo(service, msg['id'])
            
            if datos:
                print(f"Procesando: {datos['nombre_completo']} - Tel Real: {datos['telefono_real']} - Link: {datos['link']}")
                
                # Guardar Lead en Supabase
                if supabase:
                    try:
                        lead_data = {
                            "phone": datos['telefono_real'],
                            "name": datos['nombre_completo'], # Guardar Nombre Completo (BD)
                            "status": "CONTACTED",
                            "car_url": datos['link'],
                            "last_interaction": datetime.now().isoformat()
                        }
                        supabase.table("crm_leads").upsert(lead_data).execute()
                        print("   -> Lead guardado en BD.")
                    except Exception as e:
                        print(f"   Error guardando en BD: {e}")
                
                 # --- GUARDAR EN GOOGLE CONTACTS ---
                create_google_contact(creds, datos)
               
                # Lógica de número de destino (Test vs Real)
                try:
                    telefono_destino = TEST_PHONE_NUMBER
                    print(f"*** MODO PRUEBA: Usando número {TEST_PHONE_NUMBER} en lugar de {datos['telefono_real']} ***")
                except NameError:
                    telefono_destino = datos['telefono_real']

                # Enviar WhatsApp
                mensaje_texto = f"Hola {datos['nombre_simple']}! Mi nombre es Richard Gutierrez. Vi tu vehículo en Neoauto: {datos['link']}. Por favor, quisiera saber donde y en que horarios se puede ver el vehiculo?. Gracias. RG"
                exito = enviar_whatsapp(driver, telefono_destino, mensaje_texto)
                
                if exito:
                    print("Mensaje enviado con éxito.")
                    # 5. ELIMINAR CORREO (Trash) si se procesó bien
                    eliminar_correo(service, msg['id'])
                else:
                    print("Fallo al enviar mensaje.")
            
            # Pequeña pausa entre correos para no saturar
            time.sleep(5)
            
    except Exception as e:
        print(f"Error general en Selenium: {e}")
    finally:
        if 'driver' in locals():
            print("\nProceso completado. Chrome permanece abierto.")
            print("Puedes revisar los mensajes y cerrar Chrome cuando quieras.")
            # NO cerrar Chrome - dejar que el usuario lo cierre manualmente
            # driver.quit()

if __name__ == "__main__":
    main()

