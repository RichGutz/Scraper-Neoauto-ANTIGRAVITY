#!/usr/bin/env python3
import time
import re
import os
import sys
from datetime import datetime

LOG_FILE = "/home/richgutz/Scraper-Neoauto-ANTIGRAVITY/nohup_scraper_semanal.out"
NUM_WORKERS = 8

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def parse_log_line(line):
    # Regex to capture [Worker-X] and the message
    match = re.search(r'\[Worker-(\d+)\] (.*)', line)
    if match:
        worker_id = int(match.group(1))
        message = match.group(2)
        return worker_id, message
    return None, None

def main():
    print("Iniciando monitor v2...")
    
    # Initialize status dict
    workers = {i: {'action': 'Esperando inicio...', 'time': time.time(), 'status': 'IDLE'} for i in range(1, NUM_WORKERS + 1)}
    
    try:
        # Open file in non-blocking mode essentially (using seek)
        with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            # Go to end of file initially to show only new updates? 
            # Or read last N lines? Better to read from end to catch up.
            # Actually, let's read the whole file once to populate current state, then tail.
            
            while True:
                line = f.readline()
                if line:
                    w_id, msg = parse_log_line(line)
                    if w_id:
                        workers[w_id]['action'] = msg[:80] # Truncate active message
                        workers[w_id]['time'] = time.time()
                        workers[w_id]['status'] = 'ACTIVE'
                        if "ERROR" in msg or "Exception" in msg:
                             workers[w_id]['status'] = 'ERROR'
                        if "finalizado" in msg.lower():
                             workers[w_id]['status'] = 'DONE'
                else:
                    # EOF reached, print status and wait
                    clear_screen()
                    print(f"=== MONITOR DE WORKERS v2 - {datetime.now().strftime('%H:%M:%S')} ===")
                    print(f"Log: {LOG_FILE}\n")
                    
                    print(f"{'ID':<4} | {'ESTADO':<8} | {'ÚLTIMA ACCIÓN (Hace X seg)':<50}")
                    print("-" * 70)
                    
                    active_count = 0
                    for i in range(1, NUM_WORKERS + 1):
                        info = workers[i]
                        elapsed = time.time() - info['time']
                        elapsed_str = f"{elapsed:.1f}s"
                        
                        status_color = ""
                        if info['status'] == 'ACTIVE':
                            if elapsed > 120: # Stalled?
                                info['status'] = 'STALLED?'
                            else:
                                active_count += 1
                        
                        row = f"W-{i:<2} | {info['status']:<8} | {elapsed_str:<6} | {info['action']}"
                        print(row)
                    
                    print("-" * 70)
                    print(f"Workers Activos: {active_count}/{NUM_WORKERS}")
                    print("Control+C para salir")
                    
                    time.sleep(1) # Refresh rate

    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo de log {LOG_FILE}")
    except KeyboardInterrupt:
        print("\nMonitor detenido.")

if __name__ == "__main__":
    main()
