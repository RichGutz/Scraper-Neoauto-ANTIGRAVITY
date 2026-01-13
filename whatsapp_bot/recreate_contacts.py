"""
Script para LIMPIAR y RECREAR contactos correctamente

Este script:
1. Elimina TODOS los contactos del bot (organización "Neoauto Lead")
2. Elimina contactos duplicados antiguos
3. Recrea los contactos con la estructura correcta desde Supabase
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
            
        print(f"✓ Conectado a Supabase")
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
        print(f"   Error eliminando: {e}")
        return False

def create_contact_correct(service, nombre_completo, info_auto, telefono):
    """Crea un contacto con la estructura CORRECTA"""
    try:
        # Asegurarse de que el teléfono sea válido
        if not telefono.isdigit() or len(telefono) != 9:
            print(f"   ⚠️  Teléfono inválido: {telefono}")
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
        print(f"   Error creando: {e}")
        return False

def main():
    print("=" * 70)
    print("LIMPIEZA Y RECREACIÓN DE CONTACTOS")
    print("=" * 70)
    print()
    
    # 1. Conectar a Supabase
    print("1. Conectando a Supabase...")
    supabase = init_db()
    if not supabase:
        return
    
    # 2. Obtener leads válidos
    print("2. Obteniendo leads de la base de datos...")
    try:
        response = supabase.table("crm_leads").select("*").execute()
        all_leads = response.data
        
        # Filtrar leads con teléfonos válidos
        leads = []
        for lead in all_leads:
            phone = lead.get('phone', '').replace('+51', '').replace('+', '').strip()
            if phone.isdigit() and len(phone) == 9:
                leads.append(lead)
        
        print(f"   ✓ {len(leads)} leads válidos encontrados\n")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    if not leads:
        print("No hay leads válidos para procesar.")
        return
    
    # 3. Autenticar con Google
    print("3. Autenticando con Google...")
    creds = autenticar_google()
    if not creds:
        return
    service = build('people', 'v1', credentials=creds)
    print("   ✓ Autenticado\n")
    
    # 4. Obtener todos los contactos de Google
    print("4. Obteniendo contactos actuales de Google...")
    all_contacts = get_all_google_contacts(service)
    print(f"   ✓ {len(all_contacts)} contactos en Google\n")
    
    # 5. ELIMINAR todos los contactos del bot
    print("5. Eliminando contactos antiguos del bot...")
    print("=" * 70)
    
    deleted = 0
    for contact in all_contacts:
        orgs = contact.get('organizations', [])
        names = contact.get('names', [])
        
        # Eliminar si tiene organización "Neoauto Lead" O si el nombre contiene " - " con info de auto
        is_bot_contact = False
        
        if orgs and any(org.get('name') == 'Neoauto Lead' for org in orgs):
            is_bot_contact = True
        elif names:
            display_name = names[0].get('displayName', '')
            # Buscar patrones como "Nombre - Marca Modelo Año"
            if ' - ' in display_name and any(marca in display_name for marca in ['Hyundai', 'Kia', 'Toyota', 'Honda', 'Nissan', 'Mazda', 'Chevrolet', 'Ford']):
                is_bot_contact = True
        
        if is_bot_contact:
            resource_name = contact.get('resourceName')
            display_name = names[0].get('displayName', 'Sin nombre') if names else 'Sin nombre'
            print(f"   Eliminando: {display_name}")
            if delete_contact(service, resource_name):
                deleted += 1
                time.sleep(0.3)
    
    print(f"\n   ✓ {deleted} contactos eliminados\n")
    
    # 6. Recrear contactos
    print("6. Recreando contactos con estructura correcta...")
    print("=" * 70)
    
    created = 0
    errors = 0
    
    for lead in leads:
        phone = lead.get('phone', '').replace('+51', '').replace('+', '').strip()
        name = lead.get('name', 'Desconocido')
        car_url = lead.get('car_url', '')
        
        # Extraer info del auto desde la URL
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
        
        print(f"\n{name}")
        print(f"   Auto: {info_auto}")
        print(f"   Tel: +51{phone}")
        
        if create_contact_correct(service, name, info_auto, phone):
            print(f"   ✅ Creado")
            created += 1
        else:
            print(f"   ❌ Error")
            errors += 1
        
        time.sleep(0.5)
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print(f"  • Contactos eliminados: {deleted}")
    print(f"  • Contactos creados: {created}")
    print(f"  • Errores: {errors}")
    print("=" * 70)
    print("\n✅ PROCESO COMPLETADO")
    print("\nPRÓXIMOS PASOS:")
    print("1. Espera 2-3 minutos para que sincronice")
    print("2. Verifica en WhatsApp Dual que aparezcan los nombres")
    print("3. Si no aparecen, reinicia WhatsApp Dual")

if __name__ == "__main__":
    main()
