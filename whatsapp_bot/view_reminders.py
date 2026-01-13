
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import textwrap

def init_db():
    try:
        current_script_dir = Path(__file__).resolve().parent
        dotenv_path = current_script_dir / ".env"
        load_dotenv(dotenv_path)
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print(f"ERROR: No se encontraron credenciales en {dotenv_path}")
            return None
            
        return create_client(url, key)
    except Exception as e:
        print(f"Error conectando a DB: {e}")
        return None


def mostrar_detalle(task, supabase):
    """Muestra todos los detalles de una tarea y permite borrarla"""
    print("\n" + "="*80)
    print(f"   DETALLE DEL RECORDATORIO")
    print("="*80)
    print(f"   ID interno: {task.get('id')}")
    print(f"   Creado:     {task.get('created_at')}")
    print(f"   Prioridad:  {task.get('priority')}")
    print(f"   Estado:     {task.get('status')}")
    print(f"   Tel. Lead:  {task.get('lead_phone') or 'N/A'}")
    print("-" * 80)
    print("   DESCRIPCIÓN:")
    
    desc = task.get('description', '')
    # Wrap text para lectura
    print(textwrap.fill(desc, width=76, initial_indent='   ', subsequent_indent='   '))
    print("\n" + "="*80)
    
    accion = input("Presiona Enter para volver a la lista, o escribe 'BORRAR' para eliminar: ").strip()
    
    if accion.upper() == "BORRAR":
        try:
            confirm = input("¿Estás seguro? Escribe 'SI' para confirmar: ").strip()
            if confirm.upper() == "SI":
                supabase.table("crm_tasks").delete().eq("id", task.get('id')).execute()
                print("\n   ✅ Tarea eliminada correctamente.")
                input("Presiona Enter para continuar...")
        except Exception as e:
            print(f"\n   ❌ Error eliminando tarea: {e}")
            input("Presiona Enter para continuar...")

def main():
    supabase = init_db()
    if not supabase:
        print("No se puede continuar sin conexión a BD.")
        input("Presiona Enter para salir...")
        return

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "="*90)
        print("   RECORDATORIOS PENDIENTES (CRM TASKS)")
        print("="*90 + "\n")

        try:
            # Obtener tareas pendientes
            response = supabase.table("crm_tasks")\
                .select("*")\
                .eq("status", "PENDING")\
                .order("created_at", desc=True)\
                .execute()
            
            tasks = response.data
            
            if not tasks:
                print("   (No hay recordatorios pendientes)")
                print("\n   Presiona Enter para salir...")
                input()
                break
            else:
                # Cabecera con Numeración
                print(f"   {'#':<3} | {'PRIORIDAD':<10} | {'FECHA':<11} | {'DESCRIPCION'}")
                print("   " + "-"*85)
                
                # Mapa temporal para selección por índice
                task_map = {}
                
                for idx, t in enumerate(tasks, 1):
                    task_map[idx] = t
                    prio = t.get('priority', 'MEDIUM')
                    created = t.get('created_at', '')[:10]
                    desc = t.get('description', '')
                    
                    if len(desc) > 60:
                        desc = desc[:57] + "..."
                        
                    print(f"   {idx:<3} | {prio:<10} | {created:<11} | {desc}")
                
                print("\n" + "-"*90)
                seleccion = input("   Escribe el NÚMERO para ver detalle (ZOOM) o 0/Enter para salir: ").strip()
                
                if not seleccion or seleccion == "0":
                    break
                
                if seleccion.isdigit():
                    idx_sel = int(seleccion)
                    if idx_sel in task_map:
                        mostrar_detalle(task_map[idx_sel], supabase)
                    else:
                        print("   Número inválido.")
                        input("Presiona Enter...")
                else:
                    print("   Entrada inválida.")
                    input("Presiona Enter...")

        except Exception as e:
            print(f"\nError obteniendo tareas: {e}")
            input("Presiona Enter para salir...")
            break

if __name__ == "__main__":
    main()
