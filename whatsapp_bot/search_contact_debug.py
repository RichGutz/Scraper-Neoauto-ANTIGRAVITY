import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
BASE_DIR = Path('c:/Users/rguti/Scraper.Neoauto')
CREDENTIALS_DIR = BASE_DIR / 'rpta.automatica.acreedores'
TOKEN_PATH = CREDENTIALS_DIR / 'token.json'

def find_contact(phone_query):
    if not TOKEN_PATH.exists():
        print('[ERROR] Token no encontrado')
        return
        
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    service = build('people', 'v1', credentials=creds)
    
    print(f'Buscando numero: {phone_query}...')
    
    # Try searching directly first (exact or partial)
    try:
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,phoneNumbers'
        ).execute()
        
        connections = results.get('connections', [])
        found_contacts = []
        
        for person in connections:
            phones = person.get('phoneNumbers', [])
            for p in phones:
                val = p.get('value', '').replace(' ', '').replace('-', '').replace('+', '')
                if phone_query in val:
                    names = person.get('names', [])
                    name = names[0].get('displayName', 'Sin nombre') if names else 'Sin nombre'
                    found_contacts.append(f'{name} ({p.get("value")})')
        
        if found_contacts:
            print('\n[ENCONTRADO]')
            for c in found_contacts:
                print(f' - {c}')
        else:
            print('\n[INFO] No se encontro el contacto en Google Contacts.')
            
    except Exception as e:
        print(f'[ERROR] {e}')

if __name__ == "__main__":
    find_contact('984798908')
