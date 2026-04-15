# Guía de Instalación: Bot WhatsApp Anny Rojas 🚗💨

Esta guía detalla cómo configurar la computadora de Anny para que el bot de contacto automático funcione correctamente.

## 1. Requisitos de Software
1. **Google Chrome**: Instalar la versión estándar.
2. **Python**: Descargar e instalar [Python 3.12](https://www.python.org/downloads/) (Asegurarse de marcar la casilla **"Add Python to PATH"** durante la instalación).

## 2. Preparación de Carpeta
Copiar la carpeta completa `Scraper.Neoauto` a la computadora de Anny (puede ser en el Escritorio o en `C:\`).

## 3. Instalación de Librerías
Abrir una terminal (PowerShell o CMD) dentro de la carpeta del proyecto y ejecutar:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib selenium webdriver-manager beautifulsoup4 python-dotenv supabase
```

## 4. Archivos de Configuración (Copiar de tu PC)
Asegúrate de que la computadora de Anny tenga estos archivos específicos:
- `.env`: (En la raíz) Contiene las llaves de la base de datos.
- `gmail_sender/credentials.json`: Las llaves de la API de Google.
- `DISPARAR_BOT_ANNY.bat`: El acceso directo para que ella lo ejecute.

## 5. El Bot Automático
Para iniciar el proceso, Anny solo debe:
1. Hacer doble clic en el archivo **`DISPARAR_BOT_ANNY.bat`**.
2. **Primera vez**: Se abrirá una ventana de Chrome para que elija su cuenta de Google y haga clic en "Permitir".
3. **QR de WhatsApp**: Se abrirá una ventana de Chrome con WhatsApp Web. Ella debe escanear el código QR con su celular de trabajo.

> [!IMPORTANT]
> A partir de ahí, el bot recordará su sesión. Ella solo tendrá que abrir el `.bat` una vez al día o cuando quiera procesar nuevos leads.

## 6. Uso desde el CRM Web
Para la gestión diaria, Anny debe usar:
- **URL**: [crm-neoauto.geeksoft.tech](http://crm-neoauto.geeksoft.tech)
- Desde allí puede cambiar estados, agendar las citas en el calendario y ver la disponibilidad de Rich.
