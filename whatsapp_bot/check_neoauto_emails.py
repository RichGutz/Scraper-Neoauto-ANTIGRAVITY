"""
Verificar qué correos de Neoauto hay en Gmail
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_DIR = BASE_DIR / "rpta.automatica.acreedores"
TOKEN_PATH = CREDENTIALS_DIR / 'token.json'
CREDENTIALS_PATH = CREDENTIALS_DIR / 'credentials.json'

def autenticar_google():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

creds = autenticar_google()
service = build('gmail', 'v1', credentials=creds)

print("=== VERIFICANDO CORREOS DE NEOAUTO ===\n")

# Buscar correos no leídos
print("1. Correos NO LEÍDOS de Neoauto:")
results = service.users().messages().list(
    userId='me',
    q='from:contacto@neoauto.pe is:unread',
    maxResults=5
).execute()
unread = results.get('messages', [])
print(f"   Total: {len(unread)}\n")

# Buscar TODOS los correos (últimos 5)
print("2. Últimos 5 correos de Neoauto (leídos o no):")
results = service.users().messages().list(
    userId='me',
    q='from:contacto@neoauto.pe',
    maxResults=5
).execute()
all_msgs = results.get('messages', [])
print(f"   Total: {len(all_msgs)}\n")

if all_msgs:
    for i, msg in enumerate(all_msgs, 1):
        message = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
        headers = message.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Sin fecha')
        
        print(f"{i}. {subject[:60]}")
        print(f"   Fecha: {date}")
        print(f"   ID: {msg['id']}")
        print()
