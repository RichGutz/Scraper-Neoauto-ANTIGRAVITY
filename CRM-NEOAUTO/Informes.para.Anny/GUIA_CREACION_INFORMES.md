# Guía de Creación de Informes de Mercado CRM Neoauto

Esta guía detalla el procedimiento técnico y los scripts utilizados para generar informes de valoración de vehículos basados en la data histórica de Supabase.

## Paso 1: Extracción de Datos de Supabase

Para obtener una muestra representativa, se debe consultar la tabla `autos_detalles_diarios`. Es vital realizar búsquedas flexibles (`ILike`) ya que los nombres de marcas y modelos pueden variar (ej. "Mercedes" vs "Mercedes Benz").

**Comando de consulta sugerido:**
```python
# Ejemplo de búsqueda en Python para Mercedes GLC 250 del 2019
response = supabase.table('autos_detalles_diarios') \
    .select('Make, Model, Year, Price, Kilometers, District, URL') \
    .ilike('Model', '%GLC%250%') \
    .eq('Year', '2019') \
    .execute()
```

## Paso 2: Creación del Documento Maestro (Markdown)

Con los datos obtenidos, se genera un archivo `.md`. Este archivo debe contener:
1.  **Tabla Comparativa:** Listando Modelo, Precio, KM, Distrito y el Link directo a Neoauto.
2.  **Análisis Estadístico:** Cálculo de la **mediana** de precio y kilometraje.
3.  **Conclusiones:** Veredicto basado en la desviación del precio respecto a la mediana (Trato justo +/- 5%).

## Paso 3: Conversión a PDF Premium

Para que el informe tenga una presentación profesional para el cliente, se utiliza un script de conversión con CSS personalizado.

### Scripts Utilizados

#### 1. Analizador Lógico (`analyze_manual_deal.py`)
Ubicación: `C:\Users\rguti\Scraper.Neoauto\Autos.Richard.Gutierrez\analyze_manual_deal.py`
Este script permite ingresar los datos manualmente y devuelve el veredicto en consola, además de ofrecer el envío por WhatsApp.

#### 2. Generador de PDF (`generate_mercedes_pdf.py`)
Ubicación: `C:\Users\rguti\Scraper.Neoauto\documentation\generate_mercedes_pdf.py`
Este script toma el archivo Markdown y lo transforma en un PDF con estilo "Premium" usando las librerías `weasyprint` y `markdown2`.

**Código del Conversor:**
```python
import markdown2
from weasyprint import HTML, CSS
from pathlib import Path

def convert(md_path, pdf_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Soporte para tablas
    html_content = markdown2.markdown(md_content, extras=['tables'])
    
    # CSS Premium (Landscape o Portrait)
    STYLE = """
    @page { size: A4 portrait; margin: 2cm; }
    body { font-family: 'Segoe UI', sans-serif; color: #333; }
    h1 { color: #1a3a5a; border-bottom: 2px solid #1a3a5a; }
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #1a3a5a; color: white; padding: 10px; }
    td { border: 1px solid #eee; padding: 8px; }
    """

    HTML(string=html_content).write_pdf(pdf_path, stylesheets=[CSS(string=STYLE)])
```

## Protocolo de Interacción con Anny

Dado que Anny está comenzando a trabajar con agentes, el agente debe seguir este protocolo de solicitud de datos para asegurar que el análisis sea preciso.

### 1. Solicitud de Prompt (Datos del Auto)
Si Anny solicita un informe pero no proporciona los detalles, el agente debe responder pidiéndole los datos en este formato sencillo:

> "Hola Anny, para generar el informe de mercado necesito que me proporciones los siguientes datos del vehículo:
> 1. **Marca y Modelo** (ej. Mercedes GLC 250)
> 2. **Año** (ej. 2019)
> 3. **Kilometraje** (ej. 30,000 km)
> 4. **Precio** (Opcional - si quieres saber si es una buena oferta)
> 5. **Transmisión** (Opcional - Mecánica o Automática)"

### 2. Flujo de Trabajo del Agente (Paso a Paso)

Una vez que Anny entregue los datos, el agente debe seguir este flujo interno sin necesidad de más instrucciones:

1.  **Búsqueda en Supabase:** Realizar la consulta a la tabla `autos_detalles_diarios` (usando `ILike` para mayor flexibilidad).
2.  **Generación de Reporte MD:** Crear un archivo Markdown con la tabla comparativa y las conclusiones.
3.  **Ejecución del Generador PDF:** Utilizar el script `C:\Users\rguti\Scraper.Neoauto\documentation\generate_mercedes_pdf.py` (o similar) para crear el archivo final.
4.  **Entrega:** Proporcionar el link del PDF final a Anny y un resumen ejecutivo del veredicto en el chat.

## Herramientas y Scripts del Sistema

Para que el flujo funcione, el sistema cuenta con dos generadores principales:

### 1. El Analizador de Deal (`analyze_manual_deal.py`)
*Ubicación: `C:\Users\rguti\Scraper.Neoauto\Autos.Richard.Gutierrez\analyze_manual_deal.py`*
Es el motor lógico. Calcula medianas, desviaciones de precio y alertas de kilometraje.

### 2. El Motor de PDF (`generate_mercedes_pdf.py`)
*Ubicación: `C:\Users\rguti\Scraper.Neoauto\documentation\generate_mercedes_pdf.py`*
Transforma el análisis visual en un documento PDF listo para entregar al cliente final, con formato profesional.

---

**Nota para el Agente:** Siempre trata de que el proceso sea lo más automático posible para Anny. Una vez que ella da el "Prompt" con los datos, tú debes entregarle el PDF terminado.
