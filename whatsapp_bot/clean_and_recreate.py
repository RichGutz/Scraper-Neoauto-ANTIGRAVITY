"""
Script DEFINITIVO: Eliminar TODOS los contactos relacionados con Neoauto y recrearlos

Este script es más agresivo y elimina cualquier contacto que parezca ser del bot.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
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

# Teléfonos de los leads (para identificar contactos a eliminar)
LEAD_PHONES = [
    "922285372", "914316088", "997597657",
    "975054300", "999221760", "998239387",
    "988888888", "999999999"  # Incluir contactos de prueba
]

def init_db():
    """Conectar a Supabase"""
    try:
        current_script_dir = Path(__file__).resolve().parent
        dotenv_path = current_script_dir / ".env"
        load_dotenv(dotenv_path)
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print(f"ERROR: No se encontraron credenciales en {dotenv_path}")
            return None
            
        return create_client(url, key)
    except Exception as e:
        print(f"Error conectando a DB: {e}")
        return None

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

def get_all_google_contacts(service):
    """Obtiene todos los contactos de Google"""
    try:
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,phoneNumbers,organizations,metadata'
        ).execute()
        return results.get('connections', [])
    except Exception as e:
        print(f"Error obteniendo contactos: {e}")
        return []

def delete_contact(service, resource_name):
    """Elimina un contacto de Google"""
    try:
        service.people().deleteContact(resourceName=resource_name).execute()
        return True
    except Exception as e:
        return False

def create_contact_final(service, nombre_completo, info_auto, telefono):
    """Crea un contacto con la estructura FINAL"""
    try:
        if not telefono.isdigit() or len(telefono) != 9:
            return False
        
        contact_body = {
            "names": [{
                "givenName": nombre_completo,
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
        
        service.people().createContact(body=contact_body).execute()
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    print("=" * 70)
    print("LIMPIEZA TOTAL Y RECREACIÓN")
    print("=" * 70)
    print()
    
    # 1. Autenticar con Google
    print("1. Autenticando con Google...")
    creds = autenticar_google()
    if not creds:
        return
    service = build('people', 'v1', credentials=creds)
    print("   ✓ Autenticado\n")
    
    # 2. Obtener todos los contactos
    print("2. Obteniendo todos los contactos...")
    all_contacts = get_all_google_contacts(service)
    print(f"   ✓ {len(all_contacts)} contactos en Google\n")
    
    # 3. Eliminar TODOS los contactos relacionados
    print("3. Eliminando TODOS los contactos relacionados con Neoauto...")
    print("=" * 70)
    
    deleted = 0
    for contact in all_contacts:
        should_delete = False
        names = contact.get('names', [])
        phones = contact.get('phoneNumbers', [])
        orgs = contact.get('organizations', [])
        
        # Criterio 1: Tiene organización "Neoauto Lead"
        if orgs and any(org.get('name') == 'Neoauto Lead' for org in orgs):
            should_delete = True
        
        # Criterio 2: El teléfono coincide con algún lead
        for phone in phones:
            phone_value = phone.get('value', '').replace('+51', '').replace('+', '').replace(' ', '').strip()
            if phone_value in LEAD_PHONES:
                should_delete = True
                break
        
        if should_delete:
            resource_name = contact.get('resourceName')
            display_name = names[0].get('displayName', 'Sin nombre') if names else 'Sin nombre'
            print(f"   Eliminando: {display_name[:50]}")
            if delete_contact(service, resource_name):
                deleted += 1
            time.sleep(0.2)
    
    print(f"\n   ✓ {deleted} contactos eliminados\n")
    
    # 4. Esperar un poco para que Google sincronice
    print("4. Esperando sincronización de Google...")
    time.sleep(3)
    print("   ✓ Listo\n")
    
    # 5. Conectar a Supabase y obtener leads
    print("5. Obteniendo leads de Supabase...")
    supabase = init_db()
    if not supabase:
        return
    
    try:
        response = supabase.table("crm_leads").select("*").execute()
        all_leads = response.data
        
        leads = []
        for lead in all_leads:
            phone = lead.get('phone', '').replace('+51', '').replace('+', '').strip()
            if phone.isdigit() and len(phone) == 9:
                leads.append(lead)
        
        print(f"   ✓ {len(leads)} leads válidos\n")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 6. Recrear contactos
    print("6. Recreando contactos...")
    print("=" * 70)
    
    created = 0
    for lead in leads:
        phone = lead.get('phone', '').replace('+51', '').replace('+', '').strip()
        name = lead.get('name', 'Desconocido')
        car_url = lead.get('car_url', '')
        
        info_auto = "Auto Neoauto"
        if car_url and "neoauto.com" in car_url:
            try:
                slug = car_url.split('/')[-1]
                parts = slug.split('-')
                if parts and parts[-1].isdigit():
                    parts.pop()
                if len(parts) > 0:
                    info_auto = " ".join([p.capitalize() for p in parts])
            except:
                pass
        
        print(f"\n{name} - {info_auto}")
        print(f"   Tel: +51{phone}")
        
        if create_contact_final(service, name, info_auto, phone):
            print(f"   ✅ Creado")
            created += 1
        else:
            print(f"   ❌ Error")
        
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print(f"  • Contactos eliminados: {deleted}")
    print(f"  • Contactos creados: {created}")
    print("=" * 70)
    print("\n✅ PROCESO COMPLETADO")
    print("\nPRÓXIMOS PASOS:")
    print("1. REINICIA WhatsApp Dual (cierra y abre la app)")
    print("2. Espera 1 minuto")
    print("3. Verifica que aparezcan los nombres")

if __name__ == "__main__":
    main()
