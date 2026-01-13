"""
Prueba de envío de mensaje al nuevo número de WhatsApp Business: 991090016
"""

import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Matar Chrome primero
print("Cerrando Chrome si está abierto...")
subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, capture_output=True)
time.sleep(2)
print("✓ Chrome cerrado\n")

# Datos del mensaje de prueba
nombre = "Equipo"
telefono = "991090016"  # NUEVO NÚMERO DE WHATSAPP BUSINESS
link_auto = "https://neoauto.com/auto/usado/toyota-corolla-2020-ejemplo"

# Mensaje de prueba
mensaje = f"Hola! Este es un mensaje de prueba al nuevo número de WhatsApp Business. Verificando que todo funcione correctamente. Saludos!"

print("=" * 70)
print("PRUEBA DE MENSAJE AL NUEVO NÚMERO DE WHATSAPP BUSINESS")
print("=" * 70)
print(f"\nNúmero destino: +51{telefono}")
print(f"Mensaje: {mensaje}\n")

# Iniciar Chrome
print("Iniciando Chrome...")
options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=./whatsapp_bot_profile")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Abrir WhatsApp Web
    driver.get("https://web.whatsapp.com")
    
    print("\nEsperando login de WhatsApp Web...")
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.ID, "side"))
    )
    print("✓ Login detectado\n")
    
    # Construir URL de WhatsApp
    url = f"https://web.whatsapp.com/send?phone=51{telefono}&text={mensaje}"
    driver.get(url)
    
    print("Esperando que cargue el chat...")
    time.sleep(5)
    
    # Buscar el botón de enviar
    try:
        # Intentar clickear el botón de enviar
        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Enviar']"))
        )
        send_button.click()
        print("\n✅ MENSAJE ENVIADO")
    except:
        # Fallback: presionar Enter en el campo de texto
        print("Usando método alternativo...")
        footer = driver.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
        footer.send_keys(Keys.ENTER)
        print("\n✅ MENSAJE ENVIADO")
    
    time.sleep(3)
    
    print("\n" + "=" * 70)
    print("VERIFICACIÓN:")
    print("=" * 70)
    print(f"\n1. Revisa el WhatsApp Business en el número +51{telefono}")
    print(f"2. Deberías ver el mensaje de prueba enviado")
    print(f"3. Confirma que el mensaje llegó correctamente")
    
    input("\nPresiona ENTER para cerrar el navegador...")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
finally:
    driver.quit()
