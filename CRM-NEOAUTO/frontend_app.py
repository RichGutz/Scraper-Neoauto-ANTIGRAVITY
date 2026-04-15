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
    /* Eliminar Margen Superior */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    header {visibility: hidden;}
    
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
        
        # 2. Obtener Detalles de Autos (para Marca, Modelo, Año, Distrito, Precio, KM)
        urls = [c['url'] for c in contacts]
        resp_details = supabase.table("autos_detalles_diarios").select("URL, Make, Model, Year, District, Price, Kilometers").in_("URL", urls).execute()
        details = resp_details.data
        
        # 3. Merge en Pandas
        df_c = pd.DataFrame(contacts)
        df_d = pd.DataFrame(details)
        
        if not df_d.empty:
            df_d = df_d.rename(columns={"URL": "url"})
            df_final = pd.merge(df_c, df_d, on="url", how="left")
        else:
            df_final = df_c
            for col in ["Make", "Model", "Year", "District", "Price", "Kilometers"]: df_final[col] = "N/A"
            
        return df_final.to_dict('records')
    except Exception as e:
        st.error(f"Error conectando a DB: {e}")
        return []

# --- ... (resto de funciones move_lead_state y add_note_to_lead sin cambios) ---

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
st.title("CRM NeoAuto - Gestion de leads y funnel de compras.")
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
            
            # Fix: Asegurar que Price sea float antes de formatear
            try:
                precio_val = float(row.get('Price', 0))
                precio_f = f"${precio_val:,.0f}" if precio_val > 0 else "N/A"
            except:
                precio_f = "N/A"
                
            # Fix: Asegurar que KM sea float antes de formatear
            try:
                km_val = float(row.get('Kilometers', 0))
                km_f = f"{km_val:,.0f} km" if km_val > 0 else "N/A"
            except:
                km_f = "N/A"
                
            grid_data.append({
                "Seleccionar": False,
                "Vendedor": row.get('nombre_vendedor', 'N/A'),
                "Vehiculo": f"{marca} {modelo}".strip(),
                "Precio": precio_f,
                "Anio": row.get('Year', 'N/A'),
                "Distrito": row.get('District', 'N/A'),
                "KM": km_f,
                "Chat": f"https://wa.me/51{tel}" if tel and tel != "None" else None,
                "NeoAuto": row['url'],
                "Fecha": row['fecha_actualizacion'][:10],
                "_raw_url": row['url'],
                "_raw_notas": row.get('notas_actividad', {}),
                "_raw_row": row.to_dict()
            })
            
        grid_df = pd.DataFrame(grid_data)
        
        # Grid Maestro Estilo Inandes
        edited_df = st.data_editor(
            grid_df,
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn("Sel.", required=True),
                "Chat": st.column_config.LinkColumn("WhatsApp", display_text="Chat"),
                "NeoAuto": st.column_config.LinkColumn("Link", display_text="Ver Auto"),
                "Vehiculo": st.column_config.TextColumn("Marca/Modelo"),
                "_raw_url": None, "_raw_notas": None, "_raw_row": None
            },
            hide_index=True,
            use_container_width=True,
            key=f"grid_v45_{estado}"
        )
        
        seleccionados = edited_df[edited_df["Seleccionar"] == True]
        
        if not seleccionados.empty:
            lead_sel = seleccionados.iloc[0]
            # Recuperamos el lead ORIGINAL del df base para evitar que sea un string
            lead_res = df[df["url"] == lead_sel["_raw_url"]]
            if lead_res.empty:
                st.error("No se pudo recuperar la informacion del lead.")
                st.stop()
            
            lead = lead_res.iloc[0]
            # Mapeamos para que lead se comporte como el diccionario que esperan las herramientas
            # pero manteniendo el acceso a las columnas enriquecidas
            n_history = lead.get('notas_actividad', {})
            if type(n_history) is str: 
                try: n_history = json.loads(n_history)
                except: n_history = {}
            
            st.divider()
            
            # --- PANEL DE HERRAMIENTAS (SIMETRIA V48 - FIX TYPE) ---
            st.markdown(f"#### Panel de Gestion: {lead.get('nombre_vendedor', 'N/A')} ({lead.get('Make', '')} {lead.get('Model', '')})")
            
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.write("**Movimiento de Estado**")
                n_state = st.selectbox("Cambiar a:", [e for e in ESTADOS if e != estado], key=f"mv_{lead['url']}")
                # Convertimos a text_area y ajustamos altura para nivelar
                n_reason = st.text_area("Breve motivo:", key=f"mot_{lead['url']}", height=88, placeholder="Ej: No contesta")
            
            with c2:
                st.write("**Bitacora / Notas**")
                # Altura aumentada para cubrir el espacio de 3 filas de la col3 (aprox 216px total)
                n_text = st.text_area("Nota de seguimiento:", key=f"txt_{lead['url']}", height=158, placeholder="Escribe aqui...")

            with c3:
                st.write("**Datos del Vehiculo**")
                # Micro-grilla 3x2
                m1, m2 = st.columns(2)
                
                # Función de ayuda interna para evitar crashes numéricos
                def safe_val(val, suffix="", is_price=False):
                    try:
                        # Si es N/A o vacío, retornar N/A
                        if not val or str(val).strip().upper() == "N/A": return "N/A"
                        # Limpiar y convertir
                        clean_num = float(str(val).replace("$", "").replace(",", "").replace("km", "").strip())
                        if is_price: return f"${clean_num:,.0f}"
                        return f"{clean_num:,.0f}{suffix}"
                    except:
                        return "N/A"

                with m1:
                    st.text_input("Marca:", value=lead.get('Make', 'N/A'), disabled=True, key=f"mk_{lead['url']}")
                    st.text_input("Precio:", value=safe_val(lead.get('Price'), is_price=True), disabled=True, key=f"pr_{lead['url']}")
                    st.text_input("Anio:", value=lead.get('Year', 'N/A'), disabled=True, key=f"yr_{lead['url']}")
                with m2:
                    st.text_input("Modelo:", value=lead.get('Model', 'N/A'), disabled=True, key=f"md_{lead['url']}")
                    st.text_input("Distrito:", value=lead.get('District', 'N/A'), disabled=True, key=f"dt_{lead['url']}")
                    st.text_input("KM:", value=safe_val(lead.get('Kilometers'), suffix=" km"), disabled=True, key=f"km_{lead['url']}")

            # FILA DE BOTONES
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Confirmar Movimiento", type="primary", use_container_width=True, key=f"btn_mv_{lead['url']}"):
                    if move_lead_state(lead['url'], estado, n_state, n_history, n_reason):
                        st.success("Estado actualizado")
                        st.rerun()
            with b2:
                if st.button("Guardar Nota", use_container_width=True, key=f"btn_n_{lead['url']}"):
                    if add_note_to_lead(lead['url'], n_history, estado, n_text):
                        st.success("Nota guardada")
                        st.rerun()
            with b3:
                st.markdown(f'''
                <a href="{lead['url']}" target="_blank" style="display:block;text-align:center;background:#0068c9;color:white;padding:8px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:0.85rem;">
                Ver Aviso en NeoAuto
                </a>
                ''', unsafe_allow_html=True)

            # --- ZONA DE HISTORIAL ---
            st.divider()
            st.markdown("##### Bitacora de Actividad (Historial)")
            notas = lead['_raw_notas']
            if type(notas) is str: 
                try: notas = json.loads(notas)
                except: notas = {}
            
            if not notas:
                st.caption("No hay actividad registrada todavia.")
            else:
                for key, val in notas.items():
                    st.markdown(f"* **{key}**: {val}")


            # --- ZONA DE HISTORIAL ---
            st.divider()
            st.markdown("##### Bitacora de Actividad (Historial)")
            notas = lead['_raw_notas']
            if type(notas) is str: 
                try: notas = json.loads(notas)
                except: notas = {}
            
            if not notas:
                st.caption("No hay actividad registrada todavia.")
            else:
                for key, val in notas.items():
                    st.markdown(f"* **{key}**: {val}")




