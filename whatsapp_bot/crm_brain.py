"""
CRM Brain (IA Analysis Agent)

Este script:
1. Conecta a Supabase y busca mensajes NO procesados (processed = FALSE).
2. Agrupa mensajes por Lead (Teléfono).
3. Construye una transcripción de la conversación.
4. Envía la transcripción a Claude 3.5 Sonnet para análisis de intención (Citas/Visitas).
5. Si detecta intención, crea una tarea en 'crm_tasks'.
6. Marca los mensajes como procesados.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import anthropic

# --- CONFIGURACIÓN ---
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY no encontrada en .env")
    exit()

# Init Clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_unprocessed_leads():
    """Obtiene una lista única de teléfonos que tienen mensajes sin procesar"""
    try:
        # Paso 1: Obtener IDs de mensajes no procesados
        # Limitamos a 50 mensajes para no saturar en una sola corrida
        response = supabase.table("crm_messages")\
            .select("lead_phone")\
            .eq("processed", False)\
            .limit(50)\
            .execute()
        
        # Extraer telefonos únicos y filtrar basura
        phones = set()
        for r in response.data:
            phone = r['lead_phone']
            # Ignorar mensajes de sistema (filtro especifico)
            # Aumentamos limite de longitud porque ahora usamos Nombres como ID, y pueden ser largos
            if "end-to-end encrypted" in phone.lower() or len(phone) > 100:
                continue
            phones.add(phone)
            
        return list(phones)
    except Exception as e:
        print(f"Error fetching unprocessed leads: {e}")
        return []

def get_conversation_transcript(phone):
    """Obtiene los últimos 20 mensajes de un lead para contexto"""
    try:
        response = supabase.table("crm_messages")\
            .select("*")\
            .eq("lead_phone", phone)\
            .order("timestamp", desc=True)\
            .limit(20)\
            .execute()
        
        # Reordenar cronológicamente (antiguo a nuevo)
        messages = sorted(response.data, key=lambda x: x['timestamp'])
        
        transcript = ""
        msg_ids = []
        
        for msg in messages:
            sender_label = "AGENTE" if msg['sender'] == 'ME' else "CLIENTE"
            transcript += f"[{msg['timestamp']}] {sender_label}: {msg['content']}\n"
            msg_ids.append(msg['id'])
            
        return transcript, msg_ids
    except Exception as e:
        print(f"Error building transcript for {phone}: {e}")
        return "", []

def analyze_intent(transcript):
    """Envía la transcripción a Claude para análisis"""
    
    system_prompt = """
    Eres el CEREBRO de Richard (Usuario/Agente). Analizas sus chats de WhatsApp.
    
    IDENTIDADES:
    - "AGENTE" = Richard (TÚ USUARIO). Es quien compra y vende autos.
    - "CLIENTE" = La otra persona en el chat (Vendedor o Comprador).
    
    TU MISION: Detectar TAREAS para Richard basándote en el estado de la negociación.
    
    ESCENARIOS:
    
    1. FOLLOW-UP DE COMPRA (Richard intenta comprar):
       - Richard ("AGENTE") envió oferta y NO hay respuesta -> ACCION: "Esperar respuesta" (NO crear tarea urgente).
       - Cliente ("CLIENTE") aceptó oferta o propuso cita -> ACCION: "Agendar/Confirmar".
       - Cliente ("CLIENTE") dijo "está disponible" -> ACCION: "Pedir cita para ver auto".
       
    2. FOLLOW-UP DE VENTA (Richard intenta vender):
       - Cliente ("CLIENTE") pregunta "¿dónde se ve?" -> ACCION: "Responder con dirección".
       - Cliente ("CLIENTE") pide cita -> ACCION: "Agendar cita".
       - Cliente ("CLIENTE") muestra interés -> ACCION: "Hacer seguimiento".
    
    REGLAS IMPORTANTES:
    - **REGLA DE ORO**: Si Richard ("AGENTE") inicia la conversación con frases como "Hola [Nombre], vi tu auto...", "Hola, aún tienes el auto...", o similar, ENTOCES ES UNA INTENCIÓN DE **COMPRA** (Richard quiere comprar).
    - Si el mensaje inicial es de Richard expresando interés en un auto de Neoauto/Marketplace -> TIPO: "COMPRA".
    - Si Richard ("AGENTE") fue el último en hablar y propuso algo, la tarea suele ser "Esperar respuesta" (Priority LOW), a menos que hayan pasado días.
    - NO sugieras "Responder a Richard" (Richard eres tú). Sugiere "Responder al cliente".
    - Si solo preguntan precio/año/detalles técnicos SIN mostrar intención de ver/comprar → NO detectar
    - Si ya confirmaron cita → SÍ detectar para asegurar seguimiento
    - Prioridad HIGH si mencionan fecha específica o urgencia
    - Prioridad MEDIUM si muestran interés pero sin fecha
    - Prioridad LOW si solo preguntan disponibilidad
    
    OUTPUT FORMAT (JSON):
    {
        "detected": boolean,
        "type": "COMPRA" | "VENTA" | null,
        "summary": "Resumen breve de la intención",
        "priority": "HIGH" | "MEDIUM" | "LOW",
        "suggested_action": "Acción específica recomendada para Richard",
        "suggested_date": "YYYY-MM-DD HH:MM:SS" (si mencionan fecha, sino null)
    }
    """
    
    user_message = f"""
    Analiza esta conversación:\n\n{transcript}
    \n\nResponde SOLO con el JSON.
    """
    
    try:
        message = client.messages.create(
            # Usando Haiku (modelo ligero y rapido) por compatibilidad
            model="claude-3-haiku-20240307",
            max_tokens=400,  # Aumentado para incluir más campos
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        # Extraer JSON del texto (a veces Claude incluye explícitamente ```json ... ```)
        content = message.content[0].text
        # Limpieza básica por si viene con markdown
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
        
    except Exception as e:
        print(f"Error calling Claude: {e}")
        return None

def main():
    print("=" * 70)
    print("   CEREBRO IA - ANALISIS DE CONVERSACIONES")
    print("=" * 70)
    print()
    
    leads = get_unprocessed_leads()
    print(f"Conversaciones pendientes de analizar: {len(leads)}")
    print()
    
    if not leads:
        print("No hay conversaciones nuevas para analizar.")
        print("Ejecuta primero la opcion 2 (Listener) para capturar mensajes.")
        return
    
    # Estadísticas
    total_analyzed = 0
    tasks_created = 0
    tasks_compra = 0
    tasks_venta = 0
    tasks_high = 0
    tasks_medium = 0
    tasks_low = 0
    
    # Buscar nombres de los leads
    leads_map = {}
    if leads:
        try:
            response = supabase.table("crm_leads").select("phone, name").in_("phone", leads).execute()
            for r in response.data:
                leads_map[r['phone']] = r.get('name', 'Desconocido')
        except Exception as e:
            print(f"Error fetching lead names: {e}")

    print("Analizando conversaciones con Claude 3 Haiku...")
    print("-" * 70)
    print()
    
    for phone in leads:
        total_analyzed += 1
        lead_name = leads_map.get(phone, "Desconocido")
        print(f"{total_analyzed}. Lead: {lead_name} ({phone})")
        
        transcript, msg_ids = get_conversation_transcript(phone)
        if not transcript:
            print("   (Sin mensajes para analizar)\n")
            continue
        
        analysis = analyze_intent(transcript)
        
        if analysis:
            if analysis.get("detected"):
                tasks_created += 1
                task_type = analysis.get("type", "VENTA")
                priority = analysis.get("priority", "MEDIUM")
                summary = analysis.get("summary", "Sin resumen")
                action = analysis.get("suggested_action", "Hacer follow-up")
                
                # Contadores
                if task_type == "COMPRA":
                    tasks_compra += 1
                else:
                    tasks_venta += 1
                
                if priority == "HIGH":
                    tasks_high += 1
                elif priority == "MEDIUM":
                    tasks_medium += 1
                else:
                    tasks_low += 1
                
                # Mostrar resultado
                print(f"   TAREA DETECTADA: {task_type} - Prioridad {priority}")
                print(f"   Resumen: {summary}")
                print(f"   Accion recomendada: {action}")
                
                # Crear Tarea
                task_data = {
                    "lead_phone": phone,
                    "task_type": task_type,
                    "description": f"[{task_type}] {summary} | Accion: {action}",
                    "priority": priority,
                    "status": "PENDING",
                    "due_date": analysis.get("suggested_date") or datetime.now().isoformat()
                }
                try:
                    supabase.table("crm_tasks").insert(task_data).execute()
                    print(f"   -> Tarea guardada en BD")
                except Exception as e:
                    print(f"   ERROR guardando tarea: {e}")
            else:
                print("   (Sin intención de follow-up detectada)")
        else:
            print("   (Error en análisis IA)")
        
        # Marcar mensajes como procesados
        if msg_ids:
            try:
                supabase.table("crm_messages")\
                    .update({"processed": True})\
                    .in_("id", msg_ids)\
                    .execute()
                print(f"   -> {len(msg_ids)} mensajes marcados como procesados")
            except Exception as e:
                print(f"   ERROR actualizando mensajes: {e}")
        
        print()
    
    # RESUMEN FINAL
    print("=" * 70)
    print("   RESUMEN DEL ANALISIS")
    print("=" * 70)
    print()
    print(f"Conversaciones analizadas: {total_analyzed}")
    print(f"Tareas creadas: {tasks_created}")
    print()
    
    if tasks_created > 0:
        print("DESGLOSE POR TIPO:")
        print(f"  - COMPRA (Richard compra del vendedor): {tasks_compra}")
        print(f"  - VENTA (Richard vende al comprador): {tasks_venta}")
        print()
        print("DESGLOSE POR PRIORIDAD:")
        print(f"  - HIGH (urgente): {tasks_high}")
        print(f"  - MEDIUM (normal): {tasks_medium}")
        print(f"  - LOW (baja): {tasks_low}")
        print()
        print("=" * 70)
        print("   PROXIMAS ACCIONES RECOMENDADAS")
        print("=" * 70)
        print()
        print("Revisa las tareas creadas en Supabase (tabla crm_tasks)")
        print("Las tareas HIGH requieren atencion inmediata.")
        print()
    else:
        print("No se detectaron intenciones de follow-up en las conversaciones.")
        print()
    
    print("Analisis completado.")

if __name__ == "__main__":
    main()

