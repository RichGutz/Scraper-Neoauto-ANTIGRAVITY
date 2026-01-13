"""
Test final: Verificar sincronización con WhatsApp Business
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

def main():
    print("=== TEST FINAL: WhatsApp Business ===\n")
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('people', 'v1', credentials=creds)
    
    # Contacto de prueba para WhatsApp Business
    nombre = "BUSINESS TEST"
    info_auto = "Verificacion Final"
    telefono = "900000001"  # Número ficticio para prueba
    
    print(f"Creando contacto de prueba:")
    print(f"  Nombre: {nombre} {info_auto}")
    print(f"  Teléfono: +51{telefono}\n")
    
    try:
        contact_body = {
            "names": [{
                "givenName": nombre,
                "familyName": info_auto
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
        
        result = service.people().createContact(body=contact_body).execute()
        
        print("✅ CONTACTO CREADO!")
        print(f"Resource Name: {result.get('resourceName', 'N/A')}\n")
        
        print("=" * 70)
        print("VERIFICACIÓN EN WHATSAPP BUSINESS:")
        print("=" * 70)
        print("\n1. Abre WhatsApp Business")
        print("2. Busca el número: +51900000001")
        print("3. Debería aparecer: 'BUSINESS TEST Verificacion Final'")
        print("\nSi aparece → ✅ Sincronización funcionando")
        print("Si NO aparece → Reinicia WhatsApp Business y vuelve a buscar")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
