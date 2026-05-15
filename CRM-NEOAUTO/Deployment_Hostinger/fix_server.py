import paramiko
import sys

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASS, timeout=10)

def show(label, ch):
    data = ch.read()
    sys.stdout.buffer.write(("=== " + label + " ===\n").encode())
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()

# Ver líneas 718-724 del archivo en el servidor
stdin, stdout, _ = client.exec_command("sed -n '718,724p' /opt/crm_neoauto/CRM-NEOAUTO/frontend_app.py")
show("LINEAS 718-724 EN SERVIDOR", stdout)

# Borrar archivos .pyc cacheados
stdin2, stdout2, _ = client.exec_command("find /opt/crm_neoauto -name '*.pyc' -delete && echo 'pyc borrados'")
print(stdout2.read().decode("ascii", errors="replace"))

# Forzar git reset hard
stdin3, stdout3, _ = client.exec_command("cd /opt/crm_neoauto && git fetch --all && git reset --hard origin/master && echo RESET_OK")
stdout3.channel.recv_exit_status()
show("GIT RESET", stdout3)

# Verificar de nuevo
stdin4, stdout4, _ = client.exec_command("sed -n '718,724p' /opt/crm_neoauto/CRM-NEOAUTO/frontend_app.py")
show("LINEAS 718-724 DESPUES DE RESET", stdout4)

# Reiniciar
client.exec_command("systemctl restart crm_neoauto")
print("Servicio reiniciado.")
client.close()
