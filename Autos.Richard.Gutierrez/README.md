# Generador de Reportes de Autos - Quick Start

## Setup Rápido (Linux)

```bash
# 1. Instalar dependencias
pip3 install pandas python-dotenv supabase playwright pillow
playwright install --with-deps chromium

# 2. Configurar credenciales
cat > .env << EOF
SUPABASE_URL=tu_url_aqui
SUPABASE_KEY=tu_key_aqui
EOF

# 3. Ejecutar
python3 generate_autos_report.py
```

## Salida

- **PDF Final**: `reporte_autos_final.pdf` (~10MB, listo para email)
- **HTML**: `reporte_autos_final.html` (intermedio)
- **Imágenes**: `downloaded_images/` (cache)

## Configuración

Editar en `generate_autos_report.py`:

```python
PRICE_MIN = 15000          # Precio mínimo
PRICE_MAX = 16500          # Precio máximo
MAX_AGE_YEARS = 7          # Antigüedad máxima
DAYS_BACK = 30             # Días hacia atrás
```

## Regenerar sin Scraping

Si ya tienes las imágenes descargadas:

```bash
python3 regenerate_pdf_optimized.py  # Más rápido, usa cache
```

## Documentación Completa

Ver `SCRIPT_DOCUMENTATION.md` para detalles técnicos completos.
