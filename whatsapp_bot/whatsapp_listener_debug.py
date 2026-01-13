
"""
WhatsApp Listener DEBUG MODE
Version ruidosa para encontrar errores
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
from supabase import create_client
from pathlib import Path

def init_db():
    try:
        current_script_dir = Path(__file__).resolve().parent
        dotenv_path = current_script_dir / ".env"
        load_dotenv(dotenv_path)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key: return None
        return create_client(url, key)
    except Exception as e:
        print(f"DEBUG: Error DB Init: {e}")
        return None

def start_driver():
    print("DEBUG: Iniciando Chrome...")
    chrome_options = Options()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(current_dir, "whatsapp_bot_profile")
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"DEBUG: Error Driver: {e}")
        return None

def main():
    print("=== LISTENER DEBUG MODE ===")
    supabase = init_db()
    if not supabase:
        print("DEBUG: FALLO CONEXION DB")
        return

    driver = start_driver()
    if not driver: return

    try:
        driver.get("https://web.whatsapp.com")
        print("DEBUG: Esperando carga de WhatsApp...")
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "side")))
        print("DEBUG: Login OK")
        
        # BUSCAR CHATS
        time.sleep(5) # Esperar renderizado
        chats = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
        print(f"DEBUG: Encontrados {len(chats)} elementos div[role='row']")
        
        if len(chats) == 0:
            print("DEBUG: NO SE ENCONTRARON CHATS. Revisar selector.")
            # Intento alternativo de selector
            chats = driver.find_elements(By.XPATH, "//div[@aria-label='Lista de chats']")
            print(f"DEBUG: Intento alternativo 1: {len(chats)}")
        
        for i in range(min(5, len(chats))):
            print(f"\n--- Chat {i+1} ---")
            try:
                chats = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
                chat = chats[i]
                print(f"DEBUG: Texto raw del chat preview: {chat.text[:30]}...")
                
                chat.click()
                time.sleep(3)
                
                # INTENTAR SACAR NOMBRE
                try:
                    header = driver.find_element(By.CSS_SELECTOR, "header")
                    print(f"DEBUG: Header encontrado.")
                    # Buscar spans dentro del header
                    spans = header.find_elements(By.TAG_NAME, "span")
                    for s in spans:
                        txt = s.text
                        if txt and len(txt) > 0:
                            print(f"   DEBUG: Header span content: '{txt}'")
                except Exception as e:
                    print(f"DEBUG: Error leyendo header: {e}")
                
                # INTENTAR INSERTAR LEAD DE PRUEBA
                print("DEBUG: Intentando insertar lead de prueba en Supabase...")
                try:
                    res = supabase.table("crm_leads").upsert({
                        "phone": f"DEBUG_{i}",
                        "name": "Test Debug",
                        "status": "DEBUG",
                        "last_interaction": datetime.now().isoformat()
                    }).execute()
                    print(f"DEBUG: Insert Lead OK: {res.data}")
                except Exception as e:
                    print(f"DEBUG: Error insertando Lead: {e}")

            except Exception as e:
                print(f"DEBUG: Error en loop de chat: {e}")
                
    except Exception as e:
        print(f"DEBUG: Error General: {e}")
    finally:
        print("DEBUG: Finalizando.")
        # driver.quit() # Dejar abierto para ver

if __name__ == "__main__":
    main()
