# Session Log - 2026-01-26: Implementación de Scraper Semanal con Workers Paralelos

**Fecha:** 2026-01-26  
**Hora inicio:** 13:33:28  
**Objetivo:** Ejecutar `run_scraper_semanal.sh` paso a paso e implementar procesamiento paralelo con 8 workers

---

## 📋 Resumen Ejecutivo

Se ejecutó exitosamente el scraper semanal con las siguientes mejoras:
- ✅ Configuración de credenciales de Supabase
- ✅ Extracción de 2,656 URLs de 17 marcas
- ✅ Implementación de sistema de 8 workers paralelos
- ✅ Creación de monitor de progreso en tiempo real
- ⏳ Scraping en progreso (351/2,656 URLs procesadas - 13.2%)

---

## 🔧 Cambios Realizados

### 1. Configuración Inicial

**Problema encontrado:** Faltaba archivo `.env` con credenciales de Supabase

**Solución:**
```bash
cp Core/env .env
```

**Credenciales configuradas:**
- `SUPABASE_URL`: https://llrhimiivjpmxelffxef.supabase.co
- `SUPABASE_KEY`: [configurada desde Core/env]

---

### 2. Step 1: Extracción de URLs (COMPLETADO)

**Script ejecutado:** `extractores/2.SEMANAL.extractor_VCLI_v2.py`

**Resultados:**
- Total URLs extraídas: **2,656**
- Marcas procesadas: **17** (Mercedes-Benz, Volkswagen, BMW, Ford, Kia, Suzuki, Volvo, etc.)
- Tabla destino: `urls_autos` (limpiada antes de insertar)
- Tiempo ejecución: ~10 minutos

**Comando:**
```bash
python3 extractores/2.SEMANAL.extractor_VCLI_v2.py
```

---

### 3. Step 2: Randomización de URLs (COMPLETADO)

**Script ejecutado:** `extractores/3.SEMANAL.randomize_urls_autos.py`

**Resultados:**
- URLs mezcladas aleatoriamente: **2,656**
- Tabla destino: `urls_autos_random`
- Lotes insertados: 6 (500 URLs cada uno, último con 156)
- Tiempo ejecución: ~5 segundos

**Comando:**
```bash
python3 extractores/3.SEMANAL.randomize_urls_autos.py
```

---

### 4. Implementación de Workers Paralelos (NUEVO)

#### 4.1. Archivo creado: `parallel_launcher_semanal.py`

**Ubicación:** `/home/richgutz/Scraper-Neoauto-ANTIGRAVITY/parallel_launcher_semanal.py`

**Características:**
- Lanza **8 workers** en paralelo (antes era 1 solo)
- Basado en `parallel_launcher.py` pero adaptado para Linux
- Script objetivo: `extractores/4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.SUPABASE.PARA.CRON.BETA.py`
- Captura y muestra output de cada worker con prefijo `[Worker-N]`
- Delay de 0.5s entre lanzamientos para evitar race conditions

**Código clave:**
```python
NUM_INSTANCES = 8  # 8 workers en paralelo
SCRIPT_TO_RUN = "extractores/4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.SUPABASE.PARA.CRON.BETA.py"
```

#### 4.2. Modificación: `run_scraper_semanal.sh`

**Cambio en líneas 41-47:**

**ANTES:**
```bash
# --- Ejecución del scraper (una sola instancia) ---
echo ""
echo "--> Ejecutando 1 instancia de SCRAPER.NEOAUTO..."
SCRIPT_TO_RUN="extractores/4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.SUPABASE.PARA.CRON.BETA.py"
$PYTHON_EXEC "$SCRIPT_TO_RUN"
echo "--> Finalizada la instancia del scraper."
```

**DESPUÉS:**
```bash
# --- Ejecución del scraper (8 instancias en paralelo) ---
echo ""
echo "--> Ejecutando 8 instancias paralelas de SCRAPER.NEOAUTO..."
$PYTHON_EXEC "parallel_launcher_semanal.py"
echo "--> Finalizadas todas las instancias del scraper."
```

---

### 5. Instalación de Dependencias

**Problema:** Faltaba módulo `playwright`

**Soluciones aplicadas:**
```bash
# Instalar playwright
pip3 install playwright --break-system-packages

# Instalar navegador Chromium
playwright install chromium
```

**Nota:** Se usó `--break-system-packages` porque el sistema usa entorno externamente gestionado (Debian/Ubuntu)

