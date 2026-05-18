#!/usr/bin/env python3
"""
Monitor de progreso para workers paralelos del scraper semanal.
Muestra estadísticas en tiempo real de las URLs procesadas.
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

def clear_screen():
    """Limpia la pantalla del terminal."""
    os.system('clear' if os.name != 'nt' else 'cls')

def get_stats(supabase):
    """Obtiene estadísticas de progreso desde Supabase."""
    try:
        # Total de URLs en la tabla semanal
        total_response = supabase.table('urls_autos_random').select('id', count='exact').execute()
        total_urls = total_response.count if total_response.count else 0
        
        # URLs no procesadas (procesado = false o null)
        pending_response = supabase.table('urls_autos_random').select('id', count='exact').or_('procesado.is.null,procesado.eq.false').execute()
        pending_urls = pending_response.count if pending_response.count else 0
        
        # URLs procesadas
        processed_urls = total_urls - pending_urls
        
        # Porcentaje de progreso
        progress_pct = (processed_urls / total_urls * 100) if total_urls > 0 else 0
        
        return {
            'total': total_urls,
            'processed': processed_urls,
            'pending': pending_urls,
            'progress_pct': progress_pct
        }
    except Exception as e:
        return {
            'error': str(e),
            'total': 0,
            'processed': 0,
            'pending': 0,
            'progress_pct': 0
        }

def draw_progress_bar(percentage, width=50):
    """Dibuja una barra de progreso."""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

def main():
    # Conectar a Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Variables de entorno SUPABASE_URL y SUPABASE_KEY no configuradas")
        sys.exit(1)
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("✓ Conectado a Supabase")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        sys.exit(1)
    
    # Variables para calcular velocidad
    last_processed = 0
    last_time = time.time()
    urls_per_minute = 0
    
    print("\n🚀 Iniciando monitor de workers...\n")
    time.sleep(2)
    
    try:
        while True:
            clear_screen()
            
            # Obtener estadísticas
            stats = get_stats(supabase)
            current_time = time.time()
            
            # Calcular velocidad de procesamiento
            if last_processed > 0:
                time_diff = current_time - last_time
                urls_diff = stats['processed'] - last_processed
                if time_diff > 0:
                    urls_per_minute = (urls_diff / time_diff) * 60
            
            last_processed = stats['processed']
            last_time = current_time
            
            # Calcular tiempo estimado restante
            if urls_per_minute > 0 and stats['pending'] > 0:
                minutes_remaining = stats['pending'] / urls_per_minute
                hours = int(minutes_remaining // 60)
                mins = int(minutes_remaining % 60)
                eta = f"{hours}h {mins}m"
            else:
                eta = "Calculando..."
            
            # Mostrar información
            print("=" * 70)
            print("  🔍 MONITOR DE WORKERS - SCRAPER SEMANAL")
            print("=" * 70)
            print(f"\n  Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\n  📊 PROGRESO GENERAL:")
            print(f"  {draw_progress_bar(stats['progress_pct'])}")
            print(f"\n  📈 ESTADÍSTICAS:")
            print(f"     Total de URLs:      {stats['total']:,}")
            print(f"     URLs procesadas:    {stats['processed']:,}")
            print(f"     URLs pendientes:    {stats['pending']:,}")
            print(f"\n  ⚡ VELOCIDAD:")
            print(f"     URLs/minuto:        {urls_per_minute:.1f}")
            print(f"     Tiempo estimado:    {eta}")
            print(f"\n  💾 Tabla monitoreada: urls_autos_random")
            print(f"  🔄 Actualización cada 5 segundos")
            print("\n" + "=" * 70)
            print("  Presiona Ctrl+C para salir")
            print("=" * 70)
            
            # Esperar antes de actualizar
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n✓ Monitor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
