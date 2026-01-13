
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

def init_db():
    current_script_dir = Path(__file__).resolve().parent
    dotenv_path = current_script_dir / ".env"
    load_dotenv(dotenv_path)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def main():
    print("=" * 60)
    print("⚠️  ATENCION: BORRANDO TODA LA BASE DE DATOS CRM  ⚠️")
    print("=" * 60)
    print("Esta accion NO SE PUEDE DESHACER.")
    print("Se eliminaran:")
    print("  - Todos los contactos (LEADS)")
    print("  - Todas las conversaciones (MENSAJES)")
    print("  - Todas las tareas pendientes")
    print()
    
    confirm = input("ESTA SEGURO que quiere borrar toda la base de datos? (escribe 'SI' para confirmar): ")
    
    if confirm.strip() != "SI":
        print("\nOperacion cancelada por el usuario.")
        return

    supabase = init_db()
    
    try:
        # 1. Borrar Tareas (por FK)
        print("Eliminando TAREAS...")
        # Usamos un UUID vacio válido para la comparación
        zero_uuid = "00000000-0000-0000-0000-000000000000"
        supabase.table("crm_tasks").delete().neq("id", zero_uuid).execute()
        
        # 2. Borrar Mensajes
        print("Eliminando MENSAJES...")
        # crm_messages usualmente tiene ID entero (serial) o UUID. Probamos UUID primero.
        # Si falla, es porque es Serial (Integer). En ese caso neq 0 funciona. 
        # Pero el error anterior 'invalid input syntax for type uuid' confirma que es UUID.
        supabase.table("crm_messages").delete().neq("id", zero_uuid).execute()
        
        # 3. Borrar Leads
        print("Eliminando LEADS...")
        # Para leads el ID es "phone" (texto)
        supabase.table("crm_leads").delete().neq("phone", "0").execute()
        
        print("\n✅ BASE DE DATOS LIMPIA. Puedes empezar de cero.")
        
    except Exception as e:
        print(f"\n❌ Error durante el borrado: {e}")

if __name__ == "__main__":
    main()
