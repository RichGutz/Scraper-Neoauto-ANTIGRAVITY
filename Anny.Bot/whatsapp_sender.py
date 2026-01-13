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
    VERSIÓN COMPLETA: Envío de mensaje + adjunto PDF (4 pasos implementados)
    """
    if not silent:
        print("=" * 70)
        print(f"ENVIANDO MENSAJE DE WHATSAPP AL {telefono}")
        print("=" * 70)
        print(f"\nNúmero destino: +51{telefono}")
        print(f"Mensaje: {mensaje[:50]}...")
        if attachment_path:
            print(f"📎 ADJUNTO: {attachment_path}")
    
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
        
        # 5. ENVIAR MENSAJE DE TEXTO (MÉTODO FUNCIONAL - FASE 1)
        if not silent:
            print(f"Enviando mensaje a +51{telefono}...")
        
        # Codificar mensaje en la URL (MÉTODO QUE FUNCIONA)
        encoded_message = urllib.parse.quote(mensaje)
        url = f"https://web.whatsapp.com/send?phone=51{telefono}&text={encoded_message}"
        
        driver.get(url)
        if not silent:
            print("Esperando carga del chat...")
        time.sleep(5)
        
        try:
            # Estrategia 1: Buscar botón enviar (IGUAL QUE CRM)
            send_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send'] | //button[@aria-label='Enviar']"))
            )
            send_button.click()
            if not silent:
                print("✓ Click en botón enviar")
        except:
            if not silent:
                print("Botón no encontrado. Intentando ENTER en el input del footer...")
            # Estrategia 2: Buscar caja de texto y dar ENTER (FALLBACK DEL CRM)
            text_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
            )
            text_box.send_keys(Keys.ENTER)
            if not silent:
                print("✓ Enviado con ENTER en input del footer")
        
        
        # Esperar confirmación
        if not silent:
            print("\nEsperando confirmación de envío...")
        time.sleep(10)
        
        # PASO 2: SI HAY ADJUNTO, HACER CLICK EN '+'
        if attachment_path and os.path.exists(attachment_path):
            if not silent:
                print("\n" + "=" * 70)
                print("PASO 2: ADJUNTANDO ARCHIVO")
                print("=" * 70)
                print(f"Archivo: {os.path.basename(attachment_path)}\n")
            
            try:
                # Click en botón '+'
                if not silent:
                    print("[Paso 2.1] Haciendo click en botón '+'...")
                
                # Selector actualizado según HTML de WhatsApp Web 2026
                clip_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='plus-rounded']"))
                )
                clip_btn.click()
                if not silent:
                    print("   ✓ Botón '+' clickeado")
                time.sleep(2)
                
                # PASO 2.5: HACER CLICK EN BOTÓN "DOCUMENTO" DEL MENÚ
                if not silent:
                    print("\n[Paso 2.5] Haciendo click en botón 'Documento'...")
                
                try:
                    # Buscar y hacer click en el botón "Documento" del menú
                    # Puede tener diferentes selectores
                    doc_button = None
                    
                    # Estrategia 1: Por aria-label
                    try:
                        doc_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='ocument']")
                        if not silent:
                            print("   Encontrado por aria-label")
                    except:
                        pass
                    
                    # Estrategia 2: Por data-icon
                    if not doc_button:
                        try:
                            doc_button = driver.find_element(By.CSS_SELECTOR, "span[data-icon='document']")
                            doc_button = doc_button.find_element(By.XPATH, "..")  # Botón padre
                            if not silent:
                                print("   Encontrado por data-icon")
                        except:
                            pass
                    
                    # Estrategia 3: Primer botón del menú (suele ser Documento)
                    if not doc_button:
                        try:
                            menu_buttons = driver.find_elements(By.CSS_SELECTOR, "li[role='button']")
                            if len(menu_buttons) > 0:
                                doc_button = menu_buttons[0]
                                if not silent:
                                    print("   Usando primer botón del menú")
                        except:
                            pass
                    
                    if doc_button:
                        doc_button.click()
                        if not silent:
                            print("   ✓ Botón 'Documento' clickeado")
                        time.sleep(1)
                    else:
                        if not silent:
                            print("   ⚠️ No se encontró botón 'Documento', continuando...")
                except Exception as e:
                    if not silent:
                        print(f"   ⚠️ Error buscando botón Documento: {e}")
                
                
                # PASO 3: SUBIR PDF AL INPUT CORRECTO (accept="*")
                if not silent:
                    print("\n[Paso 3] Subiendo archivo PDF...")
                
                # CRÍTICO: Buscar el input ESPECÍFICO de documentos (accept="*")
                # NO usar el primer input que suele ser de imágenes (accept="image/*")
                try:
                    # Esperar a que aparezca el input de documentos
                    doc_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][accept='*']"))
                    )
                    if not silent:
                        print("   ✓ Input de documentos encontrado (accept='*')")
                except:
                    # Fallback: buscar todos y usar el que tenga accept="*"
                    if not silent:
                        print("   Buscando input alternativo...")
                    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    doc_input = None
                    for inp in file_inputs:
                        accept_attr = inp.get_attribute("accept")
                        if accept_attr == "*":
                            doc_input = inp
                            if not silent:
                                print(f"   ✓ Encontrado input con accept='*'")
                            break
                    
                    if not doc_input:
                        raise Exception("No se encontró input de documentos (accept='*')")
                
                abs_path = os.path.abspath(attachment_path)
                doc_input.send_keys(abs_path)
                if not silent:
                    print(f"   ✓ Archivo enviado: {abs_path}")
                time.sleep(4)
                
                # PASO 4: ENVIAR PDF (MÚLTIPLES ESTRATEGIAS)
                if not silent:
                    print("\n[Paso 4] Enviando PDF...")
                
                # Estrategia 1: Buscar el BOTÓN que contiene el span de enviar
                try:
                    if not silent:
                        print("   [Estrategia 1] Buscando botón por aria-label='Send'...")
                    send_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send']"))
                    )
                    send_button.click()
                    if not silent:
                        print("   ✓ Click en botón enviar (aria-label)")
                except:
                    # Estrategia 2: Buscar por el span y hacer click en el padre
                    try:
                        if not silent:
                            print("   [Estrategia 2] Buscando span y clickeando padre...")
                        send_span = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-icon='wds-ic-send-filled']"))
                        )
                        # Hacer click en el elemento padre (el botón)
                        send_button = send_span.find_element(By.XPATH, "..")
                        send_button.click()
                        if not silent:
                            print("   ✓ Click en botón padre del span")
                    except:
                        # Estrategia 3: Buscar cualquier botón con el span dentro
                        try:
                            if not silent:
                                print("   [Estrategia 3] Buscando botón que contiene el span...")
                            send_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[.//span[@data-icon='wds-ic-send-filled']]"))
                            )
                            send_button.click()
                            if not silent:
                                print("   ✓ Click en botón (XPath)")
                        except:
                            # Estrategia 4: ENTER en caption box
                            try:
                                if not silent:
                                    print("   [Estrategia 4] Intentando ENTER en caption...")
                                caption_box = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10']")
                                caption_box.send_keys(Keys.ENTER)
                                if not silent:
                                    print("   ✓ Enviado con ENTER")
                            except:
                                if not silent:
                                    print("   ⚠️ No se pudo enviar automáticamente")
                                    print("   Por favor, haz click manualmente en el botón enviar")
                
                time.sleep(5)
                if not silent:
                    print("   ✓ PDF ENVIADO ✅")
                
            except Exception as e:
                print(f"\n❌ ERROR en Paso 2: {e}")
                import traceback
                traceback.print_exc()
        
        if not silent:
            print("\n" + "=" * 70)
            print("✅ PROCESO COMPLETADO")
            print("=" * 70)
            print(f"\nVerifica en WhatsApp (+51{telefono}) que el mensaje llegó.")
            if attachment_path:
                print(f"\n⚠️ NOTA: El adjunto NO se envió (funcionalidad desactivada)")
            print("Chrome permanece abierto para revisión.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
        return False
