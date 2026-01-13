"""
Script de prueba para enviar mensaje al nuevo número de WhatsApp Business: 991090016
Usa Google Contacts API (método probado que SÍ funciona)
"""

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
    print("=" * 70)
    print("PRUEBA DE MENSAJE AL NUEVO NÚMERO DE WHATSAPP BUSINESS")
    print("=" * 70)
    print()
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('people', 'v1', credentials=creds)
    
    # Datos del contacto de prueba
    nombre = "PRUEBA WHATSAPP"
    info = "Nuevo Numero Business"
    telefono = "991090016"  # NUEVO NÚMERO DE WHATSAPP BUSINESS
    
    print(f"Creando contacto de prueba:")
    print(f"  Nombre: {nombre} - {info}")
    print(f"  Teléfono: +51{telefono}")
    print()
    
    try:
        contact_body = {
            "names": [{
                "givenName": nombre,
                "familyName": info,
                "displayName": f"{nombre} - {info}"
            }],
            "phoneNumbers": [{
                "value": f"+51{telefono}",
                "type": "mobile"
            }],
            "organizations": [{
                "name": "Test WhatsApp Business",
                "title": info
            }],
            "memberships": [{
                "contactGroupMembership": {
                    "contactGroupResourceName": "contactGroups/myContacts"
                }
            }]
        }
        
        result = service.people().createContact(body=contact_body).execute()
        
        print("✅ CONTACTO CREADO EXITOSAMENTE!")
        print(f"Resource Name: {result.get('resourceName', 'N/A')}")
        print()
        
        print("=" * 70)
        print("VERIFICACIÓN EN WHATSAPP BUSINESS:")
        print("=" * 70)
        print()
        print("1. Abre WhatsApp Business en tu celular")
        print(f"2. Busca el número: +51{telefono}")
        print(f"3. Debería aparecer como: '{nombre} - {info}'")
        print()
        print("4. Envía un mensaje de prueba desde WhatsApp Business")
        print("   (El contacto ya está sincronizado automáticamente)")
        print()
        print("Si aparece el contacto → ✅ Sincronización funcionando")
        print("Si NO aparece → Espera 1-2 minutos y vuelve a buscar")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
