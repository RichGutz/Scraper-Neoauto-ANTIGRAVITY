@echo off
setlocal
TITLE Secuencia Semanal Scraper NeoAuto

REM --- Configuración ---
set "PROJECT_DIR=C:\Users\rguti\Scraper.Neoauto"
set "LOG_FILE=%PROJECT_DIR%\scraper_sequence_semanal.log"
set "PYTHON_EXEC=python"

REM --- Logging Setup ---
echo. >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"
echo INICIANDO SECUENCIA SEMANAL - %DATE% %TIME% >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"

pushd "%PROJECT_DIR%"

REM 1. Extraccion V2 (Barrido por marcas)
echo --^> Paso 1: Ejecutando Extraccion Semanal V2...
echo --^> Paso 1: Ejecutando Extraccion Semanal V2... >> "%LOG_FILE%"
%PYTHON_EXEC% "extractores\2.SEMANAL.extractor_VCLI_v2.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR en Paso 1. >> "%LOG_FILE%" & goto :ERROR)

REM 2. Randomize URLs
echo --^> Paso 2: Aleatorizando URLs...
echo --^> Paso 2: Aleatorizando URLs... >> "%LOG_FILE%"
%PYTHON_EXEC% "extractores\3.SEMANAL.randomize_urls_autos.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR en Paso 2. >> "%LOG_FILE%" & goto :ERROR)

REM 3. Scraper Principal (Paralelo)
echo --^> Paso 3: Lanzando instancias paralelas del SCRAPER...
echo --^> Paso 3: Lanzando instancias paralelas del SCRAPER... >> "%LOG_FILE%"
%PYTHON_EXEC% -u "parallel_launcher.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR en Paso 3. >> "%LOG_FILE%" & goto :ERROR)

REM 4. Procesamiento JSON y UBIGEO
echo --^> Paso 4: Procesando JSONs y UBIGEO...
echo --^> Paso 4: Procesando JSONs y UBIGEO... >> "%LOG_FILE%"
%PYTHON_EXEC% "extractores\5.DIARIO.SEMANAL.Procesador_txt.a.json.DEEPSEEK_VCLI.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR en Paso 4. >> "%LOG_FILE%" & goto :ERROR)

REM 5. Carga a Supabase
echo --^> Paso 5: Cargando a Supabase...
echo --^> Paso 5: Cargando a Supabase... >> "%LOG_FILE%"
%PYTHON_EXEC% "extractores\6.json_a_supabase.DEEP.SEEK.CRON.VCLI.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR en Paso 5. >> "%LOG_FILE%" & goto :ERROR)

REM 6. Generador de Reporte Semanal (Dashboard)
echo --^> Paso 6: Generando Reporte Semanal...
echo --^> Paso 6: Generando Reporte Semanal... >> "%LOG_FILE%"
%PYTHON_EXEC% "main.py" >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (echo ERROR en Paso 6. >> "%LOG_FILE%" & goto :ERROR)

echo ================================================== >> "%LOG_FILE%"
echo SECUENCIA SEMANAL COMPLETADA - %DATE% %TIME% >> "%LOG_FILE%"
echo ================================================== >> "%LOG_FILE%"

echo.
echo PROCESO SEMANAL FINALIZADO CON EXITO.
popd
exit /b 0

:ERROR
echo.
echo [!] ERROR DETECTADO EN LA SECUENCIA. Revise scraper_sequence_semanal.log
popd
exit /b 1
