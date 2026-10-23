# Estado del Sistema - Scraper NeoAuto & ThinkPad Appliance

- **Fecha de Certificación:** 2026-10-23
- **Hardware Host:** Lenovo ThinkPad T430s (Appliance Headless en LAN UniFi `192.168.0.150`)
- **Almacenamiento del Scraper:** Disco Mecánico HGST 500 GB en UltraBay Caddy (`/mnt/caddy_storage/Scraper.Neoauto` / `Z:\Scraper.Neoauto`)
- **Blindaje del Sistema:** Nuevo SSD YS 240 GB (`/` / `Y:\`) blindado al 100% con CERO escrituras de scraping.
- **Repositorio Git Maestro:** [https://github.com/RichGutz/Scraper-Neoauto-ANTIGRAVITY.git](https://github.com/RichGutz/Scraper-Neoauto-ANTIGRAVITY.git)
- **Estado General:** **OPERATIVO EN PRODUCCIÓN AL 100%**

---

## 🎯 1. Resumen de Hitos y Tareas Completadas

En esta sesión se resolvió de forma integral la recuperación del entorno, la extracción forense de datos perdidos, el blindaje de hardware y la automatización programada:

```mermaid
flowchart TD
    subgraph HW ["1. Hardening de Hardware & Red"]
        BIOS["BIOS: Integrated Graphics<br/>(Cero Nouveau Faults, menor calor/watts)"]
        WOL["Ethernet enp0s25: Wake-on: g<br/>(MagicPacket activo para UniFi)"]
    end

    subgraph FORENSIC ["2. Rescate Forense SSD Kingston (574 TBW)"]
        RO["Montaje Linux: -o ro,noload<br/>(Bypass de sectores lentos y journal)"]
        SYNC["Volcado >4.2 GB a Caddy HDD<br/>• main.py canónico<br/>• Dataset Autos 3.04 GB<br/>• Scripts 24/7"]
    end

    subgraph AUTOMATION ["3. Automatización & Guardián Inteligente"]
        CRON["Crontab ThinkPad:<br/>• Diario: 18:32 PM<br/>• Lunes: 00:02 AM"]
        GUARD["Guardián smart_conditional_shutdown.sh<br/>🛡️ Si Open JEV u Ollama están activos: NO APAGAR"]
    end

    subgraph PROD ["4. Validación en Vivo"]
        SCRAPE["Scraper Diario ejecutado en Caddy:<br/>✅ 134 URLs nuevas en Supabase<br/>✅ 6 Workers Playwright paralelos activos"]
    end

    HW --> AUTOMATION
    FORENSIC --> PROD
    AUTOMATION --> PROD
```

---

## 🛠️ 2. Detalle de Arquitectura y Configuración Aplicada

### A. Diagnóstico de Pantalla & Optimización BIOS
- **Causa Raíz del mensaje en pantalla:** El driver open-source `nouveau` de la tarjeta Nvidia NVS 5400M emitía advertencias benignas de MMIO en `tty1` sobre el prompt de login.
- **Solución Definitiva:** Se configuró en BIOS **Graphics Device ➔ Integrated Graphics**. El booteo quedó 100% limpio en consola, se apagó el chip Nvidia y se redujo el consumo eléctrico a ~12W para operación 24/7.

### B. Rescate Forense Exitoso del SSD Kingston Dañado (SA400S37240G)
El SSD Kingston agotó sus ciclos de vida útil por acumular **574 TBW** frente a 80 TBW de diseño (717.5% de desgaste).
- **Procedimiento:** Conectado por USB a la ThinkPad y montado con directiva forense:
  ```bash
  sudo mount -o ro,noload /dev/sdc3 /media/rescate_kingston
  ```
- **Archivos Rescatados e Integrados al Repositorio:**
  1. `main.py`: Recuperada la función `build_canonical_model_mapping()` para estandarizar modelos (ej. `"X-Trail"` vs `"X Trail"`).
  2. `generador_reporte_beta.py` y `generador_reporte_mejorado.py`: Adaptados al mapeo canónico.
  3. `vps_uploader.py`: Rescatado script de sincronización con VPS.
  4. `run_scraper_sequence_diario.sh` y `run_scraper_semanal.sh`: Adaptados a la ruta del Caddy y al Guardián de Energía.
  5. `Autos.Richard.Gutierrez/`: Sincronizado el dataset completo de **3.04 GB** con imágenes descargadas y reportes históricos hasta el 17 de Octubre de 2026.
  6. Respaldada la carpeta `.ssh/` del usuario anterior.

### C. Certificación de Backups en Caddy & Estrategia 3-2-1
- Se verificó que en `Z:\repos_backup\home_rguti` existen **5 snapshots consolidados de Restic** (190 GB a 225 GB cada uno, deduplicados por bloques CDC).
- Se redactó e indexó la **Nota Técnica `#332 (BCK-09)`** formalizando la arquitectura **3-2-1 Enterprise**:
  - **Copia 1:** Laptop Windows 11 en vivo (`C:\Users\rguti`).
  - **Copia 2:** Caddy HDD en ThinkPad LAN (`Z:\repos_backup\home_rguti`).
  - **Copia 3:** Bóveda USB desacoplada en ThinkPad (`/mnt/usb_vault`) con reposo a 0 RPM (`hdd_off`).

---

## ⏰ 3. Cronología y Horarios de Automatización UniFi ➔ ThinkPad

| Evento | Origen | Destino | Hora Programada | Acción Realizada |
| :--- | :---: | :---: | :---: | :--- |
| **WOL Diario** | Gateway UniFi (`192.168.0.1`) | ThinkPad (`192.168.0.150`) | **18:30 (6:30 PM)** | Inyecta Magic Packet UDP a MAC `3c:97:0e:7a:97:78`. |
| **Scraper Diario** | Crontab ThinkPad | Entorno Caddy HDD | **18:32 (6:32 PM)** | Ejecuta `run_scraper_sequence_diario.sh` (espera 2 min tras WOL). |
| **WOL Semanal** | Gateway UniFi (`192.168.0.1`) | ThinkPad (`192.168.0.150`) | **00:00 (12:00 AM Lunes)** | Inyecta Magic Packet para encendido semanal masivo. |
| **Scraper Semanal** | Crontab ThinkPad | Entorno Caddy HDD | **00:02 (12:02 AM Lunes)** | Ejecuta `run_scraper_semanal.sh` (solo se dispara los lunes). |

### Crontab Activo en la ThinkPad (`richgutz`):
```cron
# === WOL Automation: UniFi despierta la ThinkPad ===
# Scraping Diario 18:32 PM (UniFi manda WOL a las 18:30)
32 18 * * * /mnt/caddy_storage/Scraper.Neoauto/run_scraper_sequence_diario.sh >> /mnt/caddy_storage/Scraper.Neoauto/cron_diario.log 2>&1

# Scraping Semanal Lunes 00:02 AM (UniFi manda WOL a las 00:00)
02 00 * * 1 /mnt/caddy_storage/Scraper.Neoauto/run_scraper_semanal.sh >> /mnt/caddy_storage/Scraper.Neoauto/cron_semanal.log 2>&1
```

---

## 🛡️ 4. Guardián de Apagado Inteligente (`smart_conditional_shutdown.sh`)

Ubicado en `/usr/local/bin/smart_conditional_shutdown.sh`, se invoca automáticamente al finalizar cada ejecución de scraping para evitar que el equipo se apague si está sirviendo como Appliance de IA:

```text
[SMART-POWER] Evaluando estado del appliance antes de apagar...
├── ¿Open JEV (:8888) activo?      ➔ SI: ABORTA APAGADO (Protege gobernanza agéntica)
├── ¿Ollama (:11434) activo?       ➔ SI: ABORTA APAGADO (Protege clúster de inferencia local)
├── ¿Sesiones SSH LAN activas?     ➔ SI: ABORTA APAGADO (Protege sesiones de trabajo del operador)
└── ¿Samba (Y:\ o Z:\) en uso?     ➔ SI: ABORTA APAGADO (Protege transferencias y montajes)
```

*Solo si todos los servicios anteriores están detenidos y la red está completamente desierta, el equipo procede al apagado físico.*

---

## 🚀 5. Validación en Vivo Certificada (Producción Real)

- **Paso 1 (Extracción URLs):** Conexión HTTP en vivo a NeoAuto. Escaneadas 11 páginas de usados y 6 de seminuevos. Guardadas **134 URLs nuevas** del día en Supabase (`urls_autos_diarios`).
- **Paso 2 (Extracción Detallada):** 6 Workers paralelos de Playwright Chromium levantados en background en la ThinkPad, navegando con scroll y simulación humana.
- **Evidencia en Disco:** Archivos `.txt` generados exitosamente en `Z:\Scraper.Neoauto\extractores\results_txt\`.
- **Integridad Git:** Código compilado con `py_compile` (0 errores) y publicado en GitHub (commits `87e0b44` y `c1560ac`).

El sistema queda 100% blindado, desatendido y protegido contra desgaste de hardware.
