"""
FASE 3 - DEPLOY COMPLETO CRM_NEOAUTO AL VPS HOSTINGER
======================================================
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
GH_TOKEN = os.getenv("GH_TOKEN")

REPO_URL    = f"https://{GH_TOKEN}@github.com/RichGutz/Scraper-Neoauto-ANTIGRAVITY.git"
BRANCH      = "funcional.hostinger.21.03.26"
APP_DIR     = "/opt/crm_neoauto"
VENV_DIR    = f"{APP_DIR}/venv"
SERVICE     = "crm_neoauto"
APP_PORT    = "8502"
SUBDOMAIN   = "crm-neoauto.geeksoft.tech"

def ssh_run(client, cmd, desc=""):
    print(f"\n[{desc}]")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out: print(f" >> {out[:300]}")
    return out, err

def deploy():
    print(f"\n[ORQUESTADOR MAESTRO CRM_NEOAUTO]")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname=VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
        
        # 1. Deps
        ssh_run(client, "export DEBIAN_FRONTEND=noninteractive && apt-get update -qq && apt-get install -y -qq git python3-venv nginx certbot python3-certbot-nginx", "1. Deps")
        
        # 2. Repo
        ssh_run(client, f"if [ -d '{APP_DIR}/.git' ]; then cd {APP_DIR} && git fetch --all && git reset --hard origin/{BRANCH} && git pull origin {BRANCH}; else rm -rf {APP_DIR} && git clone -b {BRANCH} {REPO_URL} {APP_DIR}; fi", "2. Git")
        
        # 3. Env
        sftp = client.open_sftp()
        sftp.put(local_env_path, f"{APP_DIR}/.env")
        sftp.close()
        
        # 4. Pip
        ssh_run(client, f"python3 -m venv {VENV_DIR} && {VENV_DIR}/bin/pip install --upgrade pip -q && {VENV_DIR}/bin/pip install streamlit pandas supabase python-dotenv webdriver-manager beautifulsoup4 google-api-python-client google-auth-httplib2 google-auth-oauthlib -q", "4. Python")
        
        # 5. Service (Systemd)
        service_cfg = f"""[Unit]\nDescription=CRM Neoauto\nAfter=network.target\n[Service]\nUser=root\nWorkingDirectory={APP_DIR}\nEnvironment="PATH={VENV_DIR}/bin"\nExecStart={VENV_DIR}/bin/streamlit run CRM-NEOAUTO/frontend_app.py --server.port={APP_PORT} --server.address=127.0.0.1\nRestart=always\n[Install]\nWantedBy=multi-user.target"""
        ssh_run(client, f"echo '{service_cfg}' > /etc/systemd/system/{SERVICE}.service && systemctl daemon-reload && systemctl enable {SERVICE} && systemctl restart {SERVICE}", "5. Service")
        
        # 6. Nginx
        nginx_cfg = f"server {{ listen 80; server_name {SUBDOMAIN}; location / {{ proxy_pass http://127.0.0.1:{APP_PORT}; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection \"upgrade\"; proxy_set_header Host $host; }} }}"
        ssh_run(client, f"echo '{nginx_cfg}' > /etc/nginx/sites-available/{SERVICE} && ln -sf /etc/nginx/sites-available/{SERVICE} /etc/nginx/sites-enabled/{SERVICE} && nginx -t && systemctl reload nginx", "6. Nginx")
        
        # 7. SSL
        ssh_run(client, f"certbot --nginx -d {SUBDOMAIN} --non-interactive --agree-tos -m contacto@geeksoft.pe --redirect", "7. SSL")
        
        print("\n[OK] DESPLIEGUE COMPLETO EXITOSO")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy()
