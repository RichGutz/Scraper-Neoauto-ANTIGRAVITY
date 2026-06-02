# Plan de Implementación: Reporte de Auditoría y Salud del Scraper Semanal

Este plan propone agregar un mecanismo de auditoría automático al final del pipeline semanal para evaluar la salud del proceso de scraping. El objetivo es reportar cuántos autos de cada marca fueron procesados, cuántos fueron nuevos e insertados, y cuántos fueron duplicados omitidos, enviando esta información en un correo electrónico por separado.

## Paráfrasis del Requerimiento

El usuario desea contar con una auditoría de alto nivel para el proceso de scraping semanal. Debido a que la base de datos maestra (`autos_detalles`) es grande (~45,000 registros), cada ejecución semanal saludable de los lunes debería procesar un volumen superior a los 2,000 vehículos. 

Para verificar esta "salud del scraper" de forma rápida, se implementará un reporte breve e integral (enviado en un correo separado) que indique:
1. **Total de vehículos procesados** en la sesión.
2. **Desglose completo por marca** (`Make`).
3. **Conteo detallado de registros nuevos insertados** en Supabase versus **duplicados/existentes omitidos**.
4. **Alerta visual** si el volumen total procesado es inferior al umbral mínimo de salud (2,000 autos).

---

## Cambios Propuestos

### 1. Integración de Git (Paso Inicial Obligatorio)
Para no perder las configuraciones probadas en la sesión anterior (como los 7 trabajadores paralelos, la corrección del buzón en `gmail_sender.py`, y los scripts de diagramas de flujo), realizaremos la integración en `master`:
* Fusionar (merge) la rama de respaldo `FUNCIONAL.01.06.26` hacia la rama `master`.

---

### 2. Recolección de Métricas en el Importador a Supabase

#### [MODIFY] [6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py](file:///home/richgutz/Scraper-Neoauto-ANTIGRAVITY/extractores/6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py)
* **Variables de control en memoria:** Agregar un diccionario acumulador global para registrar los resultados de la ejecución:
  ```python
  stats = {
      "total_procesados": 0,
      "nuevos_insertados": 0,
      "duplicados_omitidos": 0,
      "errores": 0,
      "marcas": {} # Estructura: {"Toyota": {"procesados": 0, "insertados": 0, "omitidos": 0, "errores": 0}}
  }
  ```
* **Lógica de Inserción:** Actualizar `importar_json_a_supabase()` para incrementar las métricas según el resultado de cada archivo JSON (validación, duplicidad en BD o inserción exitosa).
* **Generación del Reporte HTML:** Al finalizar el procesamiento de todos los archivos JSON, el script creará un reporte en `outputs/scraper_audit_report.html` con las siguientes características:
  * Diseño moderno y limpio (estética premium, tipografía sans-serif, tarjetas con métricas clave en colores curados).
  * Tarjetas de resumen:
    * **Total Procesados** (con advertencia en rojo si es < 2,000).
    * **Nuevos Insertados**.
    * **Omitidos (Duplicados)**.
    * **Errores/Descartados**.
  * Tabla con el desglose detallado por marca ordenado por volumen total descendente.

---

### 3. Distribución del Reporte de Auditoría vía Email

#### [MODIFY] [gmail_sender/gmail_sender.py](file:///home/richgutz/Scraper-Neoauto-ANTIGRAVITY/gmail_sender/gmail_sender.py)
* Agregar un nuevo argumento de línea de comandos: `--send-audit` (booleano).
* Modificar el flujo principal para que, si `--send-audit` está activo:
  * Lea el archivo de auditoría generado en `outputs/scraper_audit_report.html`.
  * Defina el asunto como: `Auditoría de Salud - Scraper Semanal (YYYY-MM-DD)`.
  * Envíe este correo de forma separada a los destinatarios listados en `gmail_sender/destinatarios.txt`.

---

### 4. Automatización del Pipeline Semanal

#### [MODIFY] [run_scraper_semanal.sh](file:///home/richgutz/Scraper-Neoauto-ANTIGRAVITY/run_scraper_semanal.sh)
* Añadir la instrucción para enviar el correo de auditoría justo después del envío del reporte de leads:
  ```bash
  # --- Envío de Correo de Auditoría de Salud ---
  echo ""
  echo "--> Enviando reporte de auditoría y salud del scraper (Gmail)..."
  $PYTHON_EXEC "$PROJECT_DIR/gmail_sender/gmail_sender.py" --enviar-correos --send-audit
  echo "Proceso de auditoría de salud finalizado."
  ```

---

## Plan de Verificación

### Pruebas Automatizadas/Manuales
1. **Verificación de Ingesta y Estadísticas:**
   * Ejecutar localmente `6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py` con un subconjunto de archivos JSON de prueba y validar que `outputs/scraper_audit_report.html` se genere con las métricas correctas.
2. **Prueba de Envío del Correo de Auditoría:**
   * Ejecutar `gmail_sender.py --enviar-correos --send-audit` y comprobar en la bandeja de entrada de `rgutil@gmail.com` la correcta recepción y visualización del reporte con su formato premium.
3. **Integración Completa:**
   * Validar que la llamada integrada dentro de `run_scraper_semanal.sh` no cause interrupciones al flujo completo.
