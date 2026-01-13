"""
Verificar contactos creados en Google Contacts
"""

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
    print("=" * 70)
    print("VERIFICAR CONTACTOS EN GOOGLE CONTACTS")
    print("=" * 70)
    print()
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('people', 'v1', credentials=creds)
    
    # Buscar contactos recientes (últimos 50)
    print("Buscando contactos recientes en Google Contacts...")
    try:
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=50,
            personFields='names,phoneNumbers,organizations'
        ).execute()
        
        connections = results.get('connections', [])
        
        if not connections:
            print("❌ No se encontraron contactos.")
            return
        
        print(f"✓ Encontrados {len(connections)} contactos\n")
        
        # Filtrar contactos de Neoauto y Marketplace
        neoauto_contacts = []
        marketplace_contacts = []
        
        for person in connections:
            names = person.get('names', [])
            phones = person.get('phoneNumbers', [])
            orgs = person.get('organizations', [])
            
            if not names or not phones:
                continue
            
            name = names[0].get('displayName', 'Sin nombre')
            phone = phones[0].get('value', 'Sin teléfono')
            org = orgs[0].get('name', '') if orgs else ''
            
            if 'Neoauto Lead' in org:
                neoauto_contacts.append((name, phone))
            elif 'Marketplace Lead' in org:
                marketplace_contacts.append((name, phone))
        
        print("=" * 70)
        print(f"CONTACTOS DE NEOAUTO: {len(neoauto_contacts)}")
        print("=" * 70)
        for i, (name, phone) in enumerate(neoauto_contacts, 1):
            print(f"{i}. {name} - {phone}")
        
        print()
        print("=" * 70)
        print(f"CONTACTOS DE MARKETPLACE: {len(marketplace_contacts)}")
        print("=" * 70)
        for i, (name, phone) in enumerate(marketplace_contacts, 1):
            print(f"{i}. {name} - {phone}")
        
        print()
        print("=" * 70)
        print("VERIFICACIÓN EN WHATSAPP BUSINESS:")
        print("=" * 70)
        print()
        print("1. Abre WhatsApp Business en tu celular")
        print("2. Ve a Configuración > Cuenta > Privacidad")
        print("3. Verifica que 'Sincronizar contactos' esté ACTIVADO")
        print("4. Ve a Configuración > Cuentas > Google")
        print("5. Verifica que la sincronización de Contactos esté ACTIVADA")
        print("6. Espera 1-2 minutos y busca los números en WhatsApp")
        print()
        print("Si no aparecen, intenta:")
        print("- Cerrar y abrir WhatsApp Business")
        print("- Forzar sincronización: Configuración > Cuentas > Google > Sincronizar ahora")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
