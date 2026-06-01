import sys
sys.path.append('C:/Users/rguti/Scraper.Neoauto/CRM-NEOAUTO/G_Drive_Uploader')
from drive_api import get_drive_service
service = get_drive_service()
results = service.files().list(q="'1_BvUhnTI5J987wsJao4sK3mDX31uNKcd' in parents and trashed=false", fields="files(id, name, mimeType, parents)").execute()
for f in results.get('files', []):
    print(f"Name: {f.get('name')}, Type: {f.get('mimeType')}, Parents: {f.get('parents')}")
