"""
Debug: Ver exactamente qué está devolviendo la API
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuración
SCOPES = ['https://www.googleapis.com/auth/contacts']
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
service = build('people', 'v1', credentials=creds)

# Obtener primeros 10 contactos peruanos
results = service.people().connections().list(
    resourceName='people/me',
    pageSize=50,
    personFields='names,phoneNumbers,organizations',
    sortOrder='LAST_MODIFIED_DESCENDING'
).execute()

contacts = results.get('connections', [])

print(f"Total contactos obtenidos: {len(contacts)}\n")

# Buscar contactos con teléfono peruano y organización
for i, contact in enumerate(contacts[:10], 1):
    names = contact.get('names', [])
    phones = contact.get('phoneNumbers', [])
    orgs = contact.get('organizations', [])
    
    has_peru = any('+51' in p.get('value', '') for p in phones)
    
    if has_peru:
        print(f"{i}. {names[0].get('displayName', 'Sin nombre') if names else 'Sin nombre'}")
        print(f"   Organizaciones: {[org.get('name') for org in orgs]}")
        print()
