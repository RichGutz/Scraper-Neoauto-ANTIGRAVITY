import paramiko
import os

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

local_token = r"C:\Users\rguti\Scraper.Neoauto\CRM-NEOAUTO\G_Drive_Uploader\token.json"
remote_token = "/opt/crm_neoauto/CRM-NEOAUTO/G_Drive_Uploader/token.json"

print("Conectando SFTP...")
transport = paramiko.Transport((VPS_HOST, VPS_PORT))
transport.connect(username=VPS_USER, password=VPS_PASS)
sftp = paramiko.SFTPClient.from_transport(transport)

try:
    print(f"Subiendo {local_token} -> {remote_token}...")
    sftp.put(local_token, remote_token)
    print("[OK] token.json subido con exito.")
except Exception as e:
    print(f"[ERROR] {e}")
finally:
    sftp.close()
    transport.close()
