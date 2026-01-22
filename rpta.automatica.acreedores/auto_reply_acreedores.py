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
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    """Return a list of unread message IDs and their metadata."""
    results = service.users().messages().list(userId='me', q='is:unread').execute()
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
    message['subject'] = 'Respuesta a su solicitud de información'
    message.attach(MIMEText(html_body, 'html'))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_reply(service, to_address, html_body):
    msg = create_reply_message(to_address, html_body)
    sent = service.users().messages().send(userId='me', body=msg).execute()
    return sent.get('id')

def mark_as_read(service, msg_id):
    service.users().messages().modify(userId='me', id=msg_id,
                                    body={'removeLabelIds': ['UNREAD']}).execute()

# ---------------------------------------------------------------------------
# Main execution loop
# ---------------------------------------------------------------------------

def main(poll_interval=30, max_cycles=0):
    logger.info('--- Auto-reply script started ---')
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    html_body = load_html_message()
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
            if not domain_allowed(sender):
                logger.info('Domain not allowed, skipping')
                continue
            # Extract email address (may contain name <email>)
            email_addr = sender.split('<')[-1].replace('>', '').strip()
            try:
                reply_id = send_reply(service, email_addr, html_body)
                logger.info(f'Sent reply to {email_addr}, reply ID {reply_id}')
                mark_as_read(service, msg_id)
                logger.info(f'Marked original message {msg_id} as read')
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
