"""
FASE 3 - DEPLOY COMPLETO CRM_NEOAUTO AL VPS HOSTINGER
======================================================
Script robusto derivado de los estándares de Inandes.
"""
import paramiko
import os
import sys
from dotenv import load_dotenv

# ========================================
#  CONFIGURA ESTO ANTES DE EJECUTAR
# ========================================
VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

# Variables Repositorio (Seguro)
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

# ========================================

def ssh_run(client, cmd, desc=""):
    if desc:
        print(f"\n  [{desc}]")
    print(f"  $ {cmd[:80]}{'...' if len(cmd)>80 else ''}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        print(f"  >> {out[:500]}")
    if err and "warning" not in err.lower():
        print(f"  !! {err[:500]}")
    return out, err

def upload_env(client):
    if not os.path.exists(local_env_path):
        print(f"\n  ADVERTENCIA: No se encontro .env en {local_env_path}")
        return False
    sftp = client.open_sftp()
    remote_env = f"{APP_DIR}/.env"
    print(f"\n  Subiendo .env via SFTP -> {remote_env}")
    sftp.put(local_env_path, remote_env)
    sftp.close()
    print("  .env subido OK")
    return True

def upload_nginx_config(client):
    nginx_conf = f"""server {{
    listen 80;
    server_name {SUBDOMAIN};

    location / {{
        proxy_pass http://127.0.0.1:{APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }}
}}
"""
    sftp = client.open_sftp()
    remote_path = f"/etc/nginx/sites-available/{SERVICE}"
    with sftp.open(remote_path, "w") as f:
        f.write(nginx_conf)
    sftp.close()
    print(f"  Config Nginx subida -> {remote_path}")

def upload_systemd_service(client):
    service_content = f"""[Unit]
Description=CRM Neoauto Streamlit App
After=network.target

[Service]
User=root
WorkingDirectory={APP_DIR}
Environment="PATH={VENV_DIR}/bin"
ExecStart={VENV_DIR}/bin/streamlit run CRM-NEOAUTO/frontend_app.py --server.port={APP_PORT} --server.address=127.0.0.1 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    sftp = client.open_sftp()
    remote_path = f"/etc/systemd/system/{SERVICE}.service"
    with sftp.open(remote_path, "w") as f:
        f.write(service_content)
    sftp.close()
    print(f"  Service systemd subido -> {remote_path}")

def deploy():
    print(f"\n{'='*55}")
    print(f"  DEPLOY MODULAR CRM_NEOAUTO -> {SUBDOMAIN}")
    print(f"{'='*55}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"\n[0/7] Conectando a {VPS_HOST}...")
        client.connect(hostname=VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
        print("  Conexion SSH OK")

        # 1. Dependencias de sistema (Silencioso para no atrapar shells)
        ssh_run(client,
            "export DEBIAN_FRONTEND=noninteractive && apt-get update -qq && "
            "apt-get install -y -qq git python3-venv nginx certbot python3-certbot-nginx 2>&1 | tail -5",
            "1/7 Validar dependencias (Bypassed interactive prompt)")

        # 2. Clonar o actualizar repo en sub-rama funcional
        ssh_run(client,
            f"if [ -d '{APP_DIR}/.git' ]; then "
            f"  cd {APP_DIR} && git fetch --all && git reset --hard origin/{BRANCH} && git pull origin {BRANCH}; "
            f"else "
            f"  rm -rf {APP_DIR} && git clone -b {BRANCH} {REPO_URL} {APP_DIR}; "
            f"fi",
            "2/7 Sincronizar rama funcional de Github")

        # 3. Subir .env
        print(f"\n  [3/7 Subir .env]")
        upload_env(client)

        # 4. Crear venv e instalar librerias explicitas de la app Neoauto
        ssh_run(client,
            f"python3 -m venv {VENV_DIR} && "
            f"{VENV_DIR}/bin/pip install --upgrade pip -q && "
            f"{VENV_DIR}/bin/pip install streamlit pandas supabase python-dotenv webdriver-manager beautifulsoup4 google-api-python-client google-auth-httplib2 google-auth-oauthlib -q 2>&1 | tail -5",
            "4/7 Activar entorno e inyectar requirements backend")

        # 5. Crear y activar systemd service
        print(f"\n  [5/7 Configurar systemd service]")
        upload_systemd_service(client)
        ssh_run(client,
            f"systemctl daemon-reload && "
            f"systemctl enable {SERVICE} && "
            f"systemctl restart {SERVICE}",
            "  Activar servicio Neoauto")

        # 6. Configurar Nginx
        print(f"\n  [6/7 Configurar Enrutamiento Nginx Proxy]")
        upload_nginx_config(client)
        ssh_run(client,
            f"ln -sf /etc/nginx/sites-available/{SERVICE} /etc/nginx/sites-enabled/{SERVICE} && "
            f"nginx -t && systemctl reload nginx",
            "  Reiniciar config de Puertos Nginx")

        # 7. Verificacion final
        import time; time.sleep(5)
        ssh_run(client, f"systemctl status {SERVICE} --no-pager | head -15", "7/7 Validacion Post-Arranque")

        print(f"\n{'='*55}")
        print(f"  DEPLOY COMPLETADO EXITOSAMENTE")
        print(f"  URL: https://{SUBDOMAIN}")
        print(f"{'='*55}\n")

    except paramiko.AuthenticationException:
        print("\nERROR: Password incorrecto.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    deploy()
