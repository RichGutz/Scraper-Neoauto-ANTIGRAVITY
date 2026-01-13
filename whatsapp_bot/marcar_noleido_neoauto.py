"""
Marcar correos de Neoauto como NO LEÍDOS para pruebas
"""

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuración
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
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
    print("=" * 70)
    print("MARCAR CORREOS DE NEOAUTO COMO NO LEÍDOS")
    print("=" * 70)
    print()
    
    creds = autenticar_google()
    if not creds:
        return
    
    service = build('gmail', 'v1', credentials=creds)
    
    # Buscar correos de Neoauto (leídos o no leídos)
    print("Buscando correos de Neoauto...")
    try:
        results = service.users().messages().list(
            userId='me',
            q='from:contacto@neoauto.pe',
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("❌ No se encontraron correos de Neoauto.")
            return
        
        print(f"✓ Encontrados {len(messages)} correos\n")
        
        # Marcar todos como no leídos
        for i, msg in enumerate(messages, 1):
            msg_id = msg['id']
            
            # Obtener detalles del correo
            message = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Sin fecha')
            
            print(f"{i}. Asunto: {subject}")
            print(f"   Fecha: {date}")
            
            # Marcar como no leído
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            
            print(f"   ✅ Marcado como NO LEÍDO\n")
        
        print("=" * 70)
        print(f"✅ {len(messages)} correo(s) marcado(s) como NO LEÍDOS")
        print("=" * 70)
        print("\nAhora el bot los procesará en la próxima ejecución.")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
