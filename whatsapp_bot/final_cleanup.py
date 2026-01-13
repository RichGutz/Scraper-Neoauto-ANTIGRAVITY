"""
Limpiar nombres en Supabase y recrear contactos correctamente
"""

import os
import re
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

def init_db():
    """Conectar a Supabase"""
    current_script_dir = Path(__file__).resolve().parent
    dotenv_path = current_script_dir / ".env"
    load_dotenv(dotenv_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    return create_client(url, key)

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
    print("LIMPIEZA FINAL: Supabase + Google Contacts")
    print("=" * 70)
    print()
    
    # 1. Conectar a Supabase
    print("1. Conectando a Supabase...")
    supabase = init_db()
    
    # 2. Limpiar nombres en Supabase
    print("2. Limpiando nombres en Supabase...")
    response = supabase.table("crm_leads").select("*").execute()
    
    for lead in response.data:
        old_name = lead['name']
        # Limpiar "Teléfono" del nombre
        new_name = re.sub(r'\s+Teléfono\s*$', '', old_name, flags=re.IGNORECASE)
        
        if old_name != new_name:
            print(f"   Limpiando: '{old_name}' → '{new_name}'")
            supabase.table("crm_leads").update({"name": new_name}).eq("phone", lead['phone']).execute()
    
    print("   ✓ Nombres limpiados\n")
    
    # 3. Obtener leads limpios
    print("3. Obteniendo leads limpios...")
    response = supabase.table("crm_leads").select("*").execute()
    leads = [l for l in response.data if l['phone'].isdigit() and len(l['phone']) == 9]
    print(f"   ✓ {len(leads)} leads válidos\n")
    
    # 4. Autenticar con Google
    print("4. Autenticando con Google...")
    creds = autenticar_google()
    if not creds:
        return
    service = build('people', 'v1', credentials=creds)
    print("   ✓ Autenticado\n")
    
    # 5. Eliminar TODOS los contactos del bot
    print("5. Eliminando contactos antiguos del bot...")
    all_contacts = service.people().connections().list(
        resourceName='people/me',
        pageSize=1000,
        personFields='names,phoneNumbers,organizations,metadata'
    ).execute().get('connections', [])
    
    deleted = 0
    for contact in all_contacts:
        orgs = contact.get('organizations', [])
        if orgs and any(org.get('name') == 'Neoauto Lead' for org in orgs):
            resource_name = contact.get('resourceName')
            service.people().deleteContact(resourceName=resource_name).execute()
            deleted += 1
            time.sleep(0.2)
    
    print(f"   ✓ {deleted} contactos eliminados\n")
    
    # 6. Recrear contactos con nombres limpios
    print("6. Recreando contactos con nombres limpios...")
    print("=" * 70)
    
    created = 0
    for lead in leads:
        phone = lead['phone']
        name = lead['name']  # Ya está limpio
        car_url = lead.get('car_url', '')
        
        # Extraer info del auto
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
        
        try:
            contact_body = {
                "names": [{
                    "givenName": name,
                    "familyName": info_auto
                }],
                "phoneNumbers": [{
                    "value": f"+51{phone}",
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
            print(f"   ✅ Creado")
            created += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print(f"  • Nombres limpiados en Supabase")
    print(f"  • Contactos eliminados: {deleted}")
    print(f"  • Contactos creados: {created}")
    print("=" * 70)
    print("\n✅ PROCESO COMPLETADO")
    print("\nPRÓXIMOS PASOS:")
    print("1. REINICIA WhatsApp Dual (Forzar detención)")
    print("2. Abre WhatsApp Dual")
    print("3. Los contactos deberían aparecer correctamente")

if __name__ == "__main__":
    main()
