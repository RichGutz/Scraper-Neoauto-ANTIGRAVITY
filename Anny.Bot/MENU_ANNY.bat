@echo off
TITLE Anny Bot - Asistente Inmobiliario
color 0D

:MENU
cls
echo ==================================================
echo    ANNY BOT - ASISTENTE INMOBILIARIO
echo ==================================================
echo.
echo  1. Iniciar Envio Masivo de WhatsApp
echo     (Lee Excel, detecta proyecto, adjunta PDF)
echo.
echo  2. Salir
echo.
echo ==================================================
echo.

set /p opcion="Elige una opcion [1-2]: "

if "%opcion%"=="1" goto INICIAR
if "%opcion%"=="2" goto SALIR

echo.
echo ERROR: Opcion invalida.
timeout /t 2 >nul
goto MENU

:INICIAR
cls
echo ==================================================
echo  INICIANDO BOT...
echo ==================================================
echo.
cd /d "%~dp0"
echo Iniciando Script Python...
python anny_bot_cli.py
echo.
echo ==================================================
echo  Proceso finalizado
echo ==================================================
pause
goto MENU

:SALIR
exit
