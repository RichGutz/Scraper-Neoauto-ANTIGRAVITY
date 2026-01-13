import os
import base64
from email.mime.text import MIMEText
import logging
import argparse

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
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
LOG_FILE = 'test_email.log'

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def autenticar_google():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                logger.error("CRITICAL ERROR: 'credentials.json' not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def crear_mensaje_prueba(destinatario_email):
    mensaje = MIMEText("Este es un correo de prueba para verificar la configuración de envío de Gemini.")
    mensaje['to'] = destinatario_email
    mensaje['from'] = 'me'
    mensaje['subject'] = 'Prueba de Envío de Correo - Gemini'
    return {'raw': base64.urlsafe_b64encode(mensaje.as_bytes()).decode()}

def main():
    parser = argparse.ArgumentParser(description="Script de prueba para enviar correos.")
    parser.add_argument('--recipient', type=str, required=True, help='Correo del destinatario.')
    args = parser.parse_args()

    logger.info("--- INICIANDO SCRIPT DE PRUEBA DE EMAIL ---")

    logger.info("[Paso 1/3] Autenticando con Google...")
    creds = autenticar_google()
    if not creds:
        logger.critical("FALLO EL PROCESO: AUTENTICACIÓN")
        return

    logger.info("[Paso 2/3] Construyendo el servicio de Gmail...")
    try:
        service_gmail = build('gmail', 'v1', credentials=creds)
    except Exception as e:
        logger.critical(f"Error construyendo el servicio de Gmail: {e}")
        return

    logger.info(f"[Paso 3/3] Enviando correo a: {args.recipient}")
    mensaje_final = crear_mensaje_prueba(args.recipient)
    try:
        sent_message = service_gmail.users().messages().send(userId='me', body=mensaje_final).execute()
        logger.info(f"  ÉXITO. Correo enviado. ID del Mensaje: {sent_message['id']}")
        print(f"Correo de prueba enviado exitosamente a {args.recipient}.")
    except Exception as error:
        logger.error(f"  ERROR al enviar correo a {args.recipient}: {error}")
        print(f"Ocurrió un error al enviar el correo: {error}")

    logger.info("--- SCRIPT DE PRUEBA DE EMAIL FINALIZADO ---")

if __name__ == '__main__':
    main()
