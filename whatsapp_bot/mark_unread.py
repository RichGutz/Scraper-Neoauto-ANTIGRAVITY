"""
Marcar correo de Andrea Cabrera como NO LEÍDO
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
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

print("Marcando correo de Andrea Cabrera como NO LEÍDO...\n")

creds = autenticar_google()
service = build('gmail', 'v1', credentials=creds)

# Buscar el correo de Andrea Cabrera
results = service.users().messages().list(
    userId='me',
    q='from:contacto@neoauto.pe subject:Andrea OR subject:Cabrera OR subject:RAV4',
    maxResults=5
).execute()

messages = results.get('messages', [])

if messages:
    msg_id = messages[0]['id']
    
    # Marcar como no leído
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()
    
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={'addLabelIds': ['UNREAD']}
    ).execute()
    
    print(f"✅ Correo marcado como NO LEÍDO (ID: {msg_id})")
    print("\nAhora ejecuta el bot:")
    print("python auto_contact_neoauto.py")
else:
    print("❌ No se encontró el correo de Andrea Cabrera")
