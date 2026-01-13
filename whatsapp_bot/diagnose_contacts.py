"""
Script de Diagnóstico Detallado de Contactos
Muestra TODOS los contactos con sus teléfonos para verificar qué se creó
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuración
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
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
    print("=== DIAGNÓSTICO DETALLADO DE CONTACTOS ===\n")
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('people', 'v1', credentials=creds)
    
    # Obtener contactos recientes (últimos 50)
    print("Obteniendo contactos recientes...\n")
    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=50,
        personFields='names,phoneNumbers,organizations',
        sortOrder='LAST_MODIFIED_DESCENDING'  # Más recientes primero
    ).execute()
    
    connections = results.get('connections', [])
    
    print(f"Total de contactos (últimos 50): {len(connections)}\n")
    print("=" * 80)
    
    # Buscar contactos con teléfonos peruanos (+51)
    peru_contacts = []
    
    for person in connections:
        names = person.get('names', [])
        phones = person.get('phoneNumbers', [])
        orgs = person.get('organizations', [])
        
        # Verificar si tiene teléfono peruano
        has_peru_phone = False
        phone_value = ""
        for phone in phones:
            if '+51' in phone.get('value', ''):
                has_peru_phone = True
                phone_value = phone.get('value', '')
                break
        
        if has_peru_phone:
            display_name = names[0].get('displayName', 'Sin nombre') if names else 'Sin nombre'
            given_name = names[0].get('givenName', '') if names else ''
            family_name = names[0].get('familyName', '') if names else ''
            org_name = orgs[0].get('name', '') if orgs else ''
            
            peru_contacts.append({
                'display': display_name,
                'given': given_name,
                'family': family_name,
                'phone': phone_value,
                'org': org_name
            })
    
    print(f"\n📱 CONTACTOS CON TELÉFONOS PERUANOS (+51): {len(peru_contacts)}\n")
    print("=" * 80)
    
    # Mostrar contactos
    for i, contact in enumerate(peru_contacts, 1):
        print(f"\n{i}. {contact['display']}")
        print(f"   Nombre: {contact['given']}")
        print(f"   Apellido: {contact['family']}")
        print(f"   Teléfono: {contact['phone']}")
        if contact['org']:
            print(f"   Organización: {contact['org']}")
        
        # Marcar si parece ser del bot
        if contact['org'] == 'Neoauto Lead':
            print(f"   ✅ CONTACTO DEL BOT")
    
    # Contar contactos del bot
    bot_contacts = [c for c in peru_contacts if c['org'] == 'Neoauto Lead']
    
    print("\n" + "=" * 80)
    print(f"\nRESUMEN:")
    print(f"  • Total contactos peruanos: {len(peru_contacts)}")
    print(f"  • Contactos del bot (Neoauto Lead): {len(bot_contacts)}")
    
    if len(bot_contacts) == 0:
        print("\n⚠️  NO SE ENCONTRARON CONTACTOS DEL BOT")
        print("   Esto significa que los contactos NO se crearon correctamente.")
    else:
        print(f"\n✅ Se encontraron {len(bot_contacts)} contactos del bot")

if __name__ == "__main__":
    main()
