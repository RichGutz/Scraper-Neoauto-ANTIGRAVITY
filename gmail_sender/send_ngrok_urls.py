import os
import datetime
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import argparse
import time
import re
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: Faltan librerías de Google.")
    print("Instala las librerías con: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    exit()

# --- CONFIGURACIÓN ---
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / 'envio_reporte.log'
NGROK_LOG_FILE = '/home/richgutz/inandes-saas-app/ngrok.log'
CREDENTIALS_FILE = SCRIPT_DIR / 'credentials.json'
TOKEN_FILE = SCRIPT_DIR / 'token.json'

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_ngrok_urls():
    urls = []
    try:
        with open(NGROK_LOG_FILE, 'r') as f:
            for line in f:
                if 'url=' in line:
                    match = re.search(r'url=(https://[\w.-]+)', line)
                    if match:
                        urls.append(match.group(1))
    except FileNotFoundError:
        logger.error(f"ERROR: ngrok log file not found: '{NGROK_LOG_FILE}'.")
    except Exception as e:
        logger.error(f"ERROR reading ngrok log file '{NGROK_LOG_FILE}': {e}")
    return list(set(urls)) # Return unique URLs

def autenticar_google():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"CRITICAL ERROR: '{CREDENTIALS_FILE}' not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds

def crear_mensaje_email(destinatario_email, asunto, cuerpo_texto):
    mensaje = MIMEMultipart()
    mensaje['to'] = destinatario_email
    mensaje['from'] = 'me'
    mensaje['subject'] = asunto
    mensaje.attach(MIMEText(cuerpo_texto, 'plain'))
    return {'raw': base64.urlsafe_b64encode(mensaje.as_bytes()).decode()}

def mover_correo_a_papelera(service_gmail, message_id):
    try:
        service_gmail.users().messages().trash(userId='me', id=message_id).execute()
        logger.info(f"Message ID '{message_id}' moved to trash.")
    except Exception as e:
        logger.error(f"Unexpected error while moving email '{message_id}' to trash: {e}")

def main():
    logger.info("--- INICIANDO SCRIPT DE ENVÍO DE URLS DE NGROK ---")

    logger.info("[Paso 1/4] Obteniendo URLs de ngrok...")
    ngrok_urls = get_ngrok_urls()
    if not ngrok_urls:
        logger.warning("No se encontraron URLs de ngrok. No se enviará ningún correo.")
        return

    logger.info("[Paso 2/4] Autenticando con Google...")
    creds = autenticar_google()
    if not creds:
        logger.critical("PROCESO FALLIDO: AUTENTICACIÓN")
        return

    logger.info("[Paso 3/4] Construyendo servicio de Gmail...")
    try:
        service_gmail = build('gmail', 'v1', credentials=creds)
    except Exception as e:
        logger.critical(f"Error al construir el servicio de Gmail: {e}")
        return

    logger.info("[Paso 4/4] Creando y enviando correo...")
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    asunto = f"Direcciones URL para pruebas {today_str}"
    cuerpo_texto = "Hola,\n\nAquí están las URLs de ngrok para las aplicaciones:\n\n" + "\n".join(ngrok_urls)
    destinatario_email = "rgutil@gmail.com"

    mensaje_final = crear_mensaje_email(destinatario_email, asunto, cuerpo_texto)

    try:
        sent_message = service_gmail.users().messages().send(userId='me', body=mensaje_final).execute()
        logger.info(f"  ÉXITO. Correo enviado. ID del mensaje: {sent_message['id']}")
        mover_correo_a_papelera(service_gmail, sent_message['id'])
    except Exception as error:
        logger.error(f"  ERROR al enviar correo a {destinatario_email}: {error}")

    logger.info("--- PROCESO DE ENVÍO DE CORREO FINALIZADO ---")

if __name__ == '__main__':
    main()
