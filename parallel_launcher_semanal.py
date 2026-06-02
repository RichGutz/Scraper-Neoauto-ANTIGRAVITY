#!/usr/bin/env python3
import subprocess
import sys
import time
from threading import Thread

# Configuration for Weekly Scraper
sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_TO_RUN = "extractores/4.DIARIO.SEMANAL.SCRAPER.NEOAUTO.SUPABASE.PARA.CRON.BETA.py"
NUM_INSTANCES = 7  # 7 workers in parallel

def stream_output(process, prefix):
    """Reads output from a subprocess and prints it to stdout with a prefix."""
    for line in iter(process.stdout.readline, ''):
        # Strip and print with worker prefix
        safe_line = line.strip()
        if safe_line:  # Only print non-empty lines
            print(f"[{prefix}] {safe_line}")
            sys.stdout.flush()
    process.stdout.close()

def main():
    print(f"--- Iniciando {NUM_INSTANCES} instancias paralelas de scraping semanal ---")
    print(f"--- Script: {SCRIPT_TO_RUN} ---")
    processes = []
    threads = []

    for i in range(1, NUM_INSTANCES + 1):
        print(f"--- Lanzando Worker-{i} ---")
        # Python -u forces unbuffered stdout, crucial for real-time logging
        cmd = [sys.executable, "-u", SCRIPT_TO_RUN]
        
        try:
            # Popen with pipes to capture output
            p = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True, 
                bufsize=1,  # Line buffered
                encoding='utf-8', 
                errors='replace'
            )
            processes.append(p)
            
            # Start a thread to stream output
            t = Thread(target=stream_output, args=(p, f"Worker-{i}"))
            t.daemon = True
            t.start()
            threads.append(t)
            
            print(f"✓ Worker-{i} iniciado (PID: {p.pid})")
            
            # Small delay between launches to avoid race conditions
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error iniciando Worker-{i}: {e}")

    print(f"\n--- {len(processes)} workers activos. Esperando finalización... ---\n")

    # Wait for all processes
    for i, p in enumerate(processes, 1):
        p.wait()
        print(f"--- Worker-{i} finalizado (exit code: {p.returncode}) ---")

    print("\n--- Todas las instancias han finalizado ---")

if __name__ == "__main__":
    main()
