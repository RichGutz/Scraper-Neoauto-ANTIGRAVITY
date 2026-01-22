@echo off
TITLE Anny Bot - Asistente Inmobiliario
color 0D

:MENU
cls
echo ==================================================
echo    ANNY BOT v4 - ASISTENTE INMOBILIARIO
echo ==================================================
echo.
echo  1. Iniciar Envio Masivo
echo  2. Salir
echo.
echo ==================================================
set /p opcion="Elige una opcion [1-2]: "

if "%opcion%"=="1" goto INICIAR
if "%opcion%"=="2" goto SALIR

echo Opcion invalida.
timeout /t 2 >nul
goto MENU

:INICIAR
cls
echo Iniciando Bot...
AnnyBot_v4.exe
pause
goto MENU

:SALIR
exit
