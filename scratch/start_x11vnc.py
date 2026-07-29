import paramiko
import time

host = "192.168.0.150"
user = "richgutz"
key_file = r"C:\Users\rguti\.ssh\id_thinkpad_antigravity"

key = paramiko.Ed25519Key.from_private_key_file(key_file)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, pkey=key, timeout=5)

print("1. Killing any stale x11vnc processes...")
client.exec_command("killall -9 x11vnc")
time.sleep(1)

print("2. Starting x11vnc server on display :0 (port 5900)...")
# x11vnc command for LightDM / Xorg on Linux Mint
x11vnc_cmd = "nohup x11vnc -display :0 -auth /var/run/lightdm/root/:0 -forever -shared -rfbport 5900 -repeat -noxdamage > /tmp/x11vnc_out.log 2>&1 &"
client.exec_command(x11vnc_cmd)
time.sleep(2)

print("3. Checking x11vnc output log and process...")
stdin, stdout, stderr = client.exec_command("cat /tmp/x11vnc_out.log; ps aux | grep x11vnc | grep -v grep")
print(stdout.read().decode())

client.close()
