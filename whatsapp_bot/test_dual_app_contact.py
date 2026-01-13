"""
Script de prueba: Crear contacto con estructura mejorada
Verifica que la nueva estructura funcione con WhatsApp Dual
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

def test_nueva_estructura():
    """Prueba crear un contacto con la estructura mejorada"""
    print("=== TEST: Estructura Mejorada de Contacto ===\n")
    
    creds = autenticar_google()
    if not creds:
        return
    
    service_people = build('people', 'v1', credentials=creds)
    
    # Datos de prueba
    nombre_completo = "Test Dual App"
    info_auto = "Honda Civic 2021"
    telefono = "988888888"
    
    print(f"Creando contacto: {nombre_completo} - {info_auto}")
    print(f"Teléfono: +51{telefono}\n")
    
    try:
        # Estructura mejorada
        contact_body = {
            "names": [{
                "givenName": nombre_completo,
                "familyName": info_auto,
                "displayName": f"{nombre_completo} - {info_auto}"
            }],
            "phoneNumbers": [{
                "value": f"+51{telefono}",
                "type": "mobile"
            }],
            "organizations": [{
                "name": "Neoauto Lead",
                "title": info_auto
            }],
            "memberships": [{
                "contactGroupMembership": {
                    "contactGroupResourceName": "contactGroups/myContacts"
                }
            }]
        }
        
        result = service_people.people().createContact(body=contact_body).execute()
        
        print("✅ Contacto creado exitosamente!")
        print(f"Resource Name: {result.get('resourceName', 'N/A')}\n")
        
        print("=" * 70)
        print("PRÓXIMOS PASOS:")
        print("1. Espera 30 segundos")
        print("2. En tu WhatsApp Dual, ve a 'Nuevo chat'")
        print("3. Busca el número: +51988888888")
        print("4. Debería aparecer como: 'Test Dual App - Honda Civic 2021'")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_nueva_estructura()
