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
    /* Tabs Corporativos */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1;
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
</style>
""", unsafe_allow_html=True)


# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
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
st.title("CRM NeoAuto")
st.markdown("Gestión del pipeline de compras.")
st.divider()

# --- CARGA DE DATOS ---
with st.spinner("Cargando contactos..."):
    all_leads = fetch_leads()

if not all_leads:
    st.info("No hay contactos en la base de datos.")
    st.stop()

df = pd.DataFrame(all_leads)

# Pestañas Superiores (Sin emojis)
tabs = st.tabs(["WhatsApp", "Citas", "Visitas", "Caidos", "Comprados", "Vendidos"])

for tab, estado in zip(tabs, ESTADOS):
    with tab:
        state_df = df[df["estado_embudo"] == estado] if not df.empty else pd.DataFrame()
        st.subheader(f"{estado} ({len(state_df)})")
        
        if state_df.empty:
            st.write("Sin contactos en esta etapa.")
            continue
            
        # Preparar Grilla
        grid_data = []
        for index, row in state_df.iterrows():
            tel = str(row['telefono_whatsapp']).replace("+51", "").replace(" ", "")
            grid_data.append({
                "Seleccionar": False,
                "Vendedor": row['nombre_vendedor'] or "N/A",
                "WhatsApp": f"https://wa.me/51{tel}" if tel and tel != "None" else None,
                "Vehiculo": row['url'],
                "Fecha": row['fecha_actualizacion'][:10],
                "_raw_url": row['url']
            })
            
        grid_df = pd.DataFrame(grid_data)
        
        # Grid Maestro
        edited_df = st.data_editor(
            grid_df,
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn("Sel.", required=True),
                "WhatsApp": st.column_config.LinkColumn("WhatsApp", display_text="Chat"),
                "Vehiculo": st.column_config.LinkColumn("NeoAuto", display_text="Aviso"),
                "_raw_url": None
            },
            hide_index=True,
            use_container_width=True,
            key=f"grid_v40_{estado}"
        )
        
        seleccionados = edited_df[edited_df["Seleccionar"] == True]
        
        if not seleccionados.empty:
            target_url = seleccionados.iloc[0]["_raw_url"]
            lead_row = state_df[state_df['url'] == target_url].iloc[0]
            lead = lead_row.to_dict()
            
            st.divider()
            
            # --- PANEL DE ACCIONES (ANCHO TOTAL) ---
            st.markdown(f"### Detalle: {lead.get('nombre_vendedor', 'N/A')}")
            
            # 1. Historial Compactado
            with st.expander("Ver Seguimiento de Actividad (Movimientos y Notas)", expanded=False):
                notas = lead.get('notas_actividad', {})
                if type(notas) is str:
                    try: notas = json.loads(notas)
                    except: notas = {"Error": "Formato invalido"}
                
                if not notas:
                    st.write("Sin actividad previa.")
                else:
                    for key, val in notas.items():
                        st.markdown(f"> **{key}**: {val}")
            
            # 2. Herramientas a Ancho Total
            st.markdown("#### Herramientas de Gestion")
            
            # Cita Calendar (Estado 2)
            if estado == "Estado 2: Cita Concertada":
                with st.expander("Agendar en Google Calendar", expanded=True):
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        c_date = st.date_input("Fecha", key=f"d_{lead['url']}")
                    with c_col2:
                        c_time = st.time_input("Hora", key=f"t_{lead['url']}")
                    c_mail = st.text_input("Email del invitado", placeholder="opcional@gmail.com", key=f"m_{lead['url']}")
                    
                    if st.button("Generar Link Maestro", key=f"btn_c_{lead['url']}"):
                        import urllib.parse
                        start = pd.to_datetime(f"{c_date} {c_time}")
                        end = start + pd.Timedelta(hours=1)
                        dates = f"{start.strftime('%Y%m%dT%H%M%S')}/{end.strftime('%Y%m%dT%H%M%S')}"
                        q = {"action": "TEMPLATE", "text": f"Revision Auto - {lead['nombre_vendedor']}", "dates": dates}
                        if c_mail: q["add"] = c_mail
                        link = f"https://calendar.google.com/calendar/u/0/render?{urllib.parse.urlencode(q)}"
                        st.markdown(f'''
                        <a href="{link}" target="_blank" style="background-color:#0068c9;color:white;padding:8px 16px;border-radius:4px;text-decoration:none;font-weight:bold;">
                        Lanzar Google Calendar
                        </a>
                        ''', unsafe_allow_html=True)
            
            # Notas y Movimiento en columnas compactas
            act_col1, act_col2 = st.columns(2)
            
            with act_col1:
                with st.expander("Agregar Nota Rapida"):
                    n_text = st.text_area("Nota:", key=f"area_{lead['url']}", height=100)
                    if st.button("Guardar Nota", key=f"save_{lead['url']}"):
                        if add_note_to_lead(lead['url'], notas, estado, n_text):
                            st.success("Guardado")
                            st.rerun()

            with act_col2:
                with st.expander("Cambiar de Estado", expanded=True):
                    next_s = st.selectbox("Mover a:", [e for e in ESTADOS if e != estado], key=f"sel_{lead['url']}")
                    motivo = st.text_input("Motivo/Resumen:", key=f"mot_{lead['url']}")
                    if st.button("Confirmar Cambio", type="primary", key=f"conf_{lead['url']}"):
                        if move_lead_state(lead['url'], estado, next_s, notas, motivo):
                            st.success("Actualizado")
                            st.rerun()
