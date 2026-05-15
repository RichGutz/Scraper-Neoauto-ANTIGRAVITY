import os
import base64
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'
TOKEN_FILE = BASE_DIR / 'token.json'
HTML_TEMPLATE = BASE_DIR / 'mensaje_respuesta.html'
ATTACHMENT_FINANTY = BASE_DIR / 'Propuesta.Finanty.7658.pdf'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.error("No valid token found. Please run the main script first to authenticate.")
            return None
    return creds

def create_reply_message(to_address, html_body, attachment_path=None):
    message = MIMEMultipart('mixed')
    message['to'] = to_address
    message['subject'] = 'TEST: Oferta de pago deuda Richard Gutierrez DNI 09870156'
    
    msg_html = MIMEMultipart('alternative')
    msg_html.attach(MIMEText(html_body, 'html'))
    message.attach(msg_html)
    
    if attachment_path and attachment_path.exists():
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_path.name}"')
            message.attach(part)
            
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def main():
    target_email = "rgutil@gmail.com"
    logger.info(f"Preparing test email for {target_email} (Finanty Mode)")
    
    creds = authenticate()
    if not creds: return
    service = build('gmail', 'v1', credentials=creds)
    
    with open(HTML_TEMPLATE, 'r', encoding='utf-8') as f:
        html_body = f.read()
        
    # Apply personalization
    display_name = "Finanty"
    placeholder = 'Estimados "Nombre del Dominio del Acreedor:'
    personalized_body = html_body.replace(placeholder, f'Estimados {display_name}')
    
    comodin_text = '<br><br><span class="highlight">Como puede verse en el email adjunto en PDF, el 24 de Abril de 2026, Finanty me ofreció cancelar mi deuda con S/. 7,658. Agradezco la oferta pero aun esta muy lejos de lo que mis ingresos me permitirian pagar.</span>'
    personalized_body = personalized_body.replace('{{COMODIN_FINANTY}}', comodin_text)
    
    msg = create_reply_message(target_email, personalized_body, ATTACHMENT_FINANTY)
    sent = service.users().messages().send(userId='me', body=msg).execute()
    logger.info(f"Test email sent! ID: {sent.get('id')}")

if __name__ == '__main__':
    main()
