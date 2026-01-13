"""
Enviar mensaje de WhatsApp al 991090016 usando Selenium (método del bot principal)
"""

import os
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Datos del mensaje
telefono = "991090016"
mensaje = "Hola! Este es un mensaje de prueba desde el bot. Verificando que todo funcione correctamente con el nuevo número de WhatsApp Business. Saludos!"

print("=" * 70)
print("ENVIANDO MENSAJE DE WHATSAPP AL 991090016")
print("=" * 70)
print(f"\nNúmero destino: +51{telefono}")
print(f"Mensaje: {mensaje}\n")

# Configurar Chrome con el perfil del bot
print("Iniciando Chrome Driver...")
chrome_options = Options()
current_dir = os.path.dirname(os.path.abspath(__file__))
profile_dir = os.path.join(current_dir, "whatsapp_bot_profile")
chrome_options.add_argument(f"user-data-dir={profile_dir}")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    selenium_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=selenium_service, options=chrome_options)
    
    print("\n" + "="*50)
    print("IMPORTANTE: Si es la primera vez, ESCANEA EL QR DE WHATSAPP AHORA.")
    print("El script esperará hasta 2 minutos a que inicies sesión...")
    print("="*50 + "\n")
    
    # Abrir WhatsApp Web primero para logueo
    driver.get("https://web.whatsapp.com")
    
    # Esperar hasta que aparezca el panel lateral (indicador de login exitoso)
    try:
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.ID, "side"))
        )
        print("✓ Login detectado exitosamente. Continuando...\n")
    except:
        print("⚠️ Tiempo de espera agotado. Asegúrate de escanear el QR a tiempo.\n")
    
    # Enviar mensaje
    print(f"Enviando mensaje a +51{telefono}...")
    
    encoded_message = urllib.parse.quote(mensaje)
    url = f"https://web.whatsapp.com/send?phone=51{telefono}&text={encoded_message}"
    
    driver.get(url)
    print("Esperando carga del chat...")
    time.sleep(5)
    
    try:
        # Estrategia 1: Buscar botón enviar
        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send'] | //button[@aria-label='Enviar']"))
        )
        send_button.click()
        print("✓ Click en botón enviar")
    except:
        print("Botón no encontrado. Intentando ENTER en el input del footer...")
        # Estrategia 2: Buscar caja de texto y dar ENTER
        text_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
        )
        text_box.send_keys(Keys.ENTER)
        print("✓ Enviado con ENTER en input del footer")
    
    # Esperar para asegurar que salga el mensaje
    print("\nEsperando confirmación de envío...")
    time.sleep(20)
    
    print("\n" + "=" * 70)
    print("✅ MENSAJE ENVIADO EXITOSAMENTE")
    print("=" * 70)
    print(f"\nVerifica en WhatsApp Business (+51{telefono}) que el mensaje llegó correctamente.")
    
    input("\nPresiona ENTER para cerrar el navegador...")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
finally:
    if 'driver' in locals():
        driver.quit()
        print("\n✓ Chrome cerrado.")
