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

def send_whatsapp_message(telefono, mensaje, attachment_path=None, silent=False):
    """
    Envía un mensaje de WhatsApp usando Selenium y WhatsApp Web
    """
    if not silent:
        print("=" * 70)
        print(f"ENVIANDO MENSAJE DE WHATSAPP AL {telefono}")
        print("=" * 70)
        print(f"\nNúmero destino: +51{telefono}")
        print(f"Mensaje: {mensaje[:50]}...")
        if attachment_path:
            print(f"Adjunto: {attachment_path}")
    
    # 1. Cerrar Chrome si está abierto
    if not silent:
        print("\nCerrando Chrome si está abierto...")
    subprocess.run("taskkill /F /IM chrome.exe /T", shell=True, capture_output=True)
    time.sleep(2)
    
    # 2. Configurar Chrome con el perfil del bot
    if not silent:
        print("Iniciando Chrome Driver...")
    
    chrome_options = Options()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
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
        
        # 5. Abrir chat
        # 5. Abrir chat
        if not silent:
            print(f"Abriendo chat con +51{telefono}...")
        
        base_url = f"https://web.whatsapp.com/send?phone=51{telefono}"
        if not attachment_path:
            # Si es solo texto, enviarlo por URL es más robusto y rápido
            encoded_msg = urllib.parse.quote(mensaje)
            url = f"{base_url}&text={encoded_msg}"
        else:
            url = base_url
            
        driver.get(url)
        # Esperar un poco más para que procese el texto en URL
        time.sleep(8)
        
        # 6. SI HAY ADJUNTO, PROCESARLO
        if attachment_path and os.path.exists(attachment_path):
            if not silent:
                print(f"\n📎 ADJUNTANDO: {os.path.basename(attachment_path)}")
                print(f"   Ruta completa: {os.path.abspath(attachment_path)}")
            
            try:
                # ESTRATEGIA DIRECTA: Inyectar archivo directamente en el input
                # Esto evita tener que hacer click en botones
                if not silent:
                    print("\n   [Método 1] Buscando input file directamente...")
                
                # Primero hacer click en el botón + para activar el menú
                clip_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='plus']"))
                )
                clip_btn.click()
                if not silent:
                    print("   ✓ Botón '+' clickeado")
                time.sleep(2)
                
                # Ahora buscar TODOS los inputs de tipo file
                file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if not silent:
                    print(f"   Encontrados {len(file_inputs)} inputs de tipo file")
                
                # Buscar el input que acepta documentos (no solo imágenes)
                doc_input = None
                for idx, inp in enumerate(file_inputs):
                    accept_attr = inp.get_attribute("accept")
                    if not silent:
                        print(f"   Input {idx}: accept='{accept_attr}'")
                    
                    # El input de documentos suele tener accept="*" o no tener restricciones de imagen
                    if accept_attr is None or "*" in accept_attr or "application" in accept_attr:
                        doc_input = inp
                        if not silent:
                            print(f"   ✓ Usando input {idx} para documentos")
                        break
                
                if doc_input is None:
                    # Si no encontramos uno específico, usar el último (suele ser el de documentos)
                    doc_input = file_inputs[-1] if file_inputs else None
                    if not silent:
                        print("   ⚠️ Usando último input como fallback")
                
                if doc_input:
                    abs_path = os.path.abspath(attachment_path)
                    doc_input.send_keys(abs_path)
                    if not silent:
                        print(f"   ✓ Archivo enviado al input: {abs_path}")
                    time.sleep(4)
                    
                    # Agregar caption
                    try:
                        caption_box = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10']"))
                        )
                        caption_box.send_keys(mensaje)
                        if not silent:
                            print("   ✓ Caption agregado")
                        time.sleep(1)
                    except:
                        if not silent:
                            print("   ⚠️ No se pudo agregar caption")
                    
                    # Enviar
                    send_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='send']"))
                    )
                    send_btn.click()
                    if not silent:
                        print("   ✓ ARCHIVO ENVIADO")
                    time.sleep(5)
                else:
                    raise Exception("No se encontró input de archivo válido")
                    
            except Exception as e:
                print(f"\n❌ ERROR al adjuntar: {e}")
                print("   Enviando solo mensaje de texto...")
                attachment_path = None
        
        # 7. Si NO hubo adjunto, enviar solo texto
        if not attachment_path:
            try:
                # Estrategia 1: Buscar botón enviar (XPath robusto para varios idiomas/versiones)
                send_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send'] | //button[@aria-label='Send'] | //button[@aria-label='Enviar']"))
                )
                send_button.click()
                if not silent:
                    print("✓ Botón enviar clickeado")
            except Exception as e:
                # Estrategia 2: Fallback ENTER en caja de texto (Asegurando que sea el FOOTER)
                if not silent:
                    print(f"⚠️ Click falló ({e}), intentando ENTER en footer...")
                try:
                    text_box = driver.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
                    text_box.click() # Asegurar foco
                    time.sleep(0.5)
                    text_box.send_keys(Keys.ENTER)
                    if not silent:
                        print("✓ Enviado con ENTER")
                except Exception as e2:
                    print(f"❌ Falló envío fallback: {e2}")

        
        # Esperar confirmación
        if not silent:
            print("\nEsperando confirmación de envío...")
        time.sleep(10)
        
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
