"""
Script de Diagnóstico: Google Contacts API
Verifica si la sincronización con Google Contacts está funcionando
"""

import os
import sys
from pathlib import Path

# Configurar consola para soportar emojis UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuración
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/contacts']
BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_DIR = BASE_DIR / "gmail_sender" # Actualizado a la ruta unificada
TOKEN_PATH = CREDENTIALS_DIR / 'token.json'
CREDENTIALS_PATH = CREDENTIALS_DIR / 'credentials.json'

def autenticar_google():
    """Reutiliza la lógica de autenticación existente"""
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

def test_create_contact():
    """Prueba crear un contacto de test"""
    print("=== TEST: Google Contacts API ===\n")
    
    # 1. Autenticar
    print("1. Autenticando con Google...")
    creds = autenticar_google()
    if not creds:
        print("   ❌ FALLO: No se pudo autenticar")
        return
    print("   ✓ Autenticación exitosa\n")
    
    # 2. Verificar que People API esté habilitada
    print("2. Verificando acceso a People API...")
    try:
        service_people = build('people', 'v1', credentials=creds)
        print("   ✓ Servicio People API inicializado\n")
    except Exception as e:
        print(f"   ❌ FALLO: {e}")
        print("   SOLUCIÓN: Habilita la API de People en Google Cloud Console")
        return
    
    # 3. Intentar crear un contacto de prueba
    print("3. Creando contacto de prueba...")
    test_contact_data = {
        'nombre_completo': 'Test Usuario',
        'telefono_real': '999999999',
        'info_auto': 'Toyota Corolla 2020'
    }
    
    full_display_name = f"{test_contact_data['nombre_completo']} - {test_contact_data['info_auto']}"
    
    try:
        result = service_people.people().createContact(body={
            "names": [{"givenName": full_display_name}],
            "phoneNumbers": [{"value": f"+51{test_contact_data['telefono_real']}"}],
            "memberships": [{"contactGroupMembership": {"contactGroupResourceName": "contactGroups/myContacts"}}]
        }).execute()
        
        print(f"   ✓ Contacto creado exitosamente!")
        print(f"   Nombre: {full_display_name}")
        print(f"   Teléfono: +51{test_contact_data['telefono_real']}")
        print(f"   Resource Name: {result.get('resourceName', 'N/A')}\n")
        
        # 4. Verificar que el contacto existe
        print("4. Verificando que el contacto se creó...")
        try:
            connections = service_people.people().connections().list(
                resourceName='people/me',
                pageSize=10,
                personFields='names,phoneNumbers'
            ).execute()
            
            contacts = connections.get('connections', [])
            print(f"   ✓ Total de contactos visibles: {len(contacts)}")
            
            # Buscar nuestro contacto de prueba
            found = False
            for contact in contacts:
                names = contact.get('names', [])
                if names and full_display_name in names[0].get('displayName', ''):
                    found = True
                    print(f"   ✓ Contacto de prueba encontrado en la lista!")
                    break
            
            if not found:
                print(f"   ⚠ Contacto creado pero no aparece en la lista inmediatamente (puede tomar unos segundos)")
                
        except Exception as e:
            print(f"   ⚠ No se pudo verificar: {e}")
        
        print("\n=== DIAGNÓSTICO COMPLETO ===")
        print("✓ La sincronización con Google Contacts ESTÁ FUNCIONANDO")
        print("\nNOTA: Si el contacto no aparece en tu teléfono:")
        print("  1. Verifica que la cuenta de Google esté sincronizada en tu dispositivo")
        print("  2. Ve a Configuración > Cuentas > Google > Sincronización de cuenta")
        print("  3. Asegúrate de que 'Contactos' esté activado")
        print("  4. Fuerza una sincronización manual")
        
    except Exception as e:
        print(f"   ❌ FALLO al crear contacto: {e}")
        print(f"\n   Detalles del error: {type(e).__name__}")
        
        if "403" in str(e):
            print("\n   SOLUCIÓN: La API de People no está habilitada o no tienes permisos.")
            print("   1. Ve a https://console.cloud.google.com/apis/library/people.googleapis.com")
            print("   2. Habilita la API")
            print("   3. Borra el archivo token.json y vuelve a autenticar")
        elif "401" in str(e):
            print("\n   SOLUCIÓN: Token expirado o inválido.")
            print("   1. Borra el archivo token.json")
            print("   2. Vuelve a ejecutar este script")

if __name__ == "__main__":
    test_create_contact()
