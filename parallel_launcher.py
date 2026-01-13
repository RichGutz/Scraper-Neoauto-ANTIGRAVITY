import subprocess
import sys
import time
from threading import Thread

# Configuration
sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_TO_RUN = r"extractores\4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.SUPABASE.PARA.CRON.BETA.py"
NUM_INSTANCES = 6

def stream_output(process, prefix):
    """Reads output from a subprocess and prints it to stdout with a prefix, stripping non-ascii."""
    for line in iter(process.stdout.readline, ''):
        # Remove non-ascii characters to satisfy Windows console
        safe_line = line.encode('ascii', 'ignore').decode('ascii').strip()
        print(f"[{prefix}] {safe_line}")
        sys.stdout.flush()
    process.stdout.close()

def main():
    print(f"--- Iniciando {NUM_INSTANCES} instancias paralelas de scraping ---")
    processes = []
    threads = []

    for i in range(1, NUM_INSTANCES + 1):
        print(f"--- Intentando lanzar Worker-{i} ---")
        # Python -u forces unbuffered stdout, crucial for real-time logging
        cmd = [sys.executable, "-u", SCRIPT_TO_RUN]
        
        try:
            # Popen with pipes to capture output
            p = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, # Merge stderr into stdout
                text=True, 
                bufsize=1, # Line buffered
                encoding='utf-8', 
                errors='replace'
            )
            processes.append(p)
            
            # Start a thread to stream output
            t = Thread(target=stream_output, args=(p, f"Worker-{i}"))
            t.daemon = True
            t.start()
            threads.append(t)
            
            print(f"Instancia {i} iniciada (PID: {p.pid})")
            
        except Exception as e:
            print(f"Error iniciando instancia {i}: {e}")

    # Wait for all processes
    for p in processes:
        p.wait()

    print("--- Todas las instancias han finalizado ---")

if __name__ == "__main__":
    main()
