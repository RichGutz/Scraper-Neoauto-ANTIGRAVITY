"""
Crear contactos de prueba usando EL MISMO MÉTODO que funcionó
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
    print("=== CREANDO CONTACTOS CON MÉTODO QUE FUNCIONÓ ===\n")
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('people', 'v1', credentials=creds)
    
    # Lista de contactos a crear (MISMO FORMATO que el test que funcionó)
    contactos = [
        {
            "nombre": "Ana María TEST",
            "info_auto": "Kia Picanto 2017",
            "telefono": "975054300"
        },
        {
            "nombre": "Jorge TEST",
            "info_auto": "Hyundai Creta 2024",
            "telefono": "999221760"
        },
        {
            "nombre": "Gisella TEST",
            "info_auto": "Hyundai Santa Fe 2017",
            "telefono": "998239387"
        }
    ]
    
    print("Creando contactos...\n")
    
    for contacto in contactos:
        nombre = contacto["nombre"]
        info_auto = contacto["info_auto"]
        telefono = contacto["telefono"]
        
        print(f"{nombre} - {info_auto}")
        print(f"  Tel: +51{telefono}")
        
        try:
            # EXACTAMENTE EL MISMO FORMATO que el test que funcionó
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
            print(f"  ✅ Creado: {result.get('resourceName', 'N/A')}\n")
            
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
        
        time.sleep(0.5)
    
    print("=" * 70)
    print("✅ CONTACTOS CREADOS")
    print("=" * 70)
    print("\nPRÓXIMOS PASOS:")
    print("1. Cierra COMPLETAMENTE WhatsApp Dual (Forzar detención)")
    print("2. Espera 10 segundos")
    print("3. Abre WhatsApp Dual")
    print("4. Busca estos números:")
    print("   • +51975054300 → 'Ana María TEST Kia Picanto 2017'")
    print("   • +51999221760 → 'Jorge TEST Hyundai Creta 2024'")
    print("   • +51998239387 → 'Gisella TEST Hyundai Santa Fe 2017'")

if __name__ == "__main__":
    main()
