import paramiko
import time
import os
from dotenv import load_dotenv

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

# Directorios Locales
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
local_env_path = os.path.join(BASE_DIR, ".env")

# Variables Repositorio
load_dotenv(local_env_path)
GH_TOKEN = os.getenv("GH_TOKEN")
REPO_URL = f"https://{GH_TOKEN}@github.com/RichGutz/Scraper-Neoauto-ANTIGRAVITY.git"
CLONE_DIR = "/opt/crm_neoauto"
BRANCH = "funcional.hostinger.21.03.26"

# Variables Systemd y Nginx
SERVICE_NAME = "crm_neoauto.service"
DOMAIN_NAME = "crm-neoauto.geeksoft.tech"
PORT = 8502

remote_env_path = f"{CLONE_DIR}/.env"

SYSTEMD_FILE = f"""[Unit]
Description=CRM Neoauto Streamlit App
After=network.target

[Service]
User=root
WorkingDirectory={CLONE_DIR}
ExecStart={CLONE_DIR}/venv/bin/streamlit run CRM-NEOAUTO/frontend_app.py --server.port={PORT} --server.address=127.0.0.1
Restart=always

[Install]
WantedBy=multi-user.target
"""

NGINX_FILE = f"""server {{
    listen 80;
    server_name {DOMAIN_NAME};

    location / {{
        proxy_pass http://127.0.0.1:{PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Necesarios para Streamlit WebSockets
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }}
}}
"""

def ssh_exec(ssh, command):
    print(f"Ejecutando: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"  [OUT]: {out[:500]}")
    if err and exit_status != 0: print(f"  [ERR]: {err[:500]}")
    return exit_status == 0

def deploy_to_vps():
    print("="*50)
    print("INICIANDO DESPLIEGUE A HOSTINGER (CRM NEOAUTO)")
    print("="*50)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS)
        print("✓ Conexion SSH Exitosa.")
        
        # 1. Instalar dependencias base si faltan (python-venv, git, nginx)
        ssh_exec(ssh, "apt-get update && apt-get install -y python3-venv git nginx certbot python3-certbot-nginx")
        
        # 2. Setup Directorio y Git Clone / Pull
        print("\n--- CONFIGURANDO REPOSITORIO ---")
        ssh_exec(ssh, f"mkdir -p {CLONE_DIR}")
        
        clone_check, stdout, stderr = ssh.exec_command(f"cd {CLONE_DIR} && git status")
        if clone_check.channel.recv_exit_status() != 0:
            print(f"Clonando repositorio (rama {BRANCH})...")
            ssh_exec(ssh, f"git clone -b {BRANCH} {REPO_URL} {CLONE_DIR}")
        else:
            print("Haciendo Git Pull...")
            ssh_exec(ssh, f"cd {CLONE_DIR} && git reset --hard && git pull origin {BRANCH}")

        # 3. Subir .ENV
        print("\n--- SINCRONIZANDO VARIABLES DE ENTORNO (.ENV) ---")
        if os.path.exists(local_env_path):
            sftp = ssh.open_sftp()
            sftp.put(local_env_path, remote_env_path)
            sftp.close()
            print("✓ Archivo .env transferido exitosamente.")
        else:
            print(f"⚠️  ERROR: No se encuentra {local_env_path}")

        # 4. Entorno Virtual Python
        print("\n--- INSTALANDO DEPENDENCIAS PYTHON ---")
        ssh_exec(ssh, f"python3 -m venv {CLONE_DIR}/venv")
        # Forzar instalacion de dependencias clave de UI
        ssh_exec(ssh, f"{CLONE_DIR}/venv/bin/pip install streamlit pandas supabase python-dotenv webdriver-manager beautifulsoup4 google-api-python-client google-auth-httplib2 google-auth-oauthlib")

        # 5. Configurar Systemd Service
        print("\n--- CONFIGURANDO SYSTEMD (AUTORUN) ---")
        ssh_exec(ssh, f"cat << 'EOF' > /etc/systemd/system/{SERVICE_NAME}\n{SYSTEMD_FILE}\nEOF")
        ssh_exec(ssh, "systemctl daemon-reload")
        ssh_exec(ssh, f"systemctl enable {SERVICE_NAME}")
        ssh_exec(ssh, f"systemctl restart {SERVICE_NAME}")

        # 6. Configurar Nginx Reverse Proxy
        print("\n--- CONFIGURANDO NGINX (REVERSE PROXY) ---")
        nginx_conf = f"/etc/nginx/sites-available/crm_neoauto"
        ssh_exec(ssh, f"cat << 'EOF' > {nginx_conf}\n{NGINX_FILE}\nEOF")
        
        # Crear symlink si no existe
        ssh_exec(ssh, f"ln -s {nginx_conf} /etc/nginx/sites-enabled/crm_neoauto 2>/dev/null || true")
        # Borrar default por si estorba
        ssh_exec(ssh, "rm -f /etc/nginx/sites-enabled/default")
        
        # Test y reload Nginx
        if ssh_exec(ssh, "nginx -t"):
            ssh_exec(ssh, "systemctl reload nginx")
            print(f"✓ Nginx enrutando tráfico a {DOMAIN_NAME}")
        else:
            print("⚠️ ERROR NGINX: Hubo un problema con la configuracion.")

        # 7. Ejecutar Certbot para Certificado SSL / HTTPS
        print("\n--- EJECUTANDO CERTBOT (HTTPS / SSL) ---")
        ssh_exec(ssh, f"certbot --nginx -d {DOMAIN_NAME} --non-interactive --agree-tos -m contacto@geeksoft.pe --redirect")
        print("\n" + "="*50)
        print("🚀 DESPLIEGUE COMPLETADO")
        print(f"🔗 Tu CRM web ya debería estar vivo en: https://{DOMAIN_NAME}")
        print("="*50)

    except Exception as e:
        print(f"Error critico: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy_to_vps()
