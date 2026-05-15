import paramiko

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

def run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode("utf-8", errors="ignore").strip()
    err = stderr.read().decode("utf-8", errors="ignore").strip()
    return out, err

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASS, timeout=10)

print("=== 1. Buscando entornos virtuales ===")
out, _ = run(client, "find /opt/crm_neoauto -name 'pip' 2>/dev/null")
print(out)

print("\n=== 2. Servicio systemd ===")
out, _ = run(client, "cat /etc/systemd/system/crm_neoauto.service")
print(out)

print("\n=== 3. Paquetes instalados en venv ===")
out, _ = run(client, "find /opt/crm_neoauto -name 'pip3' -o -name 'pip' | head -3 | xargs -I{} {} list 2>/dev/null | grep -E 'report|markdown|weasY|pandas|supabase|stream'")
print(out)

client.close()
