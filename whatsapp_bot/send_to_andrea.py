"""
Enviar mensaje de WhatsApp a Andrea Cabrera (lead real)
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

# Datos del lead
nombre = "Andrea"
telefono = "987704652"
link_auto = "https://neoauto.com/auto/usado/toyota-rav4-2017-1860166"

# Mensaje
mensaje = f"Hola {nombre}! Mi nombre es Richard Gutierrez. Vi tu auto en Neoauto: {link_auto}. Por favor, quisiera saber donde y en que horarios se puede ver el vehiculo?. Gracias. RG"

print("=" * 70)
print("ENVIANDO MENSAJE A LEAD REAL")
print("=" * 70)
print(f"\nNombre: {nombre}")
print(f"Teléfono: +51{telefono}")
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
    print("VERIFICA EN WHATSAPP BUSINESS:")
    print("=" * 70)
    print(f"\n1. Busca el chat con +51{telefono}")
    print(f"2. Debería aparecer como: 'Andrea Cabrera - Toyota Rav4 2017'")
    print(f"3. El mensaje debería estar enviado")
    
    input("\nPresiona ENTER para cerrar el navegador...")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
finally:
    driver.quit()
