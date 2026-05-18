
import sys
import os
from pathlib import Path

# Add gmail_sender to path to import logic
sys.path.append(str(Path(__file__).parent / "gmail_sender"))

try:
    from gmail_sender import autenticar_google
except ImportError:
    print("Error: Could not import gmail_sender. Check directories.")
    sys.exit(1)

def main():
    print("--- INICIANDO AUTENTICACIÓN GOOGLE ---")
    print("Si tu navegador no se abre automáticamente, copia el link que aparecerá abajo.")
    
    creds = autenticar_google()
    
    if creds and creds.valid:
        print("\n[EXITO] Autenticación completada. El archivo token.json ha sido creado.")
    else:
        print("\n[FALLO] No se pudo autenticar. Revisa la consola para errores.")

if __name__ == "__main__":
    main()
