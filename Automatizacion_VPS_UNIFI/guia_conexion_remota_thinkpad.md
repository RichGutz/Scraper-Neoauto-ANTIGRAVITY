# 🖥️ Guía: Conexión Remota a la ThinkPad T430s (Producción)

Esta guía documenta el procedimiento oficial y los parámetros técnicos para conectarte desde tu máquina de desarrollo (Windows 10) a la laptop de producción **ThinkPad T430s** (Linux), tanto en modo **Escritorio Gráfico** como por **Terminal SSH**.

---

## 📌 Parámetros de Red y Credenciales

- **Red Local (UniFi)**: Segmento `192.168.0.x`
- **Dirección IP ThinkPad**: `192.168.0.150`
- **Dirección MAC (para WOL)**: `3C:97:0E:7A:97:78`
- **Usuario Linux**: `richgutz`

---

## 1. 🖼️ Conexión por Escritorio Remoto Gráfico RDP (Nueva Sesión)

Para ver el escritorio visual de Linux con sus ventanas, iconos y navegador (cuando la ThinkPad no tiene sesión gráfica iniciada localmente):

> **⚠️ NOTA TÉCNICA IMPORTANTE:**
> La ThinkPad utiliza el protocolo **RDP (xrdp)** escuchando en el **Puerto 3389**.
> **Limitación de sesión:** Si `richgutz` ya tiene la sesión abierta localmente en la laptop física (pantalla encendida/ejecutando un proceso), RDP rechazará el inicio de sesión. Para ver esa sesión activa, usa la **Sección 3 (VNC con x11vnc)**.

### Pasos en Windows:
1. En tu teclado presiona la combinación: **`Win + R`** (Abre la ventana *Ejecutar*).
2. Escribe **`mstsc`** y presiona **Enter** *(Abre Conexión a Escritorio Remoto de Windows)*.
3. En el campo **Equipo**, ingresa:
   ```text
   192.168.0.150
   ```
4. Haz clic en **Conectar**.
5. Ingresa el usuario `richgutz` y tu contraseña cuando te sea solicitada.

---

## 2. 💻 Conexión por Terminal SSH (Línea de Comandos)

Si solo necesitas enviar comandos de terminal o gestionar procesos:

### Desde PowerShell / CMD:
```powershell
ssh richgutz@192.168.0.150
```

### Desde PuTTY:
- **Host Name (or IP address)**: `192.168.0.150`
- **Port**: `22`
- **Connection type**: `SSH`

---

## 3. 👁️ Conexión por VNC (`x11vnc`) - Ver Pantalla Física / Sesión Activa (Antigravity IDE)

Esta es la **opción oficial recomendada** para conectarte cuando la ThinkPad ya tiene la sesión local abierta (ejecutando Antigravity IDE o procesos diarios).

> **✅ ESTADO PROBADO Y VERIFICADO:**
> - **Entorno**: Linux Mint 22.1 / LightDM (Display `:0`).
> - **Puerto VNC**: `5900` (`192.168.0.150:5900`).
> - **Autostart**: Configurado en `~/.config/autostart/x11vnc.desktop` para arrancar automáticamente al iniciar Linux.

### A. Conexión rápida desde Windows:
1. Abre tu visor VNC favorito (**VNC Viewer**, **RealVNC**, **TightVNC**).
2. Ingresa el servidor:
   ```text
   192.168.0.150:5900
   ```
3. ¡Conectarás directamente en modo espejo a la sesión activa donde está corriendo **Antigravity IDE**!

### B. Comando de inicio manual (Si se detiene la sesión):
```bash
x11vnc -display :0 -auth /var/run/lightdm/root/:0 -forever -shared -rfbport 5900 -repeat -noxdamage &
```

---

## 4. 🔑 Llaves SSH Autorizadas (Conexión Directa sin Contraseña)

Se ha configurado la llave SSH de la máquina de desarrollo (`rguti@DESKTOP-JPPDHHP`) en la ThinkPad (`~/.ssh/authorized_keys`).

### Conexión desde PowerShell:
```powershell
ssh -i C:\Users\rguti\.ssh\id_thinkpad_antigravity richgutz@192.168.0.150
```

---

## 4. ⚡ Encendido Remoto (Wake-on-LAN)

Si la ThinkPad está apagada pero conectada a la corriente y al cable Ethernet:

### Opción A (Desde PowerShell en Windows):
```powershell
python -c "import socket; data = bytes.fromhex('FF'*6 + '3c970e7a9778'*16); s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1); s.sendto(data, ('192.168.0.255', 9)); s.sendto(data, ('255.255.255.255', 9)); print('Magic Packet enviado')"
```

### Opción B (Desde el Gateway UniFi 192.168.0.1):
```bash
ssh root@192.168.0.1 "/data/bridge_wol.sh"
```

