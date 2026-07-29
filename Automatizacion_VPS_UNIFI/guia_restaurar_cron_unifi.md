# Guía: Restauración del Cron Persistente en UniFi Gateway

Debido a que los reinicios o cortes de energía en el Gateway UniFi borran las tareas programadas (crontab) que no están aseguradas, es necesario configurar un servicio de **Systemd** que auto-inyecte los crons de Wake-on-LAN (WOL) en cada arranque.

Esta guía documenta el proceso interactivo seguro para hacerlo desde una máquina Windows.

---

## 1. Conexión SSH Interactiva
Desde PowerShell o CMD en Windows, inicia sesión en el Gateway UniFi:

```powershell
ssh root@192.168.0.1
```
*(Ingresa tu contraseña cuando el sistema la solicite)*

> **⚠️ IMPORTANTE:** Nunca intentes enviar comandos que contengan `>>` o `2>&1` en una sola línea remota directamente desde PowerShell (ej. `ssh root@... "comando >> log"`), porque PowerShell interpretará esos símbolos como operadores locales en tu PC y lanzará un error `StreamAlreadyRedirected`. Siempre entra primero de forma interactiva.

---

## 2. Inyección del Script de Systemd
Una vez dentro del prompt del UniFi (`root@Unifi:~#`), copia **todo este bloque completo** y pégalo de una sola vez en la consola:

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

---

## 3. Verificación
El último comando ejecutado en el bloque anterior (`crontab -l`) debe imprimir en pantalla las tareas programadas activas. 

Debes confirmar que aparecen las siguientes dos líneas, las cuales aseguran que el script de WOL se ejecutará todos los días a las 6:30 PM y los lunes a la medianoche:

```bash
30 18 * * * /data/bridge_wol.sh >> /data/wol.log 2>&1
0 0 * * 1 /data/bridge_wol.sh >> /data/wol.log 2>&1
```

¡Listo! Con esto, el Gateway UniFi volverá a encender automáticamente la ThinkPad incluso después de futuros cortes de luz.
