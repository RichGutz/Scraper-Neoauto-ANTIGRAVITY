import requests
import json

SUPABASE_URL = "https://llrhimiivjpmxelffxef.supabase.co/rest/v1/control_wol"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxscmhpbWlpdmpwbXhlbGZmeGVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY0NzM0NDEsImV4cCI6MjA2MjA0OTQ0MX0.zxWg5wSANpUfCK5OeWvwK5xQbLqgcuegKPT6gDdH5F0"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def check_and_trigger():
    print("Verificando si la tabla 'control_wol' y el registro de la ThinkPad existen...")
    # 1. Intentar consultar el registro
    url_get = f"{SUPABASE_URL}?dispositivo=eq.thinkpad_t430s"
    response = requests.get(url_get, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if len(data) == 0:
            print("El registro no existe. Creando registro inicial...")
            # Insertar registro
            payload = {
                "dispositivo": "thinkpad_t430s",
                "mac_address": "3c:97:0e:7a:97:78",
                "solicitar_encendido": True,
                "estado": "offline"
            }
            res_ins = requests.post(SUPABASE_URL, headers=headers, data=json.dumps(payload))
            if res_ins.status_code in [200, 201]:
                print("SUCCESS: Registro inicial creado y solicitud de encendido enviada!")
            else:
                print(f"ERROR al insertar registro: {res_ins.status_code} - {res_ins.text}")
        else:
            print("El registro existe. Enviando orden de encendido (solicitar_encendido = True)...")
            payload = {
                "solicitar_encendido": True
            }
            res_upd = requests.patch(url_get, headers=headers, data=json.dumps(payload))
            if res_upd.status_code in [200, 204]:
                print("SUCCESS: Orden de encendido enviada con exito a Supabase!")
            else:
                print(f"ERROR al actualizar registro: {res_upd.status_code} - {res_upd.text}")
    else:
        print(f"ERROR: No se pudo conectar a la tabla. ¿Creaste la tabla en Supabase?\nCodigo: {response.status_code}\nDetalle: {response.text}")
        print("\n--> RECUERDA: Debes crear la tabla en el SQL Editor de tu panel de Supabase usando el codigo SQL que documentamos en Plan.md")

if __name__ == "__main__":
    check_and_trigger()
