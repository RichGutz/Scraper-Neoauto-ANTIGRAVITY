import paramiko
import sys

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"
VENV_PIP = "/opt/crm_neoauto/venv/bin/pip"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASS, timeout=10)

# Instalar reportlab si no está
print("Instalando reportlab...")
stdin, stdout, stderr = client.exec_command(f"{VENV_PIP} install reportlab", timeout=120)
stdout.channel.recv_exit_status()  # Esperar a que termine

# Verificar instalación
stdin2, stdout2, _ = client.exec_command(f"{VENV_PIP} show reportlab")
result = stdout2.read().decode("ascii", errors="replace").strip()
print("Verificacion:", result[:200] if result else "NO ENCONTRADO")

# Reiniciar servicio
client.exec_command("systemctl restart crm_neoauto")
print("Servicio reiniciado.")

client.close()
