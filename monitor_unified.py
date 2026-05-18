#!/usr/bin/env python3
"""
Monitor Unificado de Workers: Combina estadísticas generales (Supabase) 
con estado detallado en tiempo real (Logs) de cada worker.
"""

import os
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables para Supabase
load_dotenv()

# Configuración
# Configuración
DEFAULT_LOG_FILE = "/home/richgutz/Scraper-Neoauto-ANTIGRAVITY/nohup_scraper_semanal.out"
LOG_FILE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG_FILE
# Support optional 2nd arg for num_workers
try:
    NUM_WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 8
except ValueError:
    NUM_WORKERS = 8
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def get_supabase_stats(supabase):
    try:
        # Total de URLs en la tabla semanal
        total_response = supabase.table('urls_autos_random').select('id', count='exact').execute()
        total_urls = total_response.count if total_response.count else 0
        
        # URLs no procesadas
        pending_response = supabase.table('urls_autos_random').select('id', count='exact').or_('procesado.is.null,procesado.eq.false').execute()
        pending_urls = pending_response.count if pending_response.count else 0
        
        processed_urls = total_urls - pending_urls
        progress_pct = (processed_urls / total_urls * 100) if total_urls > 0 else 0
        
        return {
            'total': total_urls,
            'processed': processed_urls,
            'pending': pending_urls,
            'progress_pct': progress_pct
        }
    except Exception as e:
        return {'error': str(e)}

def draw_progress_bar(percentage, width=50):
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

def parse_log_line(line):
    match = re.search(r'\[Worker-(\d+)\] (.*)', line)
    if match:
        return int(match.group(1)), match.group(2)
    return None, None

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Credenciales de Supabase no encontradas en .env")
        sys.exit(1)

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error conectando a Supabase: {e}")
        sys.exit(1)

    # Estado inicial
    # Estado inicial
    workers = {i: {'action': 'Esperando inicio...', 'time': time.time(), 'status': 'IDLE'} for i in range(1, NUM_WORKERS + 1)}
    system_phase = "Esperando logs..."
    recent_logs = []
    
    # Variables de velocidad
    last_processed = 0
    last_time = time.time()
    urls_per_minute = 0

    print("Iniciando monitor unificado...")
    time.sleep(1)

    try:
        # Abrir log
        with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            # Escanear fases en el historial reciente
            for line in lines[-2000:]: 
                line = line.strip()
                if not line: continue
                
                if "-->" in line:
                    system_phase = line.replace("-->", "").strip()
                
                w_id, msg = parse_log_line(line)
                if w_id:
                    workers[w_id]['action'] = msg[:70]
                    workers[w_id]['time'] = time.time() 
                    workers[w_id]['status'] = 'ACTIVE'
                else:
                    if len(line) > 5 and "---" not in line: 
                       recent_logs.append(line[:100])
                       if len(recent_logs) > 3: recent_logs.pop(0)

            while True:
                clear_screen()
                current_time = time.time()
                
                # 1. Actualizar estado desde Log
                while True:
                    line = f.readline()
                    if not line: break
                    line = line.strip()
                    if not line: continue

                    if "-->" in line:
                        system_phase = line.replace("-->", "").strip()
                    
                    w_id, msg = parse_log_line(line)
                    if w_id:
                        workers[w_id]['action'] = msg[:70]
                        workers[w_id]['time'] = current_time
                        workers[w_id]['status'] = 'ACTIVE'
                        if "ERROR" in msg or "Exception" in msg: workers[w_id]['status'] = 'ERROR'
                        if "finalizado" in msg.lower(): workers[w_id]['status'] = 'DONE'
                    else:
                         if len(line) > 5 and "---" not in line:
                            recent_logs.append(line[:100])
                            if len(recent_logs) > 3: recent_logs.pop(0)

                # 2. Obtener estadísticas Supabase
                stats = get_supabase_stats(supabase)
                
                # Calcular velocidad
                if 'processed' in stats:
                    if last_processed > 0 and stats['processed'] > last_processed:
                        time_diff = current_time - last_time
                        if time_diff > 0:
                            curr_speed = ((stats['processed'] - last_processed) / time_diff) * 60
                            urls_per_minute = (urls_per_minute * 0.7) + (curr_speed * 0.3) if urls_per_minute > 0 else curr_speed
                    
                    last_processed = stats['processed']
                    last_time = current_time
                
                # 3. MODO DE VISUALIZACIÓN
                print("=" * 80)
                print(f"  🔍 MONITOR UNIFICADO - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 80)
                
                print(f"\n  🚀 FASE ACTUAL: {system_phase}")
                print(f"  📝 Últimos Logs:")
                for log in recent_logs:
                    print(f"     > {log}")
                print("-" * 80)

                if 'error' in stats:
                    print(f"⚠️  Error Supabase: {stats['error']}")
                else:
                    eta = "Calculando..."
                    if urls_per_minute > 0 and stats['pending'] > 0:
                        mins_left = stats['pending'] / urls_per_minute
                        eta = f"{int(mins_left//60)}h {int(mins_left%60)}m"

                    print(f"\n  📊 PROGRESO SCRAPING:")
                    print(f"  {draw_progress_bar(stats['progress_pct'])}")
                    print(f"  Total: {stats['total']:,} | Procesadas: {stats['processed']:,} | Pendientes: {stats['pending']:,}")
                    print(f"  Velocidad: {urls_per_minute:.1f} URLs/min | ETA: {eta}")

                print("\n  👷 WORKERS (Solo activos durante fase de scraping):")
                print(f"  {'ID':<4} | {'ESTADO':<8} | {'ÚLTIMA ACCIÓN (Hace X seg)':<55}")
                print("  " + "-" * 75)
                
                active_workers = 0
                for i in range(1, NUM_WORKERS + 1):
                    w = workers[i]
                    elapsed = time.time() - w['time']
                    elapsed_str = f"{elapsed:.1f}s"
                    
                    status = w['status']
                    if status == 'ACTIVE' and elapsed > 60: status = 'STALLED?'
                    if status == 'ACTIVE': active_workers += 1
                    
                    print(f"  W-{i:<2} | {status:<8} | [{elapsed_str:<6}] {w['action']}")

                print("  " + "-" * 75)
                print(f"  Workers Activos: {active_workers}/{NUM_WORKERS}")
                print("\n  [Ctrl+C para salir]")
                
                time.sleep(2)

    except KeyboardInterrupt:
        print("\nMonitor detenido.")
    except FileNotFoundError:
        print(f"\nError: No se encuentra el archivo {LOG_FILE}")

if __name__ == "__main__":
    main()
