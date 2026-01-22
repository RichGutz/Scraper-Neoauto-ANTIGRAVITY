import os
import shutil
import subprocess
import time

def build_exe():
    print("=== INICIANDO CONSTRUCCIÓN DE ANNY BOT ===")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    # 1. Limpiar builds anteriores
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 2. Ejecutar PyInstaller
    # --onefile: crea un solo .exe
    # --name: nombre del ejecutable
    # --clean: limpiar cache
    # --hidden-import: asegurar que pandas y otros se incluyan
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--clean",
        "--name", "AnnyBot_v4",
        "--hidden-import", "pandas",
        "--hidden-import", "selenium",
        "--hidden-import", "webdriver_manager",
        "anny_bot_cli.py"
    ]
    
    # Excluir librerías pesadas no usadas
    excludes = [
        "matplotlib", "scipy", "torch", "transformers", "tensorflow", 
        "IPython", "PIL", "numpy" # Numpy a veces es dependency de pandas, cuidado. Dejemos numpy por si acaso.
    ]
    # Pandas necesita numpy, asi que NO excluyamos numpy.
    excludes = ["matplotlib", "scipy", "torch", "transformers", "tensorflow", "IPython", "PIL", "tkinter"]
    
    for exc in excludes:
        cmd.extend(["--exclude-module", exc])
    
    # Agregar icono si existe
    if os.path.exists("anny_bot_icon.ico"):
        cmd.extend(["--icon", "anny_bot_icon.ico"])
        
    print(f"Ejecutando: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    # 3. Organizar carpeta de lanzamiento (Release)
    release_dir = os.path.join(base_dir, "Release_AnnyBot")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    print(f"Creando carpeta de distribución: {release_dir}")
    
    # Copiar EXE
    exe_src = os.path.join(base_dir, "dist", "AnnyBot_v4.exe")
    exe_dst = os.path.join(release_dir, "AnnyBot_v4.exe")
    shutil.copy2(exe_src, exe_dst)
    
    # Copiar PDFS (YA NO SE USAN - LINKS INYECTADOS)
    # for file in os.listdir(base_dir):
    #     if file.lower().endswith(".pdf"):
    #         shutil.copy2(os.path.join(base_dir, file), os.path.join(release_dir, file))
    #         print(f"Copiado PDF: {file}")
            
    # Copiar Perfil de Chrome (si existe localmente o en el repo)
    profile_src_local = os.path.join(base_dir, "whatsapp_bot_profile")
    profile_src_repo = os.path.join(os.path.dirname(base_dir), "whatsapp_bot", "whatsapp_bot_profile")
    
    target_profile_dir = os.path.join(release_dir, "whatsapp_bot_profile")
    
    if os.path.exists(profile_src_local):
        print("Copiando perfil local...")
        # shutil.copytree(profile_src_local, target_profile_dir) # Puede ser muy pesado, mejor advertir
        # Para portabilidad real, deberíamos copiarlo. Pero suele ser enorme.
        # Vamos a crear la carpeta vacía para que el script sepa dónde ponerlo si no existe
        if not os.path.exists(target_profile_dir):
            os.makedirs(target_profile_dir)
        print("NOTA: Se ha creado la carpeta whatsapp_bot_profile vacía. El bot creará un perfil nuevo o el usuario debe copiar el suyo.")
    elif os.path.exists(profile_src_repo):
         if not os.path.exists(target_profile_dir):
            os.makedirs(target_profile_dir)
         print("NOTA: Se ha creado la estructura para el perfil.")

    # Crear BAT de lanzamiento
    bat_content = """@echo off
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
"""
    with open(os.path.join(release_dir, "MENU_ANNY.bat"), "w") as f:
        f.write(bat_content)
        
    print("=== CONSTRUCCIÓN COMPLETADA EXITOSAMENTE ===")
    print(f"Carpeta final: {release_dir}")

if __name__ == "__main__":
    try:
        build_exe()
    except Exception as e:
        print(f"ERROR FATAL: {e}")
        input("Presiona ENTER para cerrar...")
