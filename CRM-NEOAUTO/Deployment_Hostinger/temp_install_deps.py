import paramiko
import os

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

def install_deps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("Instalando markdown2 en el servidor...")
        stdin, stdout, stderr = client.exec_command("pip install markdown2")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("Reiniciando servicio crm_neoauto...")
        client.exec_command("systemctl restart crm_neoauto")
        print("Hecho.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    install_deps()
