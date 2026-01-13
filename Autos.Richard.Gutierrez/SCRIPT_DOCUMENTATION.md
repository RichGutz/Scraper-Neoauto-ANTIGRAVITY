# SCRIPT DOCUMENTATION: generate_autos_report.py
# Fecha de creación: 2024-12-14
# Autor: Gemini AI Agent
# Propósito: Generar reportes PDF optimizados de búsqueda de autos para Santiago Ganoza

## DESCRIPCIÓN GENERAL

Este script automatiza la búsqueda, scraping y generación de reportes PDF de autos usados desde la base de datos Supabase y el sitio web Neoauto.com. El reporte final es un PDF de ~10MB (optimizado desde 40MB) que puede ser enviado por email.

## REQUISITOS DEL SISTEMA

### Sistema Operativo
- ✅ Windows (probado)
- ✅ Linux (compatible)
- ✅ macOS (compatible)

### Dependencias Python
```bash
pip install pandas python-dotenv supabase playwright pillow
playwright install chromium
```

### Variables de Entorno (.env)
```
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_key_de_supabase
```

## FLUJO DE TRABAJO

### 1. EXTRACCIÓN DE DATOS (fetch_data)
- **Fuente**: Tabla `autos_detalles_diarios` en Supabase
- **Filtros iniciales**:
  - `unico_dueno = True` (solo autos de único dueño)
  - `Price >= 15000 AND Price <= 16500` (rango de precio)

### 2. FILTRADO DE DATOS (filter_data)
Aplica 5 filtros secuenciales:

1. **Filtro de Edad**: Solo autos de máximo 7 años de antigüedad
   - Año mínimo = Año actual - 7
   
2. **Filtro de Marca**: Solo marcas específicas
   - Japonesas: TOYOTA, HONDA, NISSAN, MAZDA, SUBARU, SUZUKI, MITSUBISHI, LEXUS, INFINITI, ACURA
   - Coreanas: KIA, HYUNDAI, GENESIS, SSANGYONG
   - Americanas: CHEVROLET, FORD, JEEP, DODGE, CHRYSLER, RAM, GMC, CADILLAC, LINCOLN, TESLA, BUICK
   - Alemanas: BMW, MERCEDES-BENZ, AUDI, VOLKSWAGEN, PORSCHE

3. **Filtro de Fecha**: Solo publicaciones de los últimos 30 días
   - Usa timezone UTC para comparación
   - Fallback a naive datetime si hay problemas de timezone

4. **Filtro de Transmisión**: Excluye transmisiones mecánicas/manuales
   - Regex: `Mecánica|Mecanica|Manual` (case-insensitive)

5. **Filtro de Combustible**: Solo gasolina
   - `Fuel Type == 'Gasolina'`

### 3. SCRAPING DE IMÁGENES Y METADATA (scrape_images_and_metadata)

#### Configuración del Browser
- **Engine**: Playwright + Chromium
- **Modo**: Headless
- **Stealth**: `--disable-blink-features=AutomationControlled`
- **User Agent**: Chrome 114 en Windows 10

#### Proceso por Auto
Para cada auto en el DataFrame filtrado:

1. **Navegar a la URL del aviso**
   - Timeout: 60 segundos
   - Wait until: domcontentloaded
   - Wait adicional: 3 segundos para contenido dinámico

2. **Buscar Metadata Externa** (Potencia y Consumo)
   - Abre nueva pestaña en Google
   - Query: `{Marca} {Modelo} {Año} ficha tecnica consumo potencia hp`
   - Extrae datos de snippets destacados
   - Regex patterns:
     - Potencia: `(\d{2,4})\s?(hp|cv|HP|CV)`
     - Consumo: `(\d{1,2}[\.,]?\d?)\s?(km/l|km/g|km/gl|l/100km)`

3. **Scraping de Imágenes**
   - **Fuente 1**: Meta tag `og:image`
   - **Fuente 2**: Todas las imágenes `<img>` que cumplan:
     - URL contiene 'neoauto'
     - URL NO contiene 'logo' ni 'reclamaciones'
     - Ancho natural > 400px
   - **Límite**: Máximo 4 imágenes por auto

