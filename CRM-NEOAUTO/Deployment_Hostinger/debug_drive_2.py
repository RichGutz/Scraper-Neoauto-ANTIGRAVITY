import sys
sys.path.append('C:/Users/rguti/Scraper.Neoauto/CRM-NEOAUTO/G_Drive_Uploader')
from drive_api import get_drive_service
service = get_drive_service()

def list_files(parent_id, prefix=""):
    results = service.files().list(q=f"'{parent_id}' in parents and trashed=false", fields="files(id, name, mimeType)").execute()
    for f in results.get('files', []):
        print(f"{prefix}- {f['name']} ({f['mimeType']})")
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            list_files(f['id'], prefix + "  ")

print("Contenido de CRM_ROOT_FOLDER_ID:")
list_files("1_BvUhnTI5J987wsJao4sK3mDX31uNKcd")
