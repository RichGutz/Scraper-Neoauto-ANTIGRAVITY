"""
Verificar datos guardados por el Listener en Supabase
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
    print("VERIFICAR DATOS DEL LISTENER EN SUPABASE")
    print("=" * 70)
    print()
    
    supabase = init_db()
    if not supabase:
        return
    
    # 1. Verificar Leads
    print("=" * 70)
    print("LEADS GUARDADOS:")
    print("=" * 70)
    try:
        leads = supabase.table("crm_leads").select("*").order("last_interaction", desc=True).limit(20).execute()
        
        if leads.data:
            print(f"\nTotal de leads recientes: {len(leads.data)}\n")
            for i, lead in enumerate(leads.data, 1):
                print(f"{i}. {lead.get('name', 'Sin nombre')} - {lead.get('phone', 'Sin teléfono')}")
                print(f"   Status: {lead.get('status', 'N/A')}")
                print(f"   Última interacción: {lead.get('last_interaction', 'N/A')}")
                if lead.get('car_url'):
                    print(f"   Auto: {lead.get('car_url')[:50]}...")
                print()
        else:
            print("No se encontraron leads.")
    except Exception as e:
        print(f"Error consultando leads: {e}")
    
    # 2. Verificar Mensajes
    print("=" * 70)
    print("MENSAJES GUARDADOS:")
    print("=" * 70)
    try:
        messages = supabase.table("crm_messages").select("*").order("timestamp", desc=True).limit(30).execute()
        
        if messages.data:
            print(f"\nTotal de mensajes recientes: {len(messages.data)}\n")
            
            # Agrupar por lead
            msgs_by_lead = {}
            for msg in messages.data:
                phone = msg.get('lead_phone', 'Desconocido')
                if phone not in msgs_by_lead:
                    msgs_by_lead[phone] = []
                msgs_by_lead[phone].append(msg)
            
            for phone, msgs in msgs_by_lead.items():
                print(f"Lead: {phone} ({len(msgs)} mensajes)")
                for msg in msgs[:5]:  # Mostrar solo los últimos 5
                    sender = msg.get('sender', 'N/A')
                    content = msg.get('content', 'Sin contenido')
                    timestamp = msg.get('timestamp', 'N/A')
                    emoji = "📩" if sender == "LEAD" else "📤"
                    print(f"  {emoji} [{sender}] {content[:60]}...")
                    print(f"     {timestamp}")
                print()
        else:
            print("No se encontraron mensajes.")
    except Exception as e:
        print(f"Error consultando mensajes: {e}")
    
    print("=" * 70)
    print("VERIFICACION COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