4. **Descarga y Optimización de Imágenes**
   - Descarga imagen original
   - Aplica `optimize_image()`:
     - Convierte RGBA/PNG a RGB/JPEG
     - Redimensiona a máximo 1200px de ancho (mantiene proporción)
     - Compresión JPEG al 85%
   - Guarda como `{car_id}_{index}.jpg` en carpeta `downloaded_images/`

5. **Almacenamiento de Resultados**
   - Estructura: `results_map[car_id] = {'images': [paths], 'metadata': {dict}}`

### 4. GENERACIÓN DE HTML (generate_html)

#### Estructura del Reporte

1. **Página de Portada**
   - Título: "Búsqueda de Autos"
   - Subtítulo: "Para Santiago Ganoza Recavarren"
   - Parámetros de búsqueda (precio, años, combustible, fecha)
   - Marcas encontradas agrupadas por origen (Japonesas, Coreanas, Americanas, Alemanas)
   - Fecha de generación

2. **Páginas de Autos** (una por auto)
   - **Header**: Marca, Modelo, Año, ID, Fecha de scraping
   - **Hero Image**: Imagen principal (600px, 60% quality, base64)
   - **Specs Grid**: 8 especificaciones en grid 3x3
     - Precio, Kilometraje, Ubicación
     - Transmisión, Combustible, Motor
     - Potencia, Rendimiento
   - **Botón**: Link al aviso original
   - **Gallery**: 3 imágenes adicionales (400px, 55% quality, base64)
   - **Footer**: Fecha de generación

#### Optimización de Imágenes para PDF

**CRÍTICO**: Este es el paso que reduce el PDF de 40MB a ~10MB

- **Hero Image**: 
  - `image_to_base64_data_uri(path, max_width=600, quality=60)`
  - Redimensiona a 600px de ancho
  - Compresión JPEG al 60%
  - Convierte a base64 data URI

- **Gallery Images**:
  - `image_to_base64_data_uri(path, max_width=400, quality=55)`
  - Redimensiona a 400px de ancho
  - Compresión JPEG al 55%
  - Convierte a base64 data URI

**Ventaja de Base64**: Las imágenes se embeben directamente en el HTML, eliminando referencias externas y permitiendo compresión agresiva sin pérdida visual significativa en PDF.

### 5. CONVERSIÓN A PDF (main)

- **Engine**: Playwright + Chromium
- **Formato**: A4
- **Opciones**: `print_background=True` (para mantener estilos)
- **Proceso**:
  1. Guarda HTML como `reporte_autos_final.html`
  2. Abre HTML en browser headless
  3. Genera PDF con `page.pdf()`
  4. Guarda como `reporte_autos_final.pdf`

## ARCHIVOS GENERADOS

```
Autos.Santiago.Ganoza/
├── downloaded_images/          # Carpeta con imágenes optimizadas
│   ├── 12073_0.jpg
│   ├── 12073_1.jpg
│   └── ...
├── reporte_autos_final.html    # HTML intermedio
└── reporte_autos_final.pdf     # PDF FINAL (~10MB)
```

## CONFIGURACIÓN PERSONALIZABLE

### En el código (líneas 18-31):
```python
PRICE_MIN = 15000          # Precio mínimo
PRICE_MAX = 16500          # Precio máximo
MAX_AGE_YEARS = 7          # Antigüedad máxima en años
DAYS_BACK = 30             # Días hacia atrás para filtrar publicaciones
TARGET_BRANDS = [...]      # Lista de marcas a incluir
```

### Optimización de imágenes (líneas 391-392):
```python
# Hero image
hero_img = image_to_base64_data_uri(imgs[0], max_width=600, quality=60)

# Gallery images
gallery_imgs = [image_to_base64_data_uri(img, max_width=400, quality=55) for img in imgs[1:4]]
```

**NOTA**: Reducir `max_width` o `quality` reduce más el tamaño del PDF, pero puede afectar la calidad visual.

## EJECUCIÓN

### Comando básico:
```bash
python generate_autos_report.py
```

### Tiempo estimado:
- 15 autos: ~3-5 minutos
- Depende de:
  - Velocidad de conexión a internet
  - Tiempo de respuesta de Neoauto.com
  - Número de autos a procesar

