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
        # 1. Obtener Leads base
        resp = supabase.table("crm_contactos").select("*").order("fecha_actualizacion", desc=True).execute()
        contacts = resp.data
        if not contacts: return []
        
        # 2. Obtener Detalles de Autos (para Marca, Modelo, Año, Distrito)
        urls = [c['url'] for c in contacts]
        # Dividir en chunks si son demasiados (Supabase limit)
        resp_details = supabase.table("autos_detalles").select("URL, Make, Model, Year, District").in_("URL", urls).execute()
        details = resp_details.data
        
        # 3. Merge en Pandas
        df_c = pd.DataFrame(contacts)
        df_d = pd.DataFrame(details)
        
        if not df_d.empty:
            # Renombrar para unir
            df_d = df_d.rename(columns={"URL": "url"})
            df_final = pd.merge(df_c, df_d, on="url", how="left")
        else:
            df_final = df_c
            for col in ["Make", "Model", "Year", "District"]: df_final[col] = "En Proceso"
            
        return df_final.to_dict('records')
    except Exception as e:
        st.error(f"Error conectando a DB: {e}")
        return []

def move_lead_state(url, current_state, new_state, notes_history, new_note_text):
    notes_history[new_state] = f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - Movido de {current_state}. {new_note_text}"
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
st.markdown("Gestion de leads y funnel de compras.")
st.divider()

# --- CARGA DE DATOS ---
with st.spinner("Sincronizando con Supabase..."):
    all_leads_data = fetch_leads()

if not all_leads_data:
    st.info("No hay contactos en la base de datos.")
    st.stop()

df = pd.DataFrame(all_leads_data)

# Pestañas Superiores (Sin emojis)
tabs = st.tabs(["WhatsApp", "Citas", "Visitas", "Caidos", "Comprados", "Vendidos"])

for tab, estado in zip(tabs, ESTADOS):
    with tab:
        state_df = df[df["estado_embudo"] == estado] if not df.empty else pd.DataFrame()
        st.subheader(f"{estado} ({len(state_df)})")
        
        if state_df.empty:
            st.write("Sin contactos en esta etapa.")
            continue
            
        # Preparar Grilla con datos enriquecidos
        grid_data = []
        for index, row in state_df.iterrows():
            tel = str(row.get('telefono_whatsapp', '')).replace("+51", "").replace(" ", "")
            marca = row.get('Make', 'N/A')
            modelo = row.get('Model', 'N/A')
            grid_data.append({
                "Seleccionar": False,
                "Vendedor": row.get('nombre_vendedor', 'N/A'),
                "Vehiculo": f"{marca} {modelo}".strip(),
                "Anio": row.get('Year', 'N/A'),
                "Distrito": row.get('District', 'N/A'),
                "Chat": f"https://wa.me/51{tel}" if tel and tel != "None" else None,
                "NeoAuto": row['url'],
                "Fecha": row['fecha_actualizacion'][:10],
                "_raw_url": row['url'],
                "_raw_notas": row.get('notas_actividad', {})
            })
            
        grid_df = pd.DataFrame(grid_data)
        
        # Grid Maestro Estilo Inandes
        edited_df = st.data_editor(
            grid_df,
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn("Sel.", required=True),
                "Chat": st.column_config.LinkColumn("WhatsApp", display_text="Abrir Chrome"),
                "NeoAuto": st.column_config.LinkColumn("Link", display_text="Ver Auto"),
                "Vehiculo": st.column_config.TextColumn("Marca/Modelo"),
                "_raw_url": None,
                "_raw_notas": None
            },
            hide_index=True,
            use_container_width=True,
            key=f"grid_v41_{estado}"
        )
        
        seleccionados = edited_df[edited_df["Seleccionar"] == True]
        
        if not seleccionados.empty:
            lead = seleccionados.iloc[0]
            st.divider()
            
            # --- PANEL DE HERRAMIENTAS (HORIZONTAL ULTRA-COMPACTO) ---
            st.markdown(f"#### Herramientas de Gestion: {lead['Vendedor']} ({lead['Vehiculo']})")
            
            # Layout de 3 columnas para acciones
            h_col1, h_col2, h_col3 = st.columns([1.2, 1.2, 1.5])
            
            with h_col1:
                # 1. Cambio de Estado
                with st.container():
                    st.write("**Mover de Etapa**")
                    next_s = st.selectbox("Seleccionar nuevo:", [e for e in ESTADOS if e != estado], key=f"mv_{lead['_raw_url']}")
                    motivo = st.text_input("Breve motivo:", key=f"mot_{lead['_raw_url']}")
                    if st.button("Confirmar Movimiento", type="primary", use_container_width=True, key=f"btn_mv_{lead['_raw_url']}"):
                        if move_lead_state(lead['_raw_url'], estado, next_s, lead['_raw_notas'], motivo):
                            st.success("Listo")
                            st.rerun()
            
            with h_col2:
                # 2. Agregar Nota Rapida
                with st.container():
                    st.write("**Notas del Lead**")
                    n_text = st.text_area("Escribir nota:", key=f"txt_{lead['_raw_url']}", height=68, placeholder="Seguimiento...")
                    if st.button("Guardar Nota", use_container_width=True, key=f"btn_n_{lead['_raw_url']}"):
                        if add_note_to_lead(lead['_raw_url'], lead['_raw_notas'], estado, n_text):
                            st.success("Guardado")
                            st.rerun()

            with h_col3:
                # 3. Agenda Calendar (Solo en Estado 2)
                if estado == "Estado 2: Cita Concertada":
                    st.write("**Agenda Calendar**")
                    c_col_a, c_col_b = st.columns(2)
                    with c_col_a: c_d = st.date_input("Fecha", key=f"cd_{lead['_raw_url']}")
                    with c_col_b: c_t = st.time_input("Hora", key=f"ct_{lead['_raw_url']}")
                    if st.button("Generar Enlace Calendar", use_container_width=True, key=f"btn_cal_{lead['_raw_url']}"):
                         import urllib.parse
                         start = pd.to_datetime(f"{c_d} {c_t}")
                         end = start + pd.Timedelta(hours=1)
                         dates = f"{start.strftime('%Y%m%dT%H%M%S')}/{end.strftime('%Y%m%dT%H%M%S')}"
                         q = {"action": "TEMPLATE", "text": f"Cita Auto - {lead['Vehiculo']}", "dates": dates}
                         link = f"https://calendar.google.com/calendar/u/0/render?{urllib.parse.urlencode(q)}"
                         st.markdown(f'<a href="{link}" target="_blank" style="display:block;text-align:center;background:#0068c9;color:white;padding:5px;border-radius:4px;text-decoration:none;">Lanzar Calendario</a>', unsafe_allow_html=True)
                else:
                    st.write("**Info Vehiculo**")
                    st.info(f"Año: {lead['Anio']} | Distrito: {lead['Distrito']}")
            
            # --- ZONA DE HISTORIAL (ABAJO DEL TODO) ---
            st.divider()
            st.markdown("##### Bitacora de Actividad")
            notas = lead['_raw_notas']
            if type(notas) is str: 
                try: notas = json.loads(notas)
                except: notas = {}
            
            if not notas:
                st.caption("No hay actividad registrada todavia.")
            else:
                for key, val in notas.items():
                    st.markdown(f"* **{key}**: {val}")
