from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.modify']

def check_identity():
    script_dir = Path(__file__).parent
    token_path = script_dir / 'token.json'
    
    if not token_path.exists():
        print(f"ERROR: No token.json found at {token_path}")
        return

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        service = build('gmail', 'v1', credentials=creds)
        
        profile = service.users().getProfile(userId='me').execute()
        print(f"Authenticated User: {profile['emailAddress']}")
        print(f"Messages Total: {profile['messagesTotal']}")
        
    except Exception as e:
        print(f"Error validating token: {e}")

if __name__ == "__main__":
    check_identity()
