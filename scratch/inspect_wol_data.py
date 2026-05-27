import requests

SUPABASE_URL = "https://llrhimiivjpmxelffxef.supabase.co/rest/v1/control_wol"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxscmhpbWlpdmpwbXhlbGZmeGVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY0NzM0NDEsImV4cCI6MjA2MjA0OTQ0MX0.zxWg5wSANpUfCK5OeWvwK5xQbLqgcuegKPT6gDdH5F0"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def inspect():
    # Consultar todos los registros de la tabla
    response = requests.get(SUPABASE_URL, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Data: {response.text}")

if __name__ == "__main__":
    inspect()
