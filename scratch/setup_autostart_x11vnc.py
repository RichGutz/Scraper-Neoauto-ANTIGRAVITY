import paramiko

host = "192.168.0.150"
user = "richgutz"
key_file = r"C:\Users\rguti\.ssh\id_thinkpad_antigravity"

key = paramiko.Ed25519Key.from_private_key_file(key_file)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, pkey=key, timeout=5)

autostart_content = """[Desktop Entry]
Type=Application
Name=x11vnc Server AutoStart
Exec=x11vnc -display :0 -auth /var/run/lightdm/root/:0 -forever -shared -rfbport 5900 -repeat -noxdamage
StartupNotify=false
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""

cmd = f"""
mkdir -p ~/.config/autostart
cat << 'EOF' > ~/.config/autostart/x11vnc.desktop
{autostart_content}EOF
chmod +x ~/.config/autostart/x11vnc.desktop
"""

stdin, stdout, stderr = client.exec_command(cmd)
print("Autostart creation status:")
print(stdout.read().decode())
print(stderr.read().decode())

# Check if file exists
stdin, stdout, stderr = client.exec_command("cat ~/.config/autostart/x11vnc.desktop")
print("File content on ThinkPad:")
print(stdout.read().decode())

client.close()
