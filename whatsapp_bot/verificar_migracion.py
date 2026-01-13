"""
Verificar que la migración SQL se ejecutó correctamente
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

def init_db():
    """Inicializar conexión a Supabase"""
    try:
        current_script_dir = Path(__file__).resolve().parent
        dotenv_path = current_script_dir / ".env"
        
        load_dotenv(dotenv_path)
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print(f"ERROR: No se encontraron credenciales en {dotenv_path}")
            return None
            
        print(f"Conectando a Supabase...")
        return create_client(url, key)
    except Exception as e:
        print(f"Error conectando a DB: {e}")
        return None

def main():
    print("=" * 70)
    print("VERIFICAR MIGRACION DE ESQUEMA CRM")
    print("=" * 70)
    print()
    
    supabase = init_db()
    if not supabase:
        return
    
    # Verificar que las nuevas columnas existen consultando un lead
    print("Verificando columna 'lead_type' en crm_leads...")
    try:
        result = supabase.table("crm_leads").select("phone, name, lead_type").limit(5).execute()
        
        if result.data:
            print("✅ Columna 'lead_type' existe y funciona correctamente\n")
            print("Primeros 5 leads con lead_type:")
            for lead in result.data:
                print(f"  - {lead.get('name', 'Sin nombre')} ({lead.get('phone', 'N/A')}): {lead.get('lead_type', 'N/A')}")
            print()
        else:
            print("⚠️  No hay leads en la tabla para verificar")
    except Exception as e:
        print(f"❌ ERROR: La columna 'lead_type' no existe o hay un problema: {e}\n")
    
    # Verificar columnas en crm_tasks
    print("Verificando columnas 'task_type' y 'priority' en crm_tasks...")
    try:
        result = supabase.table("crm_tasks").select("lead_phone, task_type, priority").limit(5).execute()
        
        if result.data:
            print("✅ Columnas 'task_type' y 'priority' existen y funcionan correctamente\n")
            print("Primeras 5 tareas con task_type y priority:")
            for task in result.data:
                print(f"  - Lead: {task.get('lead_phone', 'N/A')} | Tipo: {task.get('task_type', 'N/A')} | Prioridad: {task.get('priority', 'N/A')}")
            print()
        else:
            print("⚠️  No hay tareas en la tabla para verificar (esto es normal si no has creado tareas aún)\n")
    except Exception as e:
        print(f"❌ ERROR: Las columnas no existen o hay un problema: {e}\n")
    
    print("=" * 70)
    print("VERIFICACION COMPLETADA")
    print("=" * 70)
    print()
    print("Si ves ✅ en ambas verificaciones, la migración fue exitosa.")
    print("Ahora puedes usar:")
    print("  - lead_type: 'SELLER' (vendedor) o 'BUYER' (comprador)")
    print("  - task_type: 'COMPRA' o 'VENTA'")
    print("  - priority: 'HIGH', 'MEDIUM', 'LOW'")

if __name__ == "__main__":
    main()
