# 🚀 Plan de Optimización y Diagnóstico de Rendimiento del CRM
**Ubicación:** `CRM-NEOAUTO/Mejoras.Al.CRM.md`

Este documento detalla el diagnóstico técnico de los cuellos de botella que causan lentitud en el CRM de Streamlit y establece las propuestas de optimización específicas para lograr una velocidad de respuesta instantánea.

---

## 🔍 Diagnóstico: ¿Por qué la aplicación es lenta?

Streamlit funciona re-ejecutando todo el script de Python de arriba a abajo en cada interacción del usuario. Si el script realiza consultas síncronas de red a la base de datos dentro de ese flujo sin el uso adecuado de caché, la aplicación se bloquea por la latencia acumulada.

Hemos detectado **3 cuellos de botella críticos**:

### 🚨 1. Bucle de Peticiones Síncronas a Supabase (Tab "Vendidos")
En la construcción de la grilla para los vehículos en **Estado 6: Vendido** (`frontend_app.py`, línea 421-424), el sistema realiza lo siguiente:
```python
if estado == "Estado 6: Vendido":
    gyp_data_row = fetch_gyp(row['url']) or {}  # <-- LLAMADA DE RED INDIVIDUAL
    utilidad = float(gyp_data_row.get("utilidad_neta_usd", 0) or 0)
    ganancia_total_acumulada += utilidad
```
* **Causa de lentitud:** Por cada fila (vehículo) en la lista de vendidos, se realiza una llamada HTTP individual y bloqueante a la base de datos de Supabase para obtener su GyP. Si hay 20 vehículos vendidos, el sistema hace **20 peticiones secuenciales de red**. Esto añade entre **4 y 8 segundos de latencia** en cada refresco de pantalla.
* **Propuesta de Optimización:** Realizar una única consulta masiva a la tabla `crm_gyp` al arrancar la aplicación (`supabase.table("crm_gyp").select("*").execute()`), convertirla en DataFrame y hacer un merge local en memoria en una fracción de segundo con Pandas. Esto reduce el número de llamadas de red a **exactamente una (1)**.

---

### 🚨 2. Cero Caché en la Sección de Investigación (`dynamic_filters.py`)
El módulo de investigación realiza filtros dinámicos consultando la tabla maestra de scraped data (`autos_detalles`), la cual contiene miles de registros.
* **Causa de lentitud:** Las funciones `get_unique_brands`, `get_models_by_brand`, `get_years_by_model` y `fetch_market_data` **no tienen ningún tipo de decorador de caché**. Cada vez que el usuario escribe, cambia de tab o hace una selección, el script descarga todos los registros de marcas, modelos y años desde el servidor remoto de Supabase por internet.
* **Propuesta de Optimización:** Decorar todas las funciones de consulta de filtros de mercado con `@st.cache_data(ttl=1800)` (caché con tiempo de vida de 30 minutos). Dado que la lista de marcas, modelos y años del mercado de autos no cambia minuto a minuto, esto evitará llamadas de red redundantes y hará que la navegación de filtros sea instantánea.

---

### 🚨 3. Limpieza de Caché Ineficiente (`st.cache_data.clear()`)
Cada vez que se guarda una nota de GyP, se agrega una bitácora o se cambia el estado de un lead, el sistema ejecuta la instrucción `st.cache_data.clear()`.
* **Causa de lentitud:** En lugar de invalidar únicamente la caché de los leads (`fetch_leads`), Streamlit borra la memoria global del servidor. Esto provoca que en la siguiente interacción la aplicación deba descargar absolutamente todo desde cero (leads, datos maestros de investigación, históricos), haciendo que la aplicación se "congele" durante unos segundos.
* **Propuesta de Optimización:** Evitar el uso de `.clear()` global y en su lugar emplear técnicas de refresco selectivo a través de `st.session_state` o persistencia local en memoria para evitar re-consultar bases de datos inalteradas.

---

## 📈 Plan de Acción para la Optimización

### Fase 1: Optimización de Consultas de Red en CRM
* Reemplazar la función de bucle individual por una consulta masiva de GyP al inicio y resolver el merge de datos en Pandas.
* Implementar un mapeador local `dict` en base a la URL del lead para acceso a utilidades y costos de forma inmediata.

### Fase 2: Implementación de Caché en Investigación
* Añadir `@st.cache_data` con expiración inteligente a todas las funciones del módulo `Market_Research/dynamic_filters.py`.
* Cachear el procesamiento y normalización de marcas y modelos para evitar sobrecargar la CPU del servidor.

### Fase 3: Modularización de Librerías Pesadas
* Cambiar las importaciones globales de librerías como `plotly.express` y `reportlab` para que se importen de manera local dentro de las funciones que generan los gráficos y PDFs, reduciendo el tiempo de inicialización de Streamlit en cada rerun.
