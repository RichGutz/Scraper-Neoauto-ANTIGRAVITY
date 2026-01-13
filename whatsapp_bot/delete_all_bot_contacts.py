"""
Eliminar contactos - VERSIÓN CORREGIDA
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import time

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

print("=" * 70)
print("ELIMINANDO CONTACTOS DEL BOT")
print("=" * 70)
print()

# Obtener contactos
print("Obteniendo contactos...")
all_contacts = service.people().connections().list(
    resourceName='people/me',
    pageSize=1000,
    personFields='names,phoneNumbers,organizations'
).execute().get('connections', [])

print(f"Total: {len(all_contacts)}\n")

# Filtrar y eliminar
deleted = 0
for contact in all_contacts:
    orgs = contact.get('organizations', [])
    
    # Verificar si tiene organización "Neoauto Lead"
    has_neoauto = False
    if orgs:
        for org in orgs:
            if org.get('name') == 'Neoauto Lead':
                has_neoauto = True
                break
    
    if has_neoauto:
        names = contact.get('names', [])
        display_name = names[0].get('displayName', 'Sin nombre') if names else 'Sin nombre'
        resource_name = contact.get('resourceName')
        
        print(f"{deleted + 1}. Eliminando: {display_name[:60]}")
        
        try:
            service.people().deleteContact(resourceName=resource_name).execute()
            deleted += 1
            time.sleep(0.15)
        except Exception as e:
            print(f"   Error: {e}")

print(f"\n✅ Eliminados: {deleted} contactos")
print("Google Contacts limpio.")
