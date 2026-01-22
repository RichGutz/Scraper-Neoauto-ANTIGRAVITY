import os
import sys
import time
import subprocess
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def send_whatsapp_message(telefono, mensaje, silent=False):
    """
    Envía un mensaje de WhatsApp usando Selenium y WhatsApp Web
    VERSIÓN LITE: Solo texto (Links incluidos en el texto)
    """
    if not silent:
        print("=" * 70)
        print(f"ENVIANDO MENSAJE DE WHATSAPP AL {telefono}")
        print("=" * 70)
        print(f"\nNúmero destino: +51{telefono}")
        print(f"Mensaje: {mensaje[:50]}...")
    
    # 1. Cerrar Chrome si está abierto
    if not silent:
        print("\nCerrando Chrome si está abierto...")
    subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, capture_output=True)
    time.sleep(2)
    
    # 2. Configurar Chrome con el perfil del bot
    if not silent:
        print("Iniciando Chrome Driver...")
    
    chrome_options = Options()
    
    # Soporte para PyInstaller/Frozen (buscar carpeta junto al EXE)
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        profile_dir = os.path.join(base_dir, "whatsapp_bot_profile")
    else:
        # En modo Python normal, usar el perfil compartido en whatsapp_bot
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(base_dir)
        profile_dir = os.path.join(root_dir, "whatsapp_bot", "whatsapp_bot_profile")
    
    print(f"Usando perfil Chrome en: {profile_dir}")
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("detach", True)
    
    try:
        selenium_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=selenium_service, options=chrome_options)
        
        if not silent:
            print("\n" + "="*50)
            print("IMPORTANTE: Si es la primera vez, ESCANEA EL QR DE WHATSAPP AHORA.")
            print("El script esperará hasta 2 minutos a que inicies sesión...")
            print("="*50 + "\n")
        
        # 3. Abrir WhatsApp Web
        driver.get("https://web.whatsapp.com")
        
        # 4. Esperar login
        try:
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.ID, "side"))
            )
            if not silent:
                print("✓ Login detectado exitosamente.\n")
        except:
            if not silent:
                print("⚠️ Tiempo de espera agotado.\n")
        
        # 5. ENVIAR MENSAJE DE TEXTO
        if not silent:
            print(f"Enviando mensaje a +51{telefono}...")
        
        # Codificar mensaje en la URL 
        encoded_message = urllib.parse.quote(mensaje)
        url = f"https://web.whatsapp.com/send?phone=51{telefono}&text={encoded_message}"
        
        driver.get(url)
        if not silent:
            print("Esperando carga del chat...")
        time.sleep(5)
        
        try:
            # Estrategia 1: Buscar botón enviar
            send_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send'] | //button[@aria-label='Enviar']"))
            )
            send_button.click()
            if not silent:
                print("✓ Click en botón enviar")
        except:
            if not silent:
                print("Botón no encontrado. Intentando ENTER en el input del footer...")
            # Estrategia 2: Buscar caja de texto y dar ENTER
            text_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
            )
            text_box.send_keys(Keys.ENTER)
            if not silent:
                print("✓ Enviado con ENTER en input del footer")
        
        
        # Esperar confirmación visual breve
        if not silent:
            print("\nEsperando confirmación de envío...")
        time.sleep(5)
        
        if not silent:
            print("\n" + "=" * 70)
            print("✅ PROCESO COMPLETADO")
            print("=" * 70)
            print(f"\nVerifica en WhatsApp (+51{telefono}) que el mensaje llegó.")
            print("Chrome permanece abierto para revisión.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
        return False