---

### 6. Monitor de Progreso (NUEVO)

#### Archivo creado: `monitor_workers.py`

**Ubicación:** `/home/richgutz/Scraper-Neoauto-ANTIGRAVITY/monitor_workers.py`

**Características:**
- Monitor en tiempo real del progreso de los 8 workers
- Limpia pantalla cada 5 segundos (evita saturar RAM)
- Muestra:
  - Barra de progreso visual
  - Total URLs procesadas vs pendientes
  - Porcentaje completado
  - Velocidad (URLs/minuto)
  - Tiempo estimado restante (ETA)
- Consulta tabla `urls_autos_random` en Supabase

**Uso:**
```bash
# Ejecutar en terminal independiente (fuera de Antigravity)
cd /home/richgutz/Scraper-Neoauto-ANTIGRAVITY
python3 monitor_workers.py
```

**Salir:** `Ctrl+C`

---

## 📊 Estado Actual del Proceso

### Step 3: Scraping Paralelo (EN PROGRESO)

**Comando ejecutado:**
```bash
python3 parallel_launcher_semanal.py
```

**Estado al momento del log:**
- ⏱️ Tiempo corriendo: ~34 minutos
- ✅ URLs procesadas: **351** de 2,656
- 📈 Progreso: **13.2%**
- 🔄 URLs pendientes: **2,305**
- 👷 Workers activos: **8**
- 💾 Datos guardados en: `extractores/results_txt/semanal_result_*.txt`

**Tiempo estimado total:** 4-6 horas (con 8 workers en paralelo)

---

## 📝 Pasos Pendientes (No ejecutados aún)

### Step 4: Procesamiento de Datos
```bash
python3 extractores/5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py
```
- Convierte archivos `.txt` a `.json` usando DeepSeek AI

### Step 5: Carga a Supabase
```bash
python3 extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py
```
- Sube datos procesados a Supabase

### Step 6: Generación de Reporte
```bash
python3 main.py
```
- Genera reporte HTML y PDF

### Step 7: Subida a Google Drive
```bash
python3 google_drive/drive_uploader.py
```
- Sube reporte a Google Drive y captura enlace

### Step 8: Envío de Correo
```bash
python3 sendgrid_sender.py --subject "Reporte Semanal - 2026-01-26"
```
- Envía correo con reporte adjunto vía SendGrid

---

## 🗂️ Archivos Nuevos Creados

1. **`parallel_launcher_semanal.py`**
   - Sistema de lanzamiento de 8 workers paralelos
   - Adaptado para Linux desde `parallel_launcher.py`

2. **`monitor_workers.py`**
   - Monitor de progreso en tiempo real
   - Interfaz visual con barra de progreso y estadísticas

3. **`.env`** (copiado desde `Core/env`)
   - Credenciales de Supabase para acceso a BD

4. **`session_log_20260126.md`** (este archivo)
   - Documentación completa de la sesión

---

## 🔍 Archivos Modificados

1. **`run_scraper_semanal.sh`**
   - Líneas 41-47: Cambiado de 1 worker a 8 workers paralelos
   - Ahora llama a `parallel_launcher_semanal.py`

---

## 💡 Notas Importantes para el Próximo Claude

### Contexto del Sistema

1. **Directorio de trabajo:** `/home/richgutz/Scraper-Neoauto-ANTIGRAVITY`
2. **Python:** `python3` (sistema no usa venv, usa `--break-system-packages`)
3. **Base de datos:** Supabase
4. **Tablas principales:**
   - `urls_autos`: URLs extraídas originales
   - `urls_autos_random`: URLs mezcladas para procesamiento
   - `urls_autos_diarios`: URLs para scraping diario (vacía en este caso)

### Proceso de Scraping

1. El script `4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.SUPABASE.PARA.CRON.BETA.py`:
   - Primero intenta procesar `urls_autos_diarios` (tabla vacía)
   - Luego procesa `urls_autos_random` (tabla semanal)
   - Usa Playwright con Chromium
   - Marca URLs como `procesado=true` al completar
   - Guarda resultados en `extractores/results_txt/semanal_result_*.txt`

2. **Concurrencia:** Los 8 workers compiten por URLs usando locks en Supabase

### Monitoreo

