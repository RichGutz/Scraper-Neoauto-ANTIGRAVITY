"""
FASE 3 - DEPLOY RAPIDO CRM_NEOAUTO (STREAMLINED)
======================================================
Este script está optimizado. Su único trabajo es jalar el 
código nuevo de Github y reiniciar Streamlit instantáneamente.
"""
import paramiko
import os
import sys
from dotenv import load_dotenv

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
local_env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(local_env_path)

BRANCH      = "master"
APP_DIR     = "/opt/crm_neoauto"
SERVICE     = "crm_neoauto"

def ssh_run(client, cmd, desc="", timeout=90):
    print(f"\n[{desc}]")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="ignore").strip()
    err = stderr.read().decode("utf-8", errors="ignore").strip()
    if out:
        print(f" >> {out[:300]}")
    if err and "warning" not in err.lower():
        print(f" !! {err[:300]}")
    return out, err

def deploy_fast():
    print(f"\n{'='*55}")
    print(f"  [FAST DEPLOY CRM_NEOAUTO - SOLO CODIGO]")
    print(f"{'='*55}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[1/3] Autenticando en {VPS_HOST}...")
        client.connect(hostname=VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=10)
        
        ssh_run(client,
            f"cd {APP_DIR} && git fetch --all && git reset --hard origin/{BRANCH} && git pull origin {BRANCH}",
            "2/3 Descargando actualizaciones de Git")

        ssh_run(client,
            f"{APP_DIR}/venv/bin/pip install -r {APP_DIR}/requirements.txt -q || true",
            "2.5/3 Instalando dependencias en venv",
            timeout=300)

        ssh_run(client,
            f"systemctl daemon-reload && systemctl restart {SERVICE}",
            "3/3 Reiniciando Streamlit")


        print(f"\n{'='*55}")
        print(f"  [OK] DESPLIEGUE COMPLETADO")
        print(f"{'='*55}\n")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    deploy_fast()
