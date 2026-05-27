import paramiko

VPS_HOST = "91.108.125.253"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "doHtFib1poV+f0F7"

# El comando que enviará el Magic Packet desde Hostinger hacia la IP pública de Richard
cmd = "python3 -c \"import socket; socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(bytes.fromhex('ff'*6 + '3c970e7a9778'*16), ('190.237.10.171', 9))\""

print(f"Conectando a Hostinger ({VPS_HOST}) para disparar el Magic Packet...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("SUCCESS: Conectado por SSH a Hostinger!")
    print(f"Ejecutando comando de red en Hostinger...")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    err = stderr.read().decode()
    if err:
        print(f"WARNING: Salida de error: {err}")
    print("SUCCESS: Magic Packet enviado desde Hostinger hacia 190.237.10.171:9!")
except Exception as e:
    print(f"ERROR: Error de conexion/ejecucion: {e}")
finally:
    client.close()
