import sys
import os
from pathlib import Path

# Add google_drive directory to sys.path to import get_drive_service and others
scraper_dir = Path(__file__).resolve().parent.parent
google_drive_dir = scraper_dir / 'google_drive'
if str(google_drive_dir) not in sys.path:
    sys.path.append(str(google_drive_dir))

from drive_uploader import get_drive_service, create_or_get_folder, get_shareable_link, DRIVE_ROOT_FOLDER_NAME

def get_link():
    try:
        service = get_drive_service()
        root_drive_folder_id = create_or_get_folder(service, DRIVE_ROOT_FOLDER_NAME)
        if not root_drive_folder_id:
            print("No se pudo obtener la carpeta raíz en Drive.")
            return
        
        outputs_drive_folder_id = create_or_get_folder(service, 'outputs', root_drive_folder_id)
        if not outputs_drive_folder_id:
            print("No se pudo obtener la carpeta 'outputs' en Drive.")
            return

        q = f"name='index.semanal.html' and '{outputs_drive_folder_id}' in parents and trashed=false"
        response = service.files().list(q=q, spaces='drive', fields='files(id)').execute()
        files = response.get('files', [])
        if files:
            file_id = files[0]['id']
            link = get_shareable_link(service, file_id)
            print(f"LINK_OBTENIDO: {link}")
        else:
            print("index.semanal.html no encontrado en Drive.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    get_link()
