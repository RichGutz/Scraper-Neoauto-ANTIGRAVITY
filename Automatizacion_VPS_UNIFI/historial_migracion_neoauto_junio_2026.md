# Historial de Migración - Neoauto Rediseño (Junio 2026)

Este documento resume todas las reparaciones críticas realizadas a los scrapers de Neoauto tras su actualización estructural que separó la categoría de "seminuevos" y rediseñó el código interno (cambio a Next.js App Router).

## 1. Reparación del Scraper Semanal (V3)
- **Archivo Nuevo:** `extractores/2.SEMANAL.extractor_VCLI_v3.py`
- **Problema:** El script solo leía `/auto/usado/` y fallaba al extraer el contador total de páginas porque Neoauto empezó a escapar el JSON como `\"total\": \d+`.
- **Solución:** Se implementó una lista de `BASE_URL_TEMPLATES` para recorrer tanto `usados` como `seminuevos`. Se ajustaron las expresiones regulares para extraer URLs de seminuevos y se robusteció la lectura del contador de páginas.
- **Orquestador Actualizado:** `run_scraper_semanal.sh` apunta ahora a V3.

## 2. Reparación del Extractor Individual Diario/Semanal (V4)
- **Archivo Nuevo:** `extractores/4.DIARIO.SEMANAL.extractor_individual_v4.py`
- **Problema:** El bot obtenía `NaN`, `inf km` y basura SEO en la descripción. Los selectores CSS de la vista de un vehículo (`span.text-title-x-large`, etc.) dejaron de existir. También hubo bloqueos por CloudFront.
- **Solución:** 
  - Se evadió CloudFront inyectando navegación humana (`headless=True` con rotación y scrolls).
  - Se actualizaron los selectores Javascript:
    - **Precio:** Ahora busca en las clases maestras genéricas (`.text-title-large, .text-title-medium`).
    - **Kilometraje y Transmisión:** Busca directamente la palabra visual "Kilometraje" o "Transmisión" y extrae el texto hermano colindante.
    - **Ubicación:** Se extrae de manera infalible desde la etiqueta `<title>` de la pestaña.
    - **Descripción:** Busca cabeceras con el texto "Descripción" ignorando la basura de JSON-LD (`schema.org`).
- **Orquestador Actualizado:** `run_scraper_semanal.sh` ahora invoca esta V4 en el bloque de procesamiento profundo.

## 3. Reparación del Extractor Diario de URLs (V2)
- **Archivo Nuevo:** `extractores/2.DIARIO.daily_urls_extraction_v2.py`
- **Problema:** Al igual que el semanal, ignoraba los seminuevos de las últimas 24 horas y se rompía con la paginación.
- **Solución:** Se dividió la búsqueda en 2 rondas (`venta-de-autos-usados?publicado=1dia` y `venta-de-autos-seminuevos?publicado=1dia`). Las regex se hicieron compatibles con el término "seminuevo".
- **Orquestador Actualizado:** `run_scraper_sequence_diario.sh` invoca ahora a esta nueva V2.

## 4. Solución al Bug de WOL (Wake On LAN) en el Gateway UniFi
- **Archivo Actualizado:** `Automatizacion_VPS_UNIFI/comandos_emergencia.md`
- **Problema:** El comando de inyección de `cron` desde PowerShell (`ssh root@ip "cat << EOF..."`) fallaba constantemente con "ParserError" porque PowerShell de Windows intercepta localmente los signos `>>` creyendo que son redirecciones locales, incluso dentro de comillas.
- **Solución:** Se documentó que **jamas** se debe enviar el comando completo desde PowerShell. La vía 100% segura es entrar por SSH interactivo (`ssh root@...`) y, una vez dentro del Linux del UniFi, pegar el script `cat << EOF` multilínea.