- **Ver progreso:** Ejecutar `python3 monitor_workers.py` en terminal independiente
- **Ver logs de workers:** El proceso `parallel_launcher_semanal.py` muestra output de todos los workers
- **Verificar proceso:** `ps aux | grep python3` para ver los 8 workers activos

### Próximos Pasos

1. **Esperar** a que termine el scraping (quedan ~5-6 horas)
2. **Verificar** que todas las URLs fueron procesadas:
   ```bash
   python3 monitor_workers.py
   ```
3. **Continuar** con Step 4 (procesamiento txt → json)
4. **Ejecutar** pasos restantes del script semanal

---

## 🚨 Problemas Resueltos

1. ✅ **Falta de `.env`** → Copiado desde `Core/env`
2. ✅ **ModuleNotFoundError: playwright** → Instalado con pip3
3. ✅ **Scraping lento (1 worker)** → Implementado 8 workers paralelos
4. ✅ **Falta de visibilidad del progreso** → Creado `monitor_workers.py`

---

## 📞 Comandos Útiles para Continuar

```bash
# Ver progreso en tiempo real
python3 monitor_workers.py

# Verificar workers activos
ps aux | grep "4.DIARIO.SEMANAL.SCRAPER"

# Ver últimos archivos generados
ls -lt extractores/results_txt/ | head -20

# Contar URLs procesadas
ls extractores/results_txt/semanal_result_*.txt | wc -l

# Verificar proceso principal
ps aux | grep parallel_launcher_semanal
```

---

**Fin del log - Sesión continúa con scraping en progreso**

## 🔄 Incidente y Reinicio (16:55)

**Evento:** Los workers se detuvieron silenciosamente alrededor de las 14:31 (aprox 400 URLs procesadas).
**Diagnóstico:** Posible crash silencioso o terminación del proceso padre. No se encontraron procesos activos.
**Acción:** Se realizó un reinicio manual de los 8 workers a las 16:55 usando `parallel_launcher_semanal.py`.
**Estado Final:** Workers procesando correctamente. Monitoreo delegado al usuario via `monitor_workers.py`.

## 🔄 Segunda Intervención (17:15) - Solución Definitiva con Nohup

**Problema:** Los workers se detuvieron nuevamente porque estaban atados a la sesión de terminal del IDE.
**Solución:** Se mataron los procesos huérfanos y se relanzó el launcher usando `nohup` para desacoplarlo de la sesión.
**Comando usado:** `nohup python3 parallel_launcher_semanal.py > nohup.out 2>&1 &`
**Verificación:** Proceso padre (PID 162879) y 8 workers corriendo en background de forma independiente.

## 🚀 Integración Linux y Cierre de Sesión

### 1. Migración de Menú CRM a Linux
- **Objetivo:** Permitir controlar los scrapers desde Linux (Mint) sin perder compatibilidad con Windows.
- **Acción:** Se creó `whatsapp_bot/menu_crm.sh` (versión Bash de `MENU_CRM.bat`).
- **Nuevas funcionalidades:**
    - Detecta automáticamente el emulador de terminal (gnome-terminal, x-terminal-emulator, etc.).
    - Incluye **Opción 11: Ejecutar Proceso Semanal** (Lanza workers background + Monitor).
    - Incluye acceso directo de escritorio: `CRM Neoauto.desktop`.

### 2. Corrección de Scripts de Automatización
Se detectaron y corrigieron rutas absolutas incorrectas (hardcoded) en los scripts shell:

#### A. `run_scraper_sequence_diario.sh` (Opción 7)
- **Corrección:**
    - `PROJECT_DIR`: Actualizado a `/home/richgutz/Scraper-Neoauto-ANTIGRAVITY`.
    - `PYTHON_EXEC`: Simplificado a `python3` (eliminada referencia a venv inexistente).

#### B. `run_scraper_semanal.sh` (Opción 11 -> Full Sequence)
- **Corrección:**
    - `PROJECT_DIR`: Actualizado.
    - `PYTHON_EXEC`: Actualizado a `python3`.
    - **SendGrid:** Corregida ruta de llamada a `sendgrid_sender.py`.

### 3. Estado Final al Cierre
- **Workers:** 8 procesos corriendo en background (desacoplados con `nohup`).
- **Monitoreo:** Disponible via Opción 11 -> 2 del menú de escritorio.
- **Automatización:** Scripts de shell listos para ejecución manual o vía cron.

**Sesión finalizada exitosamente. Antigravity cerrando.**
