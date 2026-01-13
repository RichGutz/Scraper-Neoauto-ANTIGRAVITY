@echo off
echo Matando procesos zombies...
taskkill /F /IM chromedriver.exe /T
taskkill /F /IM python.exe /T
taskkill /F /IM powershell.exe /T
echo Todo limpio.
pause
