@echo off
setlocal
TITLE Secuencia Diaria Scraper

REM --- Configuración ---
REM Use absolute path to ensure robustness
set "PROJECT_DIR=C:\Users\rguti\Scraper.Neoauto"
set "LOG_FILE=%PROJECT_DIR%\scraper_sequence.log"
REM Assuming python is in PATH or use absolute path
set "PYTHON_EXEC=python" 

REM --- Logging Setup ---
echo. >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"
echo INICIANDO SECUENCIA DE SCRAPING - %DATE% %TIME% >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"

REM Move to project dir
pushd "%PROJECT_DIR%"

REM --- Secuencia de Ejecución ---

REM 1. Extraccion de URLs (1 dia)
echo --^> Ejecutando Extraccion de URLs...
echo --^> Ejecutando Extraccion de URLs... >> "%LOG_FILE%"
%PYTHON_EXEC% "extractores\2.DIARIO.daily_urls_extraction.VCLI.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR en Extraccion de URLs. >> "%LOG_FILE%"
    goto :ERROR
)

REM 2. Scraper Principal (6 INSTANCIAS PARALELAS)
echo.
echo --^> Lanzando 6 instancias paralelas del SCRAPER...
echo --^> Lanzando 6 instancias paralelas del SCRAPER... >> "%LOG_FILE%"

REM Usamos PowerShell para lanzar 6 procesos y esperar a que TODOS terminen
REM Usamos el launcher de Python para manejar la paralelizacion y el logging en tiempo real
%PYTHON_EXEC% -u "parallel_launcher.py" >> "%LOG_FILE%" 2>&1

echo --^> Scrapers finalizados.
echo --^> Scrapers finalizados. >> "%LOG_FILE%"


REM 4. Procesamiento JSON y Supabase
echo --^> Procesando JSONs... >> "%LOG_FILE%"
%PYTHON_EXEC% "extractores\5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py" >> "%LOG_FILE%" 2>&1
%PYTHON_EXEC% "extractores\6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py" >> "%LOG_FILE%" 2>&1

REM 5. Generador de Reporte (General/Legado) - DESACTIVADO TEMPORALMENTE
REM echo --^> Generando Reporte General... >> "%LOG_FILE%"
REM %PYTHON_EXEC% "generador_reporte_beta.py" >> "%LOG_FILE%" 2>&1

REM --- Reporte Richard Gutierrez (PDF + Email) ---
echo --^> Reporte Richard Gutierrez... >> "%LOG_FILE%"
%PYTHON_EXEC% "Autos.Richard.Gutierrez\generate_autos_report.py" >> "%LOG_FILE%" 2>&1

REM Envio Correo Richard (Usando Auto-Discovery de PDF)
echo --^> Enviando correo Richard... >> "%LOG_FILE%"
%PYTHON_EXEC% "Autos.Richard.Gutierrez\email_result.py" >> "%LOG_FILE%" 2>&1


REM --- Reporte General (WKHTMLTOPDF + Drive + Email) --- DESACTIVADO
REM echo --^> Reporte General... >> "%LOG_FILE%"
REM set "HTML_REPORT=%PROJECT_DIR%\outputs\gmail_reporte_beta.html"
REM set "PDF_REPORT=%PROJECT_DIR%\outputs\reporte_leads_unico_dueno.pdf"

REM wkhtmltopdf "%HTML_REPORT%" "%PDF_REPORT%" >> "%LOG_FILE%" 2>&1

REM echo --^> Subiendo a Drive... >> "%LOG_FILE%"
REM %PYTHON_EXEC% "google_drive\drive_uploader.py" > "drive_link_temp.txt"
REM set /p DRIVE_LINK=<"drive_link_temp.txt"
REM del "drive_link_temp.txt"

REM echo --^> Enviando correo final... >> "%LOG_FILE%"
REM if NOT "%DRIVE_LINK%"=="" (
REM    %PYTHON_EXEC% "gmail_sender\gmail_sender.py" --enviar-correos --drive-link "%DRIVE_LINK%" --pdf-path "%PDF_REPORT%" >> "%LOG_FILE%" 2>&1
REM ) else (
REM    %PYTHON_EXEC% "gmail_sender\gmail_sender.py" --enviar-correos --pdf-path "%PDF_REPORT%" >> "%LOG_FILE%" 2>&1
REM )

echo. >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"
echo SECUENCIA COMPLETADA - %DATE% %TIME% >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"

echo.
echo PROCESO FINALIZADO.

REM --- APAGADO AUTOMATICO ---
echo.
echo --^> INICIANDO APAGADO DEL SISTEMA EN 60 SEGUNDOS...
echo --^> INICIANDO APAGADO DEL SISTEMA EN 60 SEGUNDOS... >> "%LOG_FILE%"
shutdown /s /t 60

popd
exit /b 0

:ERROR
echo ERROR FATAL EN LA SECUENCIA. REVISE EL LOG. >> "%LOG_FILE%"
popd
exit /b 1
