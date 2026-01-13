"""
Script para listar todos los contactos de Google
Útil para verificar qué contactos se han creado desde el bot
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

def listar_contactos():
    """Lista todos los contactos de Google"""
    print("=== LISTADO DE CONTACTOS DE GOOGLE ===\n")
    
    creds = autenticar_google()
    if not creds:
        return
    
    try:
        service = build('people', 'v1', credentials=creds)
        
        # Obtener contactos
        print("Obteniendo contactos...")
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=100,
            personFields='names,phoneNumbers,metadata'
        ).execute()
        
        connections = results.get('connections', [])
        
        if not connections:
            print("❌ No se encontraron contactos en Google Contacts")
            return
        
        print(f"✓ Total de contactos encontrados: {len(connections)}\n")
        print("=" * 80)
        
        # Filtrar contactos que parecen ser del bot (contienen " - " en el nombre)
        bot_contacts = []
        other_contacts = []
        
        for person in connections:
            names = person.get('names', [])
            phones = person.get('phoneNumbers', [])
            
            if names:
                display_name = names[0].get('displayName', 'Sin nombre')
                
                # Verificar si es un contacto del bot (formato: "Nombre - Auto")
                if ' - ' in display_name:
                    bot_contacts.append({
                        'name': display_name,
                        'phone': phones[0].get('value', 'Sin teléfono') if phones else 'Sin teléfono'
                    })
                else:
                    other_contacts.append({
                        'name': display_name,
                        'phone': phones[0].get('value', 'Sin teléfono') if phones else 'Sin teléfono'
                    })
        
        # Mostrar contactos del bot
        if bot_contacts:
            print(f"\n🤖 CONTACTOS CREADOS POR EL BOT ({len(bot_contacts)}):")
            print("=" * 80)
            for i, contact in enumerate(bot_contacts, 1):
                print(f"{i}. {contact['name']}")
                print(f"   📱 {contact['phone']}")
                print()
        else:
            print("\n⚠️  NO SE ENCONTRARON CONTACTOS CREADOS POR EL BOT")
            print("   (Buscando formato: 'Nombre - Marca Modelo Año')")
        
        # Mostrar resumen
        print("\n" + "=" * 80)
        print(f"RESUMEN:")
        print(f"  • Contactos del bot: {len(bot_contacts)}")
        print(f"  • Otros contactos: {len(other_contacts)}")
        print(f"  • Total: {len(connections)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    listar_contactos()
