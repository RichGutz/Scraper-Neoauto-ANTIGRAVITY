import streamlit as st
import pandas as pd
import json
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="CRM NeoAuto",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS MODERNOS ---
st.markdown("""
<style>
    /* Asegurar que las tabs resalten visualmente y tengan 50% mas de amplitud en promedio */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1; /* Forzar el estiramiento 50% */
        height: 60px;
        font-size: 1rem;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 6px 6px 0px 0px;
        justify-content: center;
        padding: 15px 30px;
        transition: 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e5f1ff;
        border-bottom: 3px solid #0068c9;
        font-weight: bold;
    }
    /* Estilo para las cards de leads */
    .lead-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
        border-left: 4px solid #1a4e8c;
    }
    .lead-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 0.2rem;
    }
    .lead-info {
        font-size: 0.9rem;
        color: #4b5563;
    }
</style>
""", unsafe_allow_html=True)


# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    # Buscar el .env en la raiz del proyecto Scraper.Neoauto
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        # Fallback a Secrets si estamos en Streamlit Cloud (por si acaso)
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        
    return create_client(url, key)

supabase = init_connection()

# --- DEFINICIÓN DE ESTADOS ---
ESTADOS = [
    "Estado 1: 1er Contacto WhatsApp",
    "Estado 2: Cita Concertada",
    "Estado 3: Visita Ejecutada",
    "Estado 4: Descartado",
    "Estado 5: Comprado (Stock)",
    "Estado 6: Vendido"
]

