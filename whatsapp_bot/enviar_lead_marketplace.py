"""
Script para enviar mensaje a lead de Facebook Marketplace
Solicita: Link, Nombre, Celular
Guarda en BD y envía WhatsApp
"""

import os
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuración
SCOPES = ['https://www.googleapis.com/auth/contacts']
BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_DIR = BASE_DIR / "gmail_sender" # Pointing to valid credentials location
TOKEN_PATH = CREDENTIALS_DIR / 'token.json'
CREDENTIALS_PATH = CREDENTIALS_DIR / 'credentials.json'

def autenticar_google():
    """Autenticación con Google"""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(f"ERROR: 'credentials.json' no encontrado en {CREDENTIALS_PATH}")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def init_db():
    """Inicializar conexión a Supabase"""
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

def create_google_contact(creds, nombre, telefono, info_auto):
    """Crea un contacto en Google usando People API"""
    try:
        service_people = build('people', 'v1', credentials=creds)
        
        print(f"\nCreando contacto Google: {nombre} - {info_auto} (+51{telefono})...")
        
        contact_body = {
            "names": [{
                "givenName": nombre,
                "familyName": info_auto,
                "displayName": f"{nombre} - {info_auto}"
            }],
            "phoneNumbers": [{
                "value": f"+51{telefono}",
                "type": "mobile"
            }],
            "organizations": [{
                "name": "Marketplace Lead",
                "title": info_auto
            }],
            "memberships": [{
                "contactGroupMembership": {
                    "contactGroupResourceName": "contactGroups/myContacts"
                }
            }]
        }
        
        service_people.people().createContact(body=contact_body).execute()
        
        print(f"Contacto creado exitosamente (+51{telefono}).")
        return True
    except Exception as e:
        print(f"Error creando contacto Google: {e}")
        return False

def enviar_whatsapp(driver, telefono, mensaje):
    """Envía mensaje por WhatsApp Web usando Selenium"""
    try:
        encoded_message = urllib.parse.quote(mensaje)
        url = f"https://web.whatsapp.com/send?phone=51{telefono}&text={encoded_message}"
        
        print(f"\nAbriendo WhatsApp para {telefono}...")
        driver.get(url)
        
        print("Esperando carga del chat...")
        time.sleep(5)
        
        try:
            # Estrategia 1: Buscar botón enviar
            send_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send'] | //button[@aria-label='Enviar']"))
            )
            send_button.click()
            print("Click en enviar (Botón).")
        except:
            print("Botón no encontrado. Intentando ENTER en el input del footer...")
            # Estrategia 2: Buscar caja de texto y dar ENTER
            text_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
            )
            text_box.send_keys(Keys.ENTER)
            print("Enviado con ENTER en input del footer.")
        
        # Esperar para asegurar que salga el mensaje
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"Error enviando WhatsApp a {telefono}: {e}")
        return False

def main():
    print("=" * 70)
    print("ENVIAR MENSAJE A LEAD DE MARKETPLACE")
    print("=" * 70)
    print()
    print("Presiona ENTER sin escribir nada en el primer campo para cancelar")
    print()
    
    # Solicitar datos
    link = input("Link del vehiculo en Marketplace: ").strip()
    
    # Permitir cancelar presionando Enter
    if not link:
        print("\nOperacion cancelada. Regresando al menu...")
        return
    
    nombre = input("Nombre del vendedor: ").strip()
    telefono = input("Celular (9 digitos): ").strip()
    
    if not nombre or not telefono:
        print("\nERROR: Todos los campos son obligatorios.")
        return
    
    if len(telefono) != 9 or not telefono.isdigit():
        print("\nERROR: El celular debe tener 9 digitos.")
        return
    
    print(f"\nDatos ingresados:")
    print(f"  Link: {link}")
    print(f"  Nombre: {nombre}")
    print(f"  Celular: +51{telefono}")
    print()
    
    # Conectar a Supabase
    supabase = init_db()
    if not supabase:
        print("ADVERTENCIA: No se pudo conectar a Supabase. Continuando sin guardar en BD.")
    
    # Guardar en BD
    if supabase:
        try:
            lead_data = {
                "phone": telefono,
                "name": nombre,
                "status": "CONTACTED",
                "car_url": link,
                "last_interaction": datetime.now().isoformat()
            }
            supabase.table("crm_leads").upsert(lead_data).execute()
            print("Lead guardado en BD.")
        except Exception as e:
            print(f"Error guardando en BD: {e}")
    
    # Autenticar Google y crear contacto
    creds = autenticar_google()
    if creds:
        create_google_contact(creds, nombre, telefono, "Marketplace Lead")
    
    # Cerrar Chrome si está abierto
    print("\nCerrando Chrome si está abierto...")
    import subprocess
    subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, capture_output=True)
    time.sleep(2)
    print("Chrome cerrado\n")
    
    # Inicializar Selenium
    print("Iniciando Chrome Driver...")
    chrome_options = Options()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(current_dir, "whatsapp_bot_profile")
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("detach", True)  # Mantener Chrome abierto
    
    try:
        selenium_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=selenium_service, options=chrome_options)
        
        # Abrir WhatsApp Web
        driver.get("https://web.whatsapp.com")
        
        # Esperar login
        try:
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "side"))
            )
            print("Login detectado exitosamente.\n")
        except:
            print("Tiempo de espera agotado. Asegúrate de escanear el QR a tiempo.\n")
        
        # Enviar WhatsApp
        primer_nombre = nombre.split()[0]
        mensaje_texto = f"Hola {primer_nombre}! Mi nombre es Richard Gutierrez. Vi tu vehículo en Marketplace: {link}. Por favor, quisiera saber donde y en que horarios se puede ver el vehiculo?. Gracias. RG"
        
        exito = enviar_whatsapp(driver, telefono, mensaje_texto)
        
        if exito:
            print("\nMensaje enviado con exito.")
        else:
            print("\nFallo al enviar mensaje.")
        
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
