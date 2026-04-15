@echo off
TITLE CRM NEOAUTO - DISPARador BOT ANNY
color 0b

echo =======================================================
echo    INICIANDO AUTOMATIZACION: GMAIL -^> WHATSAPP
echo =======================================================
echo.

:: Moverse a la carpeta del script
cd /d "%~dp0"

:: 1. Limpieza de procesos (Chrome y Brave)
echo [1/3] Limpiando sesiones de navegadores...
taskkill /F /IM chrome.exe /T >nul 2>&1
taskkill /F /IM brave.exe /T >nul 2>&1
taskkill /F /IM chromedriver.exe /T >nul 2>&1
timeout /t 2 >nul

:: 2. Ejecutar bot usando Python del sistema (Verificado)
echo [2/3] Lanzando procesamiento...
cd whatsapp_bot
python auto_contact_neoauto.py

echo.
echo =======================================================
echo    PROCESO COMPLETADO
echo =======================================================
pause
