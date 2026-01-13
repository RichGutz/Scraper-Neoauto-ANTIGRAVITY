import time
import sys
import os

LOG_FILE = "scraper_sequence.log"

def tail():
    print("--- MONITOR DE LOGS (Python Safer Version) ---")
    print(f"Leyendo: {LOG_FILE}")
    print("----------------------------------------------")
    
    # Wait for file to be created if it doesn't exist
    while not os.path.exists(LOG_FILE):
        time.sleep(1)
        
    with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
        while True:
            line = f.readline()
            if line:
                # Remove non-ascii characters
                safe_line = line.encode('ascii', 'ignore').decode('ascii').strip()
                print(safe_line)
                if "SECUENCIA COMPLETADA" in safe_line:
                    print("\n")
                    print("========================================")
                    print("   PROCESO TERMINADO CON EXITO")
                    print("   Cerrando monitor en 5 segundos...")
                    print("========================================")
                    time.sleep(5)
                    sys.exit(0)
            else:
                time.sleep(0.5)

if __name__ == "__main__":
    try:
        tail()
    except KeyboardInterrupt:
        print("\nMonitor detenido por usuario.")
        sys.exit()
