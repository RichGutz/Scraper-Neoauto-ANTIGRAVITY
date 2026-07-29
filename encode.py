import base64

payload = """[Unit]
Description=Restaurar Cron de WOL en Inicio
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c '(crontab -l 2>/dev/null | grep -v "bridge_wol.sh"; echo "30 18 * * * /data/bridge_wol.sh >> /data/wol.log 2>&1"; echo "0 0 * * 1 /data/bridge_wol.sh >> /data/wol.log 2>&1") | crontab -'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""

# Usar \n explícitamente para que Linux lo entienda perfecto
encoded = base64.b64encode(payload.replace("\r\n", "\n").encode()).decode()
print("BASE64_OUTPUT_START")
print(encoded)
print("BASE64_OUTPUT_END")
