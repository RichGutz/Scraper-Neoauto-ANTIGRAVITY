import paramiko

host = "91.108.125.253"
port = 22
user = "root"
passwd = "Thiagutz061121@"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=passwd, timeout=10)

commands = {
    "CPU Info": "lscpu | grep -E 'CPU|Model name|Thread|Core'",
    "Uptime and Load": "uptime",
    "RAM Usage": "free -h",
    "Disk Usage": "df -h /",
    "Top Memory Processes": "ps aux --sort=-%mem | head -n 10",
    "Top CPU Processes": "ps aux --sort=-%cpu | head -n 10"
}

print("="*60)
print(" AUDITORIA DE RECURSOS VPS HOSTINGER (91.108.125.253)")
print("="*60)

for title, cmd in commands.items():
    print(f"\n--- {title} ---")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    print(out)

client.close()
