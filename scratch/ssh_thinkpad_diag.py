import paramiko

host = "192.168.0.150"
user = "richgutz"
key_file = r"C:\Users\rguti\.ssh\id_thinkpad_antigravity"

try:
    key = paramiko.Ed25519Key.from_private_key_file(key_file)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {user}@{host}...")
    client.connect(host, username=user, pkey=key, timeout=5)
    print("SSH Connected successfully!")
    
    cmd = "who; echo ---PS---; ps aux | grep -E 'x11vnc|antigravity|wayland|Xorg' | grep -v grep"
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print("STDOUT:\n", out)
    if err:
        print("STDERR:\n", err)
    client.close()
except Exception as e:
    print("SSH Error:", e)
