"""
Test directo: Crear contacto con número específico
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
    print("=== TEST: Crear contacto con número específico ===\n")
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('people', 'v1', credentials=creds)
    
    # Datos del contacto
    nombre = "Jorge Huaman TEST"
    info_auto = "Hyundai Creta 2024"
    telefono = "999221760"
    
    print(f"Creando contacto:")
    print(f"  Nombre: {nombre}")
    print(f"  Auto: {info_auto}")
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
        
        print("✅ CONTACTO CREADO EXITOSAMENTE!")
        print(f"Resource Name: {result.get('resourceName', 'N/A')}\n")
        
        print("=" * 70)
        print("PRÓXIMOS PASOS:")
        print("1. Cierra COMPLETAMENTE WhatsApp Dual (Forzar detención)")
        print("2. Espera 10 segundos")
        print("3. Abre WhatsApp Dual")
        print("4. Busca el número: +51999221760")
        print("5. Debería aparecer como: 'Jorge Huaman TEST Hyundai Creta 2024'")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
