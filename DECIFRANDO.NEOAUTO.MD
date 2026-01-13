# DECIFRANDO NEOAUTO: Manual de Guerra Contra-Scraping

**Fecha:** 11 de Enero del 2026
**Objetivo:** Documentar la evolución tecnológica de NeoAuto y cómo vencer sus defensas de scraping.

## 1. El Enemigo: Next.js y Client-Side Hydration

NeoAuto ha migrado de un sitio web tradicional (Server-Side Rendering con HTML semántico) a una aplicación moderna basada en **Next.js** (React).

### El Síntoma
- **Antes:** Podías hacer `soup.select('a.c-results__link')` y obtenías los links.
- **Ahora (2026):** El HTML crudo que devuelve `requests.get` **NO CONTIENE** los elementos `<a>` con las clases esperadas en el cuerpo principal.
- **Error Típico:** El scraper devuelve "0 autos encontrados" aunque el status code sea 200.
- **Causa:** El contenido visible se renderiza vía JavaScript en el navegador (Client-Side Rendering). El HTML inicial solo contiene un "esqueleto" y una gran carga de datos JSON para "hidratar" la página.

## 2. La Defensa: Datos Ocultos en JSON

En lugar de estar en etiquetas HTML, la información de los autos reside en scripts de datos dentro del HTML.

### Estructura Detectada
Los datos se encuentran serializados (a menudo escapados) dentro de variables globales o props de Next.js.
Visualmente en el código fuente se ve así:
```json
\"slug\":\"/auto/usado/toyota-yaris-2020-123456\", \"price\":...
```

## 3. La Solución: Regex Multi-Estrategia

No confíes en selectores CSS ni Xpath para el listado inicial, porque el DOM final no existe en la respuesta cruda de `requests`.

### Estrategia Ganadora (Definida en Script 2.DIARIO)

Implementamos un enfoque de 3 capas en la función `scrape_page`:

1.  **Capa 1: JSON Escapado (La más efectiva)**
    Busca patrones de cadenas escapadas, típicas de datos incrustados en JS.
    *Regex:* `r'\\"slug\\":\\"(/auto/(?:usado|nuevo)/[^"]+)\\"'`

2.  **Capa 2: JSON Simple**
    Fallback por si cambian la forma de serializar (comillas simples o sin escapar).
    *Regex:* `r'"slug":"(/auto/(?:usado|nuevo)/[^"]+)"'`

3.  **Capa 3: HTML Anchor (Legacy/SSR)**
    Fallback final por si la página revierte a Server-Side Rendering completo o si logran bloquear el acceso a los scripts.
    *Regex:* `r'href=["\'](/?auto/(?:usado|nuevo)/[^"\']+)["\']'`

**Nota Crítica:** Siempre normalizar el slug agregando `https://neoauto.com` y asegurando el slash inicial.

## 4. Trampas Adicionales

### A. El Contador de Avisos Falso
- El texto "X avisos encontrados" a veces no está en el HTML plano o es dinámico.
- **Solución:** Si no encuentras el texto, busca `"total":123` en el JSON crudo. Siempre ten un `break` de seguridad: si una página devuelve 0 links, DETÉN el bucle. No confíes en el número total de páginas calculado.

### B. Bloqueo de 403 Forbidden
- NeoAuto bloquea activamente peticiones sin User-Agent o con User-Agents de librerías (como `python-requests`).
- **Solución:** Rotar User-Agents y usar headers de navegador real (Chrome/Firefox en Windows).

### C. "Cero Autos de Hoy" vs "Todos los Autos"
- Si filtras por `publicado=hoy` y no hay resultados, la web a veces redirecciona o muestra sugerencias (todo el catálogo).
- **Detección:** Si tu scraper dice "Encontré 2500 autos de hoy" a las 7 AM, ALERTA. Es imposible. Probablemente estás scrapeando el catálogo general. Verifica la URL final y el comportamiento manual.

## 5. Resumen para el Futuro Gemini

Si el scraper falla de nuevo:
1.  **NO mires el navegador interactivo.** Mira el "View Source" (HTML crudo).
2.  Busca un slug conocido (ej: `/auto/usado/marca-modelo...`).
3.  Fíjate cómo está envuelto ese texto. ¿Está dentro de un `<a>`? ¿O está dentro de un bloque `<script>`?
4.  Si está en un script, ajusta la Regex en `2.DIARIO`. **No intentes renderizar JS con Selenium/Playwright para la extracción masiva de URLs diaria**, es muy lento. Usa Regex sobre el texto crudo.
