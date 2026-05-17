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
* Presiona `Ctrl + C` para detenerlo.
