import os
import time
import base64
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Scopes required for sending emails and modifying them
SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

# Directory containing this script
BASE_DIR = Path(__file__).parent

# Credentials files (will be copied from gmail_sender folder)
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'
TOKEN_FILE = BASE_DIR / 'token.json'

# Recipients list (domains to reply to)
ALLOWED_DOMAINS = ['finanty.com', 'inverpeco.com.pe']

# Paths to message templates
HTML_TEMPLATE = BASE_DIR / 'mensaje_respuesta.html'

# Logging setup
LOG_FILE = BASE_DIR / 'auto_reply_acreedores.log'
import sys

# Configure logging to file and console
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def authenticate():
    """Authenticate with Gmail using OAuth2 credentials."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds

def load_html_message():
    """Load the HTML template for the reply."""
    if not HTML_TEMPLATE.exists():
        logger.error(f"HTML template not found: {HTML_TEMPLATE}")
        return None
    with open(HTML_TEMPLATE, 'r', encoding='utf-8') as f:
        return f.read()

def get_unread_messages(service):
    """Return a list of unread message IDs from allowed creditor domains."""
    query = 'is:unread (from:finanty.com OR from:inverpeco.com.pe)'
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return messages

def get_message_sender(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From']).execute()
    headers = msg.get('payload', {}).get('headers', [])
    for h in headers:
        if h['name'].lower() == 'from':
            return h['value']
    return None

def domain_allowed(sender):
    """Check if sender's email domain is in the allowed list."""
    if '@' not in sender:
        return False
    domain = sender.split('@')[-1].lower()
    return any(domain.endswith(allowed) for allowed in ALLOWED_DOMAINS)

def create_reply_message(to_address, html_body):
    message = MIMEMultipart('alternative')
    message['to'] = to_address
    message['subject'] = 'Oferta de pago deuda Richard Gutierrez DNI 09870156'
    message.attach(MIMEText(html_body, 'html'))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_reply(service, to_address, html_body):
    msg = create_reply_message(to_address, html_body)
    # Send the message; Gmail automatically places it in Sent folder
    sent = service.users().messages().send(userId='me', body=msg).execute()
    return sent.get('id')

def load_recipients():
    """Load the list of recipient email addresses from destinatarios.txt."""
    recipients_path = BASE_DIR / 'destinatarios.txt'
    if not recipients_path.exists():
        logger.error(f"Recipients file not found: {recipients_path}")
        return []
    with open(recipients_path, 'r', encoding='utf-8') as f:
        # Strip whitespace and ignore empty lines
        return [line.strip() for line in f if line.strip()]


# ---------------------------------------------------------------------------
# Main execution loop
# ---------------------------------------------------------------------------

def main(poll_interval=30, max_cycles=0):
    logger.info('--- Auto-reply script started ---')
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    html_body = load_html_message()
    # Preload recipients list once
    all_recipients = load_recipients()
    logger.info(f'Loaded {len(all_recipients)} recipients from destinatarios.txt')
    if not html_body:
        logger.error('No HTML body loaded, aborting.')
        return

    cycle = 0
    while True:
        cycle += 1
        logger.info(f'Cycle {cycle} - checking unread messages')
        messages = get_unread_messages(service)
        for msg in messages:
            msg_id = msg['id']
            sender = get_message_sender(service, msg_id)
            if not sender:
                continue
            logger.info(f'Found message from {sender}')
            # Domain already filtered by Gmail query, proceed directly
            # email address extraction and reply handling

            # Extract email address (may contain name <email>)
            email_addr = sender.split('<')[-1].replace('>', '').strip()
            try:
                # Extract domain from email address
                domain = email_addr.split('@')[1]
                # Load all recipients once (if not already loaded)
                if 'all_recipients' not in globals():
                    all_recipients = load_recipients()
                # Find recipients that share the same domain
                target_recipients = set([r for r in all_recipients if r.split('@')[-1].lower() == domain.lower()])
                # Ensure the original sender is included even if not in the file
                target_recipients.add(email_addr)
                logger.info(f"Enviando respuestas al dominio {domain} a {len(target_recipients)} destinatario(s)")
                for recipient in target_recipients:
                    # Personalize the HTML template with the sender's domain
                    display_name = domain.split('.')[0].capitalize()
                    placeholder = 'Estimados "Nombre del Dominio del Acreedor:'
                    personalized_body = html_body.replace(placeholder, f'Estimados {display_name}')
                    for i in range(10):
                        reply_id = send_reply(service, recipient, personalized_body)
                        logger.info(f'Sent reply #{i+1} to {recipient}, reply ID {reply_id}')
                        if i < 9:
                            time.sleep(30)
                # After all sends, mark the original message as read to avoid re‑processing
                mark_as_read(service, msg_id)
                logger.info(f'Marked original message {msg_id} as read after sending replies')
            except Exception as e:
                logger.error(f'Error sending reply to {email_addr}: {e}')
        if max_cycles and cycle >= max_cycles:
            logger.info('Reached max cycles, exiting')
            break
        logger.info(f'Waiting {poll_interval} seconds before next check')
        time.sleep(poll_interval)

if __name__ == '__main__':
    # Default: poll every 30 seconds, run indefinitely
    main()
