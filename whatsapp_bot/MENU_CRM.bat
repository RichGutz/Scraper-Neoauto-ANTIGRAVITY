@echo off
TITLE CRM Neoauto - Menu Principal
color 0A

:MENU
cls
echo ==================================================
echo    CRM NEOAUTO - MENU PRINCIPAL
echo ==================================================
echo.
echo  1. Procesar Correos y Enviar WhatsApps
echo     (Parsea Gmail, crea contactos, envia saludos)
echo.
echo  2. Activar Listener (Monitoreo Continuo)
echo     (Lee conversaciones de WhatsApp en tiempo real)
echo.
echo  3. Enviar Lead de Marketplace
echo     (Manual: Ingresar lead de Facebook) 
echo.
echo  4. Generar Resumen IA
echo     (El cerebro analiza todo y genera reporte)
echo.
echo  5. Analizar Lead (Precio vs Mercado)
echo     (Pega link de Neoauto y obtiene valuacion IA)
echo.
echo  6. RESET DB (Borrar todo)
echo     (Elimina tareas, mensajes y leads)
echo.
echo  7. Secuencia Diaria (1 DIA)
echo     (Scrapea Neoauto [publicado=1dia] + Reportes + Email)
echo.
echo  8. Kill Zombies (Limpiar Procesos)
echo.
echo  9. Resetear Token Google (Solucion Error 403)
echo 10. Responder a Acreedores
echo.
echo  0. Salir
echo.
echo ==================================================
echo.

set /p opcion="Ingrese su opcion: "

if "%opcion%"=="1" goto OP1
if "%opcion%"=="2" goto LISTENER
if "%opcion%"=="3" goto MARKETPLACE
if "%opcion%"=="4" goto RESUMEN_IA
if "%opcion%"=="5" goto ANALIZAR_LEAD
if "%opcion%"=="6" goto RESET_DB
if "%opcion%"=="7" goto SECUENCIA_DIARIA
if "%opcion%"=="8" goto OP8
if "%opcion%"=="9" goto OP9
if "%opcion%"=="10" goto RESPONDER_ACREEDORES
if "%opcion%"=="0" goto SALIR

echo.
echo ERROR: Opcion invalida. Intenta de nuevo.
timeout /t 2 >nul
goto MENU

:SECUENCIA_DIARIA
cls
echo ==================================================
echo  INICIANDO SECUENCIA DIARIA (Modo: 1 DIA)
echo ==================================================
echo.
echo Lanzando procesos en paralelo:
echo 1. Ejecutor de Secuencia (Ventana Minimizada)
echo 2. Monitor de Logs (PowerShell Tail)
echo.

cd /d "%~dp0"
REM Regresamos un nivel al root del proyecto para encontrar el bat
cd ..

echo.
REM 0. Resetear Log
echo INICIANDO NUEVA SECUENCIA... > scraper_sequence.log

REM 1. Lanzar el Worker
echo Lanzando Worker...
start "Worker Scraper" /min cmd /c "run_scraper_sequence_diario.bat"

REM 2. Lanzar el Monitor
echo Lanzando Monitor...
start "Monitor Log Scraper" python tail_log.py

echo.
echo ==================================================
echo MONITOR DE SECUENCIA INICIADO (Ventana Negra)
echo ==================================================
pause
goto MENU

:OP8
cls
echo ==================================================
echo  KILL ZOMBIES (Limpiar Procesos)
echo ==================================================
echo.
echo Matando Zombies...
cd ..
call kill_zombies.bat
pause
goto MENU

:OP9
cls
echo ==================================================
echo  RESETEAR TOKEN DE GOOGLE
echo ==================================================
echo.
echo Buscando token.json para eliminar...
if exist "..\gmail_sender\token.json" (
    del "..\gmail_sender\token.json"
    echo [OK] Token eliminado.
    echo.
    echo AHORA: Ejecute la Opcion 1 (Auto Contact) para volver a loguearse
    echo y acepte TODOS los permisos (Gmail + Contactos).
) else (
    echo [INFO] No se encontro token.json (Ya estaba eliminado).
)
pause
goto MENU

:OP1
goto PROCESAR_CORREOS

:RESPONDER_ACREEDORES
cls
echo ==================================================
echo  RESPONDER A ACREEDORES
echo ==================================================
echo.
cd /d "%~dp0"
cd ..\rpta.automatica.acreedores
rem Launch renamed auto-reply script in new window
start "AutoReply" cmd /c "python auto_reply_acreedores_v1.py"
rem Launch tail log in another window
start "TailLog" cmd /c "python tail_auto_reply_log.py"
pause
goto MENU
:PROCESAR_CORREOS
cls
echo ==================================================
echo  PROCESANDO CORREOS Y ENVIANDO WHATSAPPS
echo ==================================================
echo.
cd /d "%~dp0"
python auto_contact_neoauto.py
echo.
echo ==================================================
echo  Proceso completado
echo ==================================================
pause
goto MENU

:LISTENER
cls
echo ==================================================
echo  ACTIVANDO LISTENER (Monitoreo Continuo)
echo ==================================================
echo.
echo NOTA: Presiona Ctrl+C para detener el listener
echo.
cd /d "%~dp0"
python whatsapp_listener.py
echo.
echo ==================================================
echo  Listener detenido
echo ==================================================
pause
goto MENU

:RESUMEN_IA
cls
echo ==================================================
echo  GENERANDO RESUMEN IA
echo ==================================================
echo.
cd /d "%~dp0"
python crm_brain.py
echo.
echo ==================================================
echo  Resumen generado
echo ==================================================
pause
goto MENU

:MARKETPLACE
cls
echo ==================================================
echo  ENVIAR LEAD DE MARKETPLACE
echo ==================================================
echo.
cd /d "%~dp0"
python enviar_lead_marketplace.py
echo.
echo ==================================================
echo  Proceso completado
echo ==================================================
pause
goto MENU

:ANALIZAR_LEAD
cls
echo ==================================================
echo  ANALIZADOR DE PRECIOS CON IA
echo ==================================================
echo.
set /p "URL_LEAD=Pega el Link del Auto (Neoauto): "
cd /d "%~dp0"
python "..\Autos.Richard.Gutierrez\analyze_lead.py" "%URL_LEAD%"
echo.
echo ==================================================
echo  Analisis completado
echo ==================================================
pause
goto MENU

:RESET_DB
cls
echo ==================================================
echo  RESET DATABASE (BORRADO TOTAL)
echo ==================================================
echo.
color 0C
cd /d "%~dp0"
python reset_full_db.py
color 0A
echo.
echo ==================================================
echo  Proceso finalizado
echo ==================================================
pause
goto MENU

:SALIR
cls
echo.
echo Hasta luego!
echo.
timeout /t 2 >nul
exit
