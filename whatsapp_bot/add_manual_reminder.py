
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

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

def main():
    print("\n" + "="*50)
    print("   NUEVO RECORDATORIO MANUAL (Link + Acción + Nombre)")
    print("="*50 + "\n")

    supabase = init_db()
    if not supabase:
        print("No se puede continuar sin conexión a BD.")
        input("Presiona Enter para salir...")
        return

    # 1. LINK (Mandatory)
    while True:
        link = input(">> Link del Auto (Obligatorio): ").strip()
        if link:
            break
        print("   ¡El link es obligatorio!")

    # 2. ACCION (Mandatory)
    while True:
        accion = input(">> Acción/Recordatorio (Obligatorio): ").strip()
        if accion:
            break
        print("   ¡La acción es obligatoria!")
        
    # 3. NOMBRE (Mandatory)
    while True:
        nombre_cliente = input(">> Nombre del Cliente (Obligatorio): ").strip()
        if nombre_cliente:
            break
        print("   ¡El nombre es obligatorio!")

    # 4. TELEFONO (Optional)
    phone = input(">> Teléfono del Cliente (Opcional, Enter para omitir): ").strip()

    # Preparar datos
    lead_phone = None
    
    if phone:
        # Si hay teléfono, asegurar que el Lead exista
        # Limpiar teléfono (solo números)
        clean_phone = "".join(filter(str.isdigit, phone))
        
        if len(clean_phone) >= 9: # Validación básica
            lead_phone = clean_phone
            try:
                # Verificar si existe
                res = supabase.table("crm_leads").select("phone").eq("phone", lead_phone).execute()
                
                if not res.data:
                    print(f"   -> El teléfono {lead_phone} es nuevo. Creando lead para '{nombre_cliente}'...")
                    # Crear Lead con el nombre proporcionado
                    lead_data = {
                        "phone": lead_phone,
                        "name": nombre_cliente,
                        "status": "NEW",
                        "lead_type": "BUYER", # Asumimos comprador por defecto
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("crm_leads").insert(lead_data).execute()
                else:
                    # Opcional: Actualizar nombre si era "Unknown" o "Vendedor"
                    pass
            except Exception as e:
                print(f"   Error validando/creando lead: {e}")
                lead_phone = None # Fallback a null si falla
        else:
            print("   (Teléfono inválido, se omitirá)")
            lead_phone = None

    # Insertar Tarea
    # Incluimos el nombre en la descripción si no hay teléfono para identificarlo
    extra_info = f" [Cliente: {nombre_cliente}]" if not lead_phone else ""
    full_description = f"[MANUAL] {accion} | Link: {link}{extra_info}"
    
    task_data = {
        "lead_phone": lead_phone, # Puede ser None
        "task_type": "VENTA", # Valor por defecto
        "description": full_description,
        "priority": "MEDIUM",
        "status": "PENDING",
        "due_date": datetime.now().isoformat()
    }

    try:
        supabase.table("crm_tasks").insert(task_data).execute()
        print("\n" + "="*50)
        print(" ✅ RECORDATORIO GUARDADO EXITOSAMENTE")
        print("="*50)
    except Exception as e:
        print(f"\n❌ Error guardando tarea: {e}")

    print("\nPresiona Enter para volver al menú...")
    input()

if __name__ == "__main__":
    main()
