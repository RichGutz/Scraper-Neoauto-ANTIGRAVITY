# Plan de Implementación: Subida de Documentos a Google Drive (v2)

## Objetivo
Agregar un módulo interactivo en la pestaña "Vendidos" que permita cargar documentos clasificados del vehículo hacia Google Drive. 
Utilizaremos el **Boilerplate del Mini ERP** (Service Account) para garantizar que la autenticación sea automática y transparente en el servidor (Hostinger), sin necesidad de flujos OAuth manuales ni `token.json`.

## Enfoque por Fases (Desarrollo y Pruebas Aisladas)
Para garantizar el éxito y no romper el CRM actual, implementaremos esta solución en etapas incrementales:

### Fase 1: Configuración del Entorno y Credenciales
- **Destino**: Crearemos la carpeta raíz del CRM directamente en tu cuenta de Google Drive personal (`rgutil@gmail.com`), aprovechando los 5 TB de tu plan Google AI.
- **Credenciales (SA)**: Intentaremos reciclar el archivo `sa_credentials.json` del proyecto ERP (Boilerplate). Si por alguna razón de permisos no funciona para escribir en tu Drive personal, te guiaré para generar un nuevo archivo JSON exclusivo desde la consola de Google Cloud para este proyecto.

### Fase 2: Pruebas con Data Dummy (Testing Aislado)
- Crearemos un script de prueba aislado (ej. `test_uploader.py`) dentro de `G_Drive_Uploader`.
- Usaremos este script para intentar subir archivos "dummy" (archivos de texto o PDFs falsos) hacia tu Drive.
- Validaremos que se cree correctamente la carpeta `YYYYMMDD_PLACA`, sus subcarpetas y que el auto-renombrado funcione según la convención.

### Fase 3: Integración en el CRM (Producción)
- **Solo cuando la Fase 2 sea 100% exitosa**, tomaremos el "artefacto" validado y lo conectaremos directamente en la interfaz de usuario de `frontend_app.py` en la pestaña Vendidos.

## Componentes Involucrados

### 1. Extracción del Boilerplate (Mini ERP)
Tras estudiar `google_integration.py` del ERP, vamos a importar las siguientes piezas clave hacia `C:\Users\rguti\Scraper.Neoauto\CRM-NEOAUTO\G_Drive_Uploader`:
- `get_sa_credentials_dict()`: Manejo robusto de credenciales de Service Account.
- `create_folder_with_sa()`: Para crear la estructura de carpetas automáticamente.
- `upload_file_with_sa()`: Sube el archivo directo usando MediaIoBaseUpload desde la memoria (BytesIO), lo cual es perfecto para el `st.file_uploader` de Streamlit porque evita tener que guardar archivos temporales en el disco del servidor.

### 2. Interfaz Gráfica (Layout 3 Columnas en Vendidos)
- **Columna Izquierda (GyP)**: Resumen Financiero y burbujas de utilidades.
- **Columna Central (Bitácora)**: Historial de notas.
- **Columna Derecha (Documentos Compra/Venta)**: Aquí vivirá el nuevo gadget interactivo con zonas *Drag & Drop* para:
  - 📷 **Fotos**
  - 💳 **Tarjeta de Propiedad**
  - 📝 **Testimonio de Compra**
  - 📝 **Testimonio de Venta**

### 3. Estructura y Convenciones en Google Drive
- **Carpeta Raíz del Vehículo**: `YYYYMMDD_PLACA` (Ej. `20260601_ABC123`).
- **Sub-carpetas por Defecto**: `Fotos`, `Testimonios`, `Tarjeta De propiedad`.
- **Auto-renombrado Inteligente**: `YYYYMMDD_PLACA_FOTO1`, `YYYYMMDD_PLACA_TARJETA_DE_PROPIEDAD`, etc.

### 4. Base de Datos (Supabase)
Necesitamos añadir una columna JSON o Texto donde guardemos los metadatos y enlaces de los documentos.
* Comando SQL sugerido: `ALTER TABLE crm_gyp ADD COLUMN documentos JSONB DEFAULT '[]'::jsonb;`

## Open Questions
> [!IMPORTANT]
> 1. **Acceso del Service Account**: El Service Account del ERP tiene un correo propio (ej. `algo@proyecto.iam.gserviceaccount.com`). Para que pueda subir cosas a tu Drive de 5TB (`rgutil@gmail.com`), debes crear una carpeta en tu Drive (ej. "CRM Documentos") y **compartirla** dándole permisos de "Editor" a ese correo del Service Account. ¿Ya tienes creada esa carpeta para que probemos?
