import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata.readonly']

# Rutas dinámicas para que funcione tanto en Windows local como en Linux (Hostinger)
G_DRIVE_UPLOADER_DIR = Path(__file__).resolve().parent
BASE_DIR = G_DRIVE_UPLOADER_DIR.parent.parent # Sube a Scraper.Neoauto o /opt/crm_neoauto

# Apuntamos a los tokens que ya existen en el scraper de Neoauto
GOOGLE_DRIVE_DIR = BASE_DIR / "google_drive"
CLIENT_SECRET_FILE = GOOGLE_DRIVE_DIR / 'client_secret.json'

# El token lo guardaremos LOCALMENTE aquí para que no interfiera con el del Scraper
TOKEN_FILE = G_DRIVE_UPLOADER_DIR / 'token.json'

def get_drive_service():
    """
    Obtiene el servicio de Google Drive usando token.json (OAuth User),
    lo cual permite usar los 5TB de cuota de la cuenta rgutil@gmail.com.
    """
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(f"No se encontró client_secret.json en {GOOGLE_DRIVE_DIR}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(str(TOKEN_FILE), 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def create_folder(service, parent_id, folder_name):
    """
    Crea una subcarpeta en Google Drive usando OAuth.
    """
    try:
        # Verificar si la carpeta ya existe
        query = f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        results = service.files().list(
            q=query, spaces='drive', fields='files(id, name)',
            includeItemsFromAllDrives=True, supportsAllDrives=True
        ).execute()
        
        existing = results.get('files', [])
        if existing:
            return True, existing[0]['id']
            
        # Si no existe, crear
        metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        
        file = service.files().create(
            body=metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        return True, file.get('id')
    except Exception as e:
        return False, str(e)

def upload_file(service, file_bytes, file_name, folder_id, mime_type='application/pdf'):
    """
    Sube un archivo desde BytesIO usando OAuth.
    """
    try:
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        
        # Compartir (hacer legible para cualquiera con el link) si se desea, 
        # o simplemente retornar el webViewLink
        return True, file
        
    except Exception as e:
        return False, str(e)