# --- FUNCIONES DE BASE DE DATOS ---
def fetch_leads():
    try:
        response = supabase.table("crm_contactos").select("*").order("fecha_actualizacion", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error conectando a DB: {e}")
        return []

def move_lead_state(url, current_state, new_state, notes_history, new_note_text):
    # Actualizar el JSONB
    notes_history[new_state] = f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - Movido desde {current_state}. Nota: {new_note_text}"
    
    try:
        supabase.table("crm_contactos").update({
            "estado_embudo": new_state,
            "notas_actividad": notes_history,
            "fecha_actualizacion": pd.Timestamp.now().isoformat()
        }).eq("url", url).execute()
        return True
    except Exception as e:
        st.error(f"Falla al mover: {str(e)}")
        return False

def add_note_to_lead(url, notes_history, state, new_note_text):
    import uuid
    note_id = f"Nota-{str(uuid.uuid4())[:6]}"
    notes_history[f"{state}_{note_id}"] = f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - {new_note_text}"
    try:
        supabase.table("crm_contactos").update({
            "notas_actividad": notes_history
        }).eq("url", url).execute()
        return True
    except Exception as e:
        st.error(f"Falla agregando nota: {str(e)}")
        return False


# --- HEADER ---
st.title("🚗 CRM NeoAuto")
st.markdown("Gestión del Funnel de Compras.")
st.divider()

# --- CARGA DE DATOS ---
with st.spinner("Cargando pipeline..."):
    all_leads = fetch_leads()

if not all_leads:
    st.info("No hay contactos en la base de datos todavía. Procesa los correos de NeoAuto usando el bot para alimentarlo.")
    st.stop()

df = pd.DataFrame(all_leads)

# Pestañas Superiores
tabs = st.tabs(["💬 WhatsApp", "🗓️ Citas", "👁️ Visitas", "❌ Caídos", "🚗 Comprados", "💰 Vendidos"])

# Iterar sobre cada Estado y su Tab
for tab, estado in zip(tabs, ESTADOS):
    with tab:
        # Filtrar DF para este estado
        state_df = df[df["estado_embudo"] == estado] if not df.empty else pd.DataFrame()
        
        st.subheader(f"{estado} ({len(state_df)})")
        
        if state_df.empty:
            st.write("No hay contactos activos en esta etapa.")
            continue
        
        # Grid para Cards de Leads vs Visualizador
        col_list, col_viewer = st.columns([1, 1.5])
        
        with col_list:
            # Renderizamos lista compacta de leads
            st.markdown("##### Leads Activos")
            
            for index, row in state_df.iterrows():
                # Card
                url = row['url']
                nombre = row['nombre_vendedor'] or "Sin Nombre"
                telefono = row['telefono_whatsapp'] or "Sin Teléfono"
                fecha = row['fecha_actualizacion'][:10]
                
                with st.container():
                    st.markdown(f"""
                    <div class="lead-card">
                        <div class="lead-title">{nombre}</div>
                        <div class="lead-info">📱 {telefono} | 📅 {fecha}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botón para inspeccionar
                    if st.button(f"🔍 Inspeccionar Lead", key=f"btn_insp_{url}_{estado}"):
                        st.session_state.current_lead = row.to_dict()
                        
        with col_viewer:
            if 'current_lead' in st.session_state and st.session_state.current_lead['estado_embudo'] == estado:
                lead = st.session_state.current_lead
                st.markdown(f"### Detalles del Lead")
                st.write(f"**Vendedor:** {lead.get('nombre_vendedor', 'N/A')}")
                st.write(f"**WhatsApp:** +51{lead.get('telefono_whatsapp', 'N/A')} [Contactar](https://wa.me/51{lead.get('telefono_whatsapp', '')})")
                st.write(f"**Publicación:** [Ver Aviso NeoAuto]({lead.get('url', '#')})")
                
                if lead.get('id_evento_calendar'):
                    st.info(f"📅 Google Calendar Enlazado: {lead['id_evento_calendar']}")
                
                st.divider()
                st.markdown("#### 📝 Historial de Actividad (JSONB)")
                notas = lead.get('notas_actividad', {})
                if type(notas) is str:
                    try:
                        notas = json.loads(notas)
                    except:
                        notas = {"Error": "No se pudo formatear el JSON"}
                
                for key, note_text in notas.items():
                    st.markdown(f"> **{key}**: {note_text}")
                    
                st.divider()
                st.markdown("#### ⚙️ Acciones")
                
                # Accion NUEVA: Cita Calendar (Solo en Estado 2)
                if estado == "Estado 2: Cita Concertada":
                    with st.expander("📅 Generar Invitación de Google Calendar", expanded=True):
                        st.caption("Usa este panel para armar la invitación. Se abrirá la cuenta de tu navegador actual.")
                        cal_date = st.date_input("Fecha de cita", key=f"cal_d_{lead['url']}")
                        cal_time = st.time_input("Hora de cita", key=f"cal_t_{lead['url']}")
                        cal_mail = st.text_input("Correo electrónico del otro asistente (o cliente):", placeholder="ejemplo@gmail.com", key=f"cal_m_{lead['url']}")
                        cal_title = st.text_input("Título Evento", value=f"Revisión Auto - {lead.get('nombre_vendedor', 'Cliente')}", key=f"cal_title_{lead['url']}")
                        
                        if st.button("🔗 Crear Link Mágico de Calendar", key=f"cal_btn_{lead['url']}"):
                            import urllib.parse
                            start_dt = pd.to_datetime(f"{cal_date} {cal_time}")
                            end_dt = start_dt + pd.Timedelta(hours=1)
                            fmt = "%Y%m%dT%H%M%S"
                            dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
                            
                            query = {
                                "action": "TEMPLATE",
                                "text": cal_title,
                                "dates": dates_str,
                                "details": f"Contacto WhatsApp: +51{lead.get('telefono_whatsapp', '')}",
                            }
                            if cal_mail.strip():
                                query["add"] = cal_mail.strip()
                                
                            cal_link = f"https://calendar.google.com/calendar/u/0/render?{urllib.parse.urlencode(query)}"
                            
                            st.markdown(f'''
                            <a href="{cal_link}" target="_blank" style="background-color:#1a73e8;color:white;padding:10px 15px;border-radius:5px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:10px;">
                            👉 Clic AQUÍ para enviar la invitación en tu Google Calendar
                            </a>
                            ''', unsafe_allow_html=True)

                
                # Accion 1: Agregar Nota Rápida
                with st.expander("➕ Agregar Nota en este Estado"):
                    nueva_nota = st.text_area("Nota:", key=f"note_{lead['url']}")
                    if st.button("Guardar Nota", key=f"save_note_{lead['url']}"):
                        if add_note_to_lead(lead['url'], notas, estado, nueva_nota):
                            st.success("Nota agregada")
                            st.rerun()

                # Accion 2: Cambio de Estado
                with st.expander("➡️ Mover a otro Estado"):
                    avanzar_a = st.selectbox(
                        "Seleccionar nuevo estado:", 
                        [e for e in ESTADOS if e != estado],
                        key=f"move_sel_{lead['url']}"
                    )
                    motivo = st.text_input("Nota/Motivo del cambio:", key=f"motivo_{lead['url']}")
                    if st.button("Confirmar Movimiento", type="primary", key=f"confirm_move_{lead['url']}"):
                        if move_lead_state(lead['url'], estado, avanzar_a, notas, motivo):
                            st.success(f"Movido a {avanzar_a}")
                            # Limpiar seleccion para no mostrarlo en el estado viejo
                            del st.session_state.current_lead
                            st.rerun()
            else:
                st.info("👈 Selecciona 'Inspeccionar Lead' en un contacto para ver los detalles y actualizar su estado.")
