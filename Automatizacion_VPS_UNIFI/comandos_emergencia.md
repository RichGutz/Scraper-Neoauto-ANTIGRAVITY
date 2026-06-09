# 🚨 Comandos de Emergencia - ThinkPad T430s
Guía rápida para encender y apagar la ThinkPad de forma remota y manual desde la terminal de **PowerShell** de tu computadora de desarrollo Windows en caso de emergencias o pruebas.

---

## 🚀 1. Encender la ThinkPad (Wake-on-LAN Nativo)
No necesitas instalar programas de terceros. Este script de PowerShell utiliza las librerías nativas de .NET para enviar el Magic Packet directamente a la red física local:

### Comando de un solo clic (Copia y pega en tu PowerShell):
```powershell
$mac = "3c:97:0e:7a:97:78"; $macBytes = $mac -split ":" | ForEach-Object { [Convert]::ToByte($_, 16) }; $packet = [byte[]](@() + (,0xFF * 6) + ($macBytes * 16)); $client = New-Object System.Net.Sockets.UdpClient; $client.Connect("192.168.0.255", 9); $client.Send($packet, $packet.Length) | Out-Null; $client.Close(); Write-Host "🚀 ¡Magic Packet enviado con éxito desde esta PC a la ThinkPad!" -ForegroundColor Green
```

---

## 🛑 2. Apagar la ThinkPad (SSH Remoto)
Puedes ordenar el apagado seguro inmediato a través de SSH. Como ya configuramos el permiso especial de `shutdown` sin contraseña, este comando se ejecutará al instante.

### Comando (Copia y pega en tu PowerShell):
```powershell
ssh richgutz@192.168.0.150 "sudo /sbin/shutdown -h now"
```
*(Nota: Si no tienes las llaves SSH cargadas en esta PC, te pedirá ingresar tu contraseña de usuario de la ThinkPad y luego se apagará de inmediato).*

---

## 🔍 3. Comprobar si la ThinkPad está encendida (Ping Continuo)
Si quieres verificar en tiempo real cuándo la ThinkPad termina de encenderse o cuándo se apaga por completo, corre este comando:

```powershell
ping -t 192.168.0.150
```
```
* Presiona `Ctrl + C` para detenerlo.

---

## 🛠️ 4. Persistencia de Cron de WOL en el Gateway UniFi
Para evitar que el cron se borre en cada reinicio del Gateway UniFi, configuramos un servicio de Systemd persistente.

### A. Si ya estás conectado por SSH dentro del Gateway:
Ejecuta esto para crear el servicio, habilitarlo y verificarlo:

```bash
# 1. Crear el servicio de systemd que auto-inyecta el cron en cada arranque
cat << 'EOF' > /etc/systemd/system/restore-wol-cron.service
[Unit]
Description=Restaurar Cron de WOL en Inicio
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c '(crontab -l 2>/dev/null | grep -v "bridge_wol.sh"; echo "30 18 * * * /data/bridge_wol.sh >> /data/wol.log 2>&1"; echo "0 0 * * 1 /data/bridge_wol.sh >> /data/wol.log 2>&1") | crontab -'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# 2. Registrar y arrancar el servicio
systemctl daemon-reload
systemctl enable restore-wol-cron.service
systemctl start restore-wol-cron.service

# 3. Verificar que el cron se inyectó con éxito
crontab -l
```

### B. Si estás en Windows (PowerShell / CMD):
⚠️ **IMPORTANTE: NO INTENTES ENVIAR ESTO EN UN SOLO COMANDO REMOTO DESDE POWERSHELL.** 
PowerShell de Windows intercepta los símbolos `>>` y `2>&1` creyendo que son comandos locales y arrojará un error de "ParserError" (StreamAlreadyRedirected). 

Para evitar problemas de formato y saltos de línea (`\r\n`), usa el **Método Interactivo**:

**1. Entra al UniFi abriendo la sesión interactiva en PowerShell o CMD:**
```powershell
ssh root@192.168.0.1
```
*(Ingresa tu contraseña cuando te la pida)*

**2. Una vez que veas el mensaje de bienvenida del UniFi, pega TODO este bloque de una sola vez:**
```bash
cat << 'EOF' > /etc/systemd/system/restore-wol-cron.service
[Unit]
Description=Restaurar Cron de WOL en Inicio
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c '(crontab -l 2>/dev/null | grep -v "bridge_wol.sh"; echo "30 18 * * * /data/bridge_wol.sh >> /data/wol.log 2>&1"; echo "0 0 * * 1 /data/bridge_wol.sh >> /data/wol.log 2>&1") | crontab -'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable restore-wol-cron.service
systemctl start restore-wol-cron.service
crontab -l
```
*(El último comando `crontab -l` te mostrará en pantalla que todo quedó registrado correctamente).*