### Salida esperada:
```
Fetching data from Supabase...
Fetched 390 initial records.
Filtering data...
Converting DateTime...
Filtered down to 15 records.
Scraping images and metadata...
Processing ID 12073: https://neoauto.com/auto/usado/...
  Searching specs for: HYUNDAI I20 HB 2024 ficha tecnica consumo potencia hp
  External Specs Found: {'Potencia': '99 HP', 'Consumo': 'N/A'}
  Found 4 valid images. Downloading...
...
Generating HTML report with base64 optimized images...
Converting images to base64 for car ID 12073...
...
HTML report saved to reporte_autos_final.html
Converting to PDF...
PDF report saved to reporte_autos_final.pdf

✅ OPTIMIZATION: PDF size reduced by ~74% using base64 image embedding with aggressive compression
   - Hero images: 600px width, 60% quality
   - Gallery images: 400px width, 55% quality
   - Expected PDF size: ~10MB (down from ~40MB)
```

## COMPATIBILIDAD LINUX

### Instalación de dependencias en Linux:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-pip
pip3 install pandas python-dotenv supabase playwright pillow
playwright install --with-deps chromium

# Fedora/RHEL
sudo dnf install python3-pip
pip3 install pandas python-dotenv supabase playwright pillow
playwright install --with-deps chromium
```

### Diferencias Windows vs Linux:
- **Rutas de archivos**: El script usa `os.path.join()` que es cross-platform
- **Playwright**: Funciona igual en ambos sistemas
- **Encoding**: UTF-8 especificado explícitamente en `open()`

## TROUBLESHOOTING

### Error: "No module named 'playwright'"
```bash
pip install playwright
playwright install chromium
```

### Error: "SUPABASE_URL not found"
- Verificar que existe archivo `.env` en el mismo directorio
- Verificar que contiene `SUPABASE_URL` y `SUPABASE_KEY`

### Error: "Timeout loading URL"
- Normal para algunos autos (sitio lento o aviso eliminado)
- El script continúa con el siguiente auto
- Los autos sin imágenes se excluyen del reporte final

### PDF muy grande (>15MB)
- Reducir `quality` en líneas 391-392 (ej: 50 y 45)
- Reducir `max_width` (ej: 500 y 300)
- Reducir número de imágenes por auto (línea 289: cambiar `[:4]` a `[:3]`)

### PDF muy pequeño pero imágenes pixeladas
- Aumentar `quality` (ej: 70 y 65)
- Aumentar `max_width` (ej: 800 y 500)

## MANTENIMIENTO

### Actualizar marcas objetivo:
Editar líneas 22-30 en `TARGET_BRANDS`

### Actualizar rango de precios:
Editar líneas 18-19:
```python
PRICE_MIN = 20000  # Nuevo mínimo
PRICE_MAX = 25000  # Nuevo máximo
```

### Cambiar destinatario del reporte:
Editar línea 341:
```python
<h2 style="...">Para [NUEVO NOMBRE]</h2>
```

## NOTAS IMPORTANTES

1. **Rate Limiting**: El script hace scraping de Neoauto.com. Si se ejecuta muy frecuentemente, puede ser bloqueado temporalmente.

2. **Imágenes faltantes**: Algunos autos pueden no tener imágenes si:
   - El aviso fue eliminado
   - El sitio bloqueó el scraping
   - Timeout de conexión
   
3. **Metadata incompleta**: La búsqueda de potencia/consumo en Google no siempre encuentra resultados. Es normal ver "N/A" en algunos autos.

4. **Tamaño del PDF**: El tamaño final depende del número de autos. Fórmula aproximada:
   - ~700KB por auto con 4 imágenes
   - 15 autos ≈ 10.5 MB
   - 20 autos ≈ 14 MB

## SCRIPT ALTERNATIVO: regenerate_pdf_optimized.py

Si ya tienes las imágenes descargadas y solo quieres regenerar el PDF sin scraping:

```bash
python regenerate_pdf_optimized.py
```

Este script:
- NO hace scraping
- Usa imágenes existentes en `downloaded_images/`
- Genera PDF optimizado en ~30 segundos
- Útil para ajustar parámetros de compresión sin re-scrapear

## CONTACTO Y SOPORTE

Para modificaciones o problemas, consultar:
- Código fuente: `generate_autos_report.py`
- Este documento: `SCRIPT_DOCUMENTATION.md`
- Logs de ejecución: Salida estándar del script

---
Última actualización: 2024-12-14
Versión: 2.0 (Optimizada con base64)
