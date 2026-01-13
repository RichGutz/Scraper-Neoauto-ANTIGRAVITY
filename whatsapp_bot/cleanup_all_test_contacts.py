"""
Eliminar TODOS los contactos con organización "Neoauto Lead"
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import time

# Configuración
SCOPES = ['https://www.googleapis.com/auth/contacts']
BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_DIR = BASE_DIR / "rpta.automatica.acreedores"
TOKEN_PATH = CREDENTIALS_DIR / 'token.json'
CREDENTIALS_PATH = CREDENTIALS_DIR / 'credentials.json'

def autenticar_google():
    """Autenticación con Google"""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(f"ERROR: 'credentials.json' no encontrado en {CREDENTIALS_PATH}")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def main():
    print("=" * 70)
    print("ELIMINANDO TODOS LOS CONTACTOS DEL BOT")
    print("=" * 70)
    print()
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('people', 'v1', credentials=creds)
    
    # Obtener todos los contactos
    print("Obteniendo contactos...")
    all_contacts = service.people().connections().list(
        resourceName='people/me',
        pageSize=1000,
        personFields='names,phoneNumbers,organizations,metadata'
    ).execute().get('connections', [])
    
    print(f"Total: {len(all_contacts)} contactos\n")
    
    # Filtrar contactos con organización "Neoauto Lead"
    bot_contacts = []
    for contact in all_contacts:
        orgs = contact.get('organizations', [])
        if orgs:
            for org in orgs:
                if org.get('name') == 'Neoauto Lead':
                    bot_contacts.append(contact)
                    break
    
    print(f"Contactos del bot encontrados: {len(bot_contacts)}\n")
    
    if len(bot_contacts) == 0:
        print("✅ No hay contactos del bot para eliminar")
        return
    
    print("Eliminando contactos...")
    print("=" * 70)
    
    deleted = 0
    errors = 0
    
    for contact in bot_contacts:
        names = contact.get('names', [])
        display_name = names[0].get('displayName', 'Sin nombre') if names else 'Sin nombre'
        resource_name = contact.get('resourceName')
        
        print(f"{deleted + 1}. {display_name[:60]}")
        
        try:
            service.people().deleteContact(resourceName=resource_name).execute()
            deleted += 1
            time.sleep(0.15)  # Pausa para no saturar la API
        except Exception as e:
            print(f"   Error: {e}")
            errors += 1
    
    print("\n" + "=" * 70)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 70)
    print(f"\nContactos eliminados: {deleted}")
    print(f"Errores: {errors}")
    print("\nGoogle Contacts está limpio y listo para nuevos contactos.")

if __name__ == "__main__":
    main()
