#!/usr/bin/env python3
import os
import sys
import paramiko

# VPS Connection Details
VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "Thiagutz061121@"
REMOTE_DIR = "/opt/crm_neoauto/reportes"

def sftp_mkdir_recursive(sftp, remote_directory):
    """Recursively creates directory path on remote server if it does not exist."""
    if remote_directory == "/" or remote_directory == "":
        return
    try:
        sftp.stat(remote_directory)
    except FileNotFoundError:
        parent = os.path.dirname(remote_directory)
        sftp_mkdir_recursive(sftp, parent)
        sftp.mkdir(remote_directory)
        print(f"Directorio remoto creado: {remote_directory}")

def upload_dir_recursive(sftp, local_dir, remote_dir):
    """Uploads a local directory tree recursively to the remote directory."""
    sftp_mkdir_recursive(sftp, remote_dir)
    
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = os.path.join(remote_dir, item).replace('\\', '/')
        
        if os.path.isdir(local_path):
            upload_dir_recursive(sftp, local_path, remote_path)
        else:
            try:
                # Get local size and remote size (if exists)
                local_size = os.path.getsize(local_path)
                try:
                    remote_stat = sftp.stat(remote_path)
                    remote_size = remote_stat.st_size
                except FileNotFoundError:
                    remote_size = -1
                
                # Only upload if size differs or file doesn't exist
                if local_size != remote_size:
                    sftp.put(local_path, remote_path)
                    print(f"Subido: {local_path} -> {remote_path}")
            except Exception as e:
                print(f"Error subiendo {local_path}: {e}")

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("="*60)
    print("INICIANDO SUBIDA DE REPORTES AL VPS DE HOSTINGER")
    print("="*60)
    
    # Paths to local folders
    local_outputs = os.path.join(project_dir, "outputs")
    local_models = os.path.join(project_dir, "model_pages")
    
    if not os.path.exists(local_outputs):
        print(f"ERROR: La carpeta local '{local_outputs}' no existe.")
        sys.exit(1)
        
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Conectando a {VPS_HOST}:{VPS_PORT}...")
        client.connect(
            hostname=VPS_HOST, 
            port=VPS_PORT, 
            username=VPS_USER, 
            password=VPS_PASS, 
            timeout=15
        )
        print("[OK] Conexión SSH establecida.")
        
        sftp = client.open_sftp()
        print("Iniciando sesión SFTP...")
        
        # Upload outputs folder
        print("\n--> Subiendo carpeta 'outputs'...")
        upload_dir_recursive(sftp, local_outputs, f"{REMOTE_DIR}/outputs")
        
        # Upload model_pages folder if exists
        if os.path.exists(local_models):
            print("\n--> Subiendo carpeta 'model_pages'...")
            upload_dir_recursive(sftp, local_models, f"{REMOTE_DIR}/model_pages")
        else:
            print("\nADVERTENCIA: La carpeta local 'model_pages' no existe, omitiendo.")
            
        sftp.close()
        print("\n[OK] Sincronización de archivos finalizada con éxito.")
        
    except Exception as e:
        print(f"\n[ERROR] Ocurrió una falla durante la sincronización: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()
