# 🕊️ Protocolo de Paz: Desarrollo Multiplataforma (Windows 10 ⇄ Linux Mint)
**Ubicación:** `Automatizacion_VPS_UNIFI/PEACE.WIN.LINUX.md`

Este documento establece las reglas y mejores prácticas para que cualquier desarrollador o agente de Inteligencia Artificial que edite este repositorio en **Windows 10 (Desarrollo)** o en la **ThinkPad T430s (Linux Mint de Producción)** no rompa la compatibilidad del sistema y pueda sincronizar cambios de forma limpia a través de Git.

---

## 🚨 El Problema Fundamental
Compartir el mismo repositorio de Git entre dos sistemas operativos causa conflictos recurrentes si se cometen los siguientes errores:
1. **Rutas fijas (hardcodeadas):** Usar separadores Windows `\` o rutas absolutas como `C:\Users\...` que no existen en Linux (`/home/...`).
2. **Saltos de línea corruptos (CRLF vs LF):** Guardar scripts de Bash `.sh` con formato de Windows (CRLF), lo cual provoca que Linux falle al intentar leer retornos de carro invisibles `\r`.
3. **Entornos virtuales quemados:** Guardar rutas absolutas de ejecutables de Python en scripts del repositorio.

---

## 🛠️ Las 4 Reglas de Convivencia (Peace Rules)

### Regla 1: Usar `pathlib` para Rutas Dinámicas y Portables
**Queda estrictamente prohibido** el uso de strings planos para definir rutas de archivos si estas se van a leer en ambos sistemas. Se debe usar siempre el módulo nativo `pathlib.Path`.

*   ❌ **Mal (Roto en Linux):**
    ```python
    ruta = "extractores\\4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.py"
    ```
*   ✅ **Bien (Portable en cualquier SO):**
    ```python
    from pathlib import Path
    
    # Obtiene la ruta de forma segura sin importar el separador
    BASE_DIR = Path(__file__).resolve().parent
    ruta = BASE_DIR / "extractores" / "4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.py"
    ```

---

### Regla 2: Configuración del Sistema en `.env` (Ignorado por Git)
Todo parámetro que cambie entre la máquina de Windows y la ThinkPad (ejecutables de Python, variables de entorno, directorios de salida locales) debe declararse en el archivo `.env` local en cada extremo.

> [!IMPORTANT]
> El archivo `.env` **nunca** se sube a Git (está en `.gitignore`). De esta forma, cada máquina mantiene su configuración local intacta.

*   **En Windows 10 (Desarrollo):**
    ```env
    PYTHON_EXEC="venv\Scripts\python.exe"
    PROJECT_DIR="C:\Users\rguti\Scraper.Neoauto"
    ```
*   **En la ThinkPad (Linux Mint - Producción):**
    ```env
    PYTHON_EXEC="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY/.venv/bin/python"
    PROJECT_DIR="/home/richgutz/Scraper-Neoauto-ANTIGRAVITY"
    ```

En Python, consume estas variables usando `os.getenv` o la librería `dotenv`:
```python
import os
from dotenv import load_dotenv

load_dotenv()
python_cmd = os.getenv("PYTHON_EXEC")
```

---

### Regla 3: Detección Dinámica del Sistema Operativo
Si un script de Python debe lanzar subprocesos o comandos del sistema operativo diferentes en cada entorno, debe detectar dinámicamente dónde está corriendo en lugar de tener dos versiones de código:

```python
import platform
import os

sistema = platform.system() # Retorna 'Windows' o 'Linux'

if sistema == "Windows":
    # Comando o comportamiento exclusivo de Windows
    os.system("cls")
else:
    # Comando o comportamiento exclusivo de Linux
    os.system("clear")
```

---

### Regla 4: Mantener Scripts de Linux con Saltos de Línea LF
Los scripts Bash (`.sh`) para Linux nunca deben guardarse con saltos de línea de Windows (CRLF). 

> [!TIP]
> Para evitar esto de forma definitiva, se configuró el archivo `.gitattributes` en la raíz del repositorio. Este archivo le ordena a Git **forzar siempre saltos de línea LF** en archivos de extensión `.sh` al momento de hacer checkout en cualquier sistema. No borres ni alteres `.gitattributes`.

---

## 🤖 Guía para Agentes de IA en la ThinkPad (Linux)
Si eres un agente de IA trabajando en la ThinkPad de producción:
1. **Antes de editar:** Ejecuta `git status` para verificar si hay cambios locales no confirmados por Richard.
2. **Si modificas código:** Asegúrate de que las rutas que agregues respeten la **Regla 1** (usa `pathlib`).
3. **No modifiques `.env` de producción:** Si necesitas una variable nueva, agrégala con un nombre genérico en `.env.example` y pídele a Richard que la agregue a su `.env` de Windows.
4. **Al finalizar:** Guarda los cambios en una rama de respaldo (ej. `funcional.WOL.dd.mm.yy`) y haz push. Nunca empujes directamente a `master` en producción si no estás 100% seguro de que el código corre también en Windows.
