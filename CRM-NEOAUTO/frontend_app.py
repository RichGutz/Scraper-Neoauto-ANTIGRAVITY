import streamlit as st
import pandas as pd
import json
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import datetime
from google_auth import get_google_creds
from calendar_utils import create_calendar_event

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


# --- LOGIN SIMPLE ---
ALLOWED_USERS = ["anny", "rgutil", "annyred9", "rgutil@gmail.com", "annyred9@gmail.com"]
SECRET_PASS = "VivaLaVida2026$"

def login_ui():
    st.markdown("""<style>[data-testid="stSidebar"]{display:none;}</style>""", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        st.markdown("<h2 style='text-align:center;margin-top:20px'>CRM NeoAuto - Acceso Seguro</h2>", unsafe_allow_html=True)
        st.markdown("<h5 style='text-align:center;color:#888;font-weight:normal'>Introduce tus credenciales de acceso</h5><br>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Usuario o Correo")
            password = st.text_input("Contraseña", type="password")
            submit_btn = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit_btn:
                if username.strip().lower() in ALLOWED_USERS and password == SECRET_PASS:
                    st.session_state["user_info"] = {"email": username.lower(), "name": username.split("@")[0].capitalize()}
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o usuario no autorizado.")

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
    "Estado 4: Cerrado",
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

# --- FUNCIONES GYP ---

def fetch_gyp(lead_url):
    """Trae el registro de crm_gyp para un lead. Retorna dict o None."""
    try:
        res = supabase.table("crm_gyp").select("*").eq("lead_url", lead_url).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Error al leer GyP: {e}")
        return None

def save_gyp(lead_url, payload):
    """Upsert del registro GyP. Retorna True/False."""
    try:
        existing = supabase.table("crm_gyp").select("id").eq("lead_url", lead_url).execute()
        if existing.data:
            supabase.table("crm_gyp").update(payload).eq("lead_url", lead_url).execute()
        else:
            payload["lead_url"] = lead_url
            supabase.table("crm_gyp").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar GyP: {e}")
        return False

# --- FUNCIONES DE FLUJO ---

def move_lead_state(url, current_state, new_state, notes_history):
    notes_history[new_state] = f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - Movido de {current_state}."
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


def main_app():
    # --- HEADER ---
    st.title(f"CRM NeoAuto - Bienvenido {st.session_state.user_info.get('name', '')}")
    st.markdown(f"Usuario autenticado: `{st.session_state.user_info.get('email', '')}`")
    st.divider()

    if st.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    # --- CARGA DE DATOS ---
    with st.spinner("Sincronizando con Supabase..."):
        all_leads_data = fetch_leads()

    if not all_leads_data:
        st.info("No hay contactos en la base de datos.")
        st.stop()

    df = pd.DataFrame(all_leads_data)

    # Pestañas Superiores (Sin emojis)
    tabs = st.tabs(["WhatsApp", "Citas", "Visitas", "Cerrado", "Comprados", "Vendidos", "Analizador"])

    for tab, estado in zip(tabs[:-1], ESTADOS):
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
                    "Chat": f"https://wa.me/{tel}" if tel and tel != "None" else None,
                    "NeoAuto": row['url'],
                    "Fecha": str(row.get('fecha_actualizacion', ''))[:10] if row.get('fecha_actualizacion') else "N/A",
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
                    "Chat": st.column_config.LinkColumn("WhatsApp", display_text=r"(\d+)"),
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

                # --- PANEL DE HERRAMIENTAS ---
                st.markdown(f"#### Panel de Gestion: {lead.get('nombre_vendedor', 'N/A')} ({lead.get('Make', '')} {lead.get('Model', '')})")

                # Mostrar errores persistentes de calendario si existen
                if "calendar_error" in st.session_state:
                    st.error(f"Atencion: {st.session_state.calendar_error}")
                    if st.button("Entendido, limpiar error"):
                        del st.session_state.calendar_error
                        st.rerun()

                # ============================================================
                # PANEL GYP — solo para Estado 5: Comprado (Stock)
                # ============================================================
                if estado == "Estado 5: Comprado (Stock)":

                    gyp_data = fetch_gyp(lead['url'])
                    g = gyp_data or {}

                    bcol1, bcol2 = st.columns([4, 1])
                    with bcol1:
                        st.markdown("##### Ganancia y Perdida (GyP)")
                    with bcol2:
                        tc = st.number_input("T. Cambio (USD/PEN)", min_value=1.0, value=float(g.get("tipo_cambio", 3.4)), step=0.01, format="%.2f", key=f"tc_{lead['url']}")

                    # Encabezados (ajustados a 6 columnas con espaciadores para cajas angostas)
                    h1, h2, h_s1, h3, h_s2, h4 = st.columns([3, 1, 0.3, 1, 0.5, 1.5])
                    h1.markdown("**RUBRO**")
                    h2.markdown("**USD ($)**")
                    h3.markdown("**SOLES (S/)**")
                    h4.markdown("<div style='text-align:center;'>**TOTAL USD ($)**</div>", unsafe_allow_html=True)

                    st.markdown("<hr style='margin:0px'>", unsafe_allow_html=True)

                    rubros = [
                        ("Precio de Venta", "precio_venta"),
                        ("Precio de Compra", "precio_compra"),
                        ("Gastos Notariales", "notarial"),
                        ("Gastos Registrales", "registral"),
                        ("Pintura y Aros", "pintura_aros"),
                        ("Lavado", "lavado"),
                        ("Combustible", "gasolina"),
                        ("Cochera", "cochera"),
                        ("Mecanica", "mecanica"),
                        ("Llantas", "llantas"),
                        ("Publicidad NeoAuto", "neoauto"),
                        ("Cheque Gerencia", "cheque_gerencia"),
                        ("Intereses", "intereses")
                    ]

                    resultados_usd = {}

                    for label, key_name in rubros:
                        c1, c2, c_s1, c3, c_s2, c4 = st.columns([3, 1, 0.3, 1, 0.5, 1.5])
                        c1.write(label)
                        
                        k_usd = f"u_{key_name}_{lead['url']}"
                        k_pen = f"p_{key_name}_{lead['url']}"
                        
                        saved_val_usd = float(g.get(f"{key_name}_usd", 0) or 0)
                        
                        # Mutua exclusividad
                        current_usd = st.session_state.get(k_usd, saved_val_usd)
                        current_pen = st.session_state.get(k_pen, 0)
                        
                        disable_usd = (current_pen > 0)
                        disable_pen = (current_usd > 0)
                        
                        val_usd = c2.number_input("USD", min_value=0, value=int(saved_val_usd), step=10, label_visibility="collapsed", disabled=disable_usd, key=k_usd)
                        val_pen = c3.number_input("PEN", min_value=0, value=0, step=10, label_visibility="collapsed", disabled=disable_pen, key=k_pen)
                        
                        if val_usd > 0:
                            total_usd = val_usd
                        else:
                            total_usd = round(val_pen / tc, 2) if val_pen > 0 else 0
                            
                        # Resalte estetico y centrado de la columna Total
                        if key_name == "precio_venta":
                            c4.markdown(f"<div style='text-align:center; background-color:#e8f5e9; color:#1b5e20; padding:4px; border-radius:4px; font-weight:bold; border: 1px solid #c8e6c9;'>${total_usd:,.0f}</div>", unsafe_allow_html=True)
                        else:
                            c4.markdown(f"<div style='text-align:center; background-color:#ffebee; color:#b71c1c; padding:4px; border-radius:4px; border: 1px solid #ffcdd2;'>-${total_usd:,.0f}</div>", unsafe_allow_html=True)

                        resultados_usd[key_name] = total_usd

                    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)
                    
                    # Totales
                    total_ingresos = resultados_usd["precio_venta"]
                    total_costos = sum(resultados_usd[k] for k in resultados_usd if k != "precio_venta")
                    utilidad = total_ingresos - total_costos
                    margen_pct = (utilidad / total_ingresos * 100) if total_ingresos > 0 else 0.0

                    color = "green" if utilidad > 0 else "red"
                    st.markdown(f"<h5 style='text-align:right'>UTILIDAD NETA: <span style='color:{color}'>${utilidad:,.0f} ({margen_pct:.1f}%)</span></h5>", unsafe_allow_html=True)

                    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)
                    
                    col_com, col_btns = st.columns([3, 2])
                    with col_com:
                        # Extraer texto de comentarios, en BD es un JSONB
                        com_val = g.get("comentarios", {})
                        if isinstance(com_val, dict):
                            com_text = com_val.get("texto", "")
                        else:
                            com_text = str(com_val)
                        comentarios_txt = st.text_area("Comentarios:", value=com_text, height=85, label_visibility="collapsed", placeholder="Notas de GyP...", key=f"g_com_{lead['url']}")
                        
                    with col_btns:
                        if st.button("Guardar GyP", type="primary", use_container_width=True, key=f"btn_gyp_{lead['url']}"):
                            gyp_payload = {
                                "tipo_cambio": tc,
                                "utilidad_neta_usd": round(utilidad, 2),
                                "comentarios": {"texto": comentarios_txt} if comentarios_txt else {}
                            }
                            for _, key_name in rubros:
                                gyp_payload[f"{key_name}_usd"] = resultados_usd[key_name]
                                
                            if save_gyp(lead['url'], gyp_payload):
                                st.success("GyP guardado!")
                                st.rerun()

                        vendido_habilitado = total_ingresos > 0
                        if not vendido_habilitado:
                            st.caption("Ingresa Precio Venta para Vender.")
                        if st.button("Mover a Vendido", use_container_width=True, disabled=not vendido_habilitado, key=f"btn_vendido_{lead['url']}"):
                            if move_lead_state(lead['url'], estado, "Estado 6: Vendido", n_history):
                                st.success("Lead movido a Vendido.")
                                st.rerun()

                # ============================================================
                # PANEL ESTANDAR — todos los demas estados
                # ============================================================
                else:
                    c1, c2, c3 = st.columns(3)

                    with c1:
                        st.write("**Agenda de Visita**")
                        n_state = st.selectbox("Cambiar a:", [e for e in ESTADOS if e != estado], key=f"mv_{lead['url']}")
                        v_date = st.date_input("Fecha:", min_value=datetime.date.today(), key=f"vdate_{lead['url']}")
                        v_time = st.time_input("Hora:", value=datetime.time(10, 0), key=f"vtime_{lead['url']}")
                        v_loc  = st.text_input("Lugar/Direccion:", placeholder="Ej: Av. Primavera 123", key=f"vloc_{lead['url']}")

                    with c2:
                        st.write("**Bitacora / Notas**")
                        n_text = st.text_area("Nota de seguimiento:", key=f"txt_{lead['url']}", height=245, placeholder="Escribe aqui...")

                    with c3:
                        st.write("**Datos del Vehiculo**")
                        m1, m2 = st.columns(2)

                        def safe_val(val, suffix="", is_price=False):
                            try:
                                if not val or str(val).strip().upper() == "N/A": return "N/A"
                                clean_num = float(str(val).replace("$", "").replace(",", "").replace("km", "").strip())
                                if is_price: return f"${clean_num:,.0f}"
                                return f"{clean_num:,.0f}{suffix}"
                            except:
                                return "N/A"

                        with m1:
                            st.text_input("Marca:",  value=lead.get('Make', 'N/A'),     disabled=True, key=f"mk_{lead['url']}")
                            st.text_input("Precio:", value=safe_val(lead.get('Price'), is_price=True), disabled=True, key=f"pr_{lead['url']}")
                            st.text_input("Anio:",   value=lead.get('Year', 'N/A'),     disabled=True, key=f"yr_{lead['url']}")
                        with m2:
                            st.text_input("Modelo:",   value=lead.get('Model', 'N/A'),    disabled=True, key=f"md_{lead['url']}")
                            st.text_input("Distrito:", value=lead.get('District', 'N/A'), disabled=True, key=f"dt_{lead['url']}")
                            st.text_input("KM:",       value=safe_val(lead.get('Kilometers'), suffix=" km"), disabled=True, key=f"km_{lead['url']}")

                    # FILA DE BOTONES
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("Confirmar Movimiento", type="primary", use_container_width=True, key=f"btn_mv_{lead['url']}"):
                            if n_state == "Estado 2: Cita Concertada":
                                creds = get_google_creds()
                                if creds:
                                    vendedor   = lead.get('nombre_vendedor', 'Vendedor')
                                    telefono   = lead.get('telefono_whatsapp', 'S/T')
                                    auto_info  = f"{lead.get('Make', '')} {lead.get('Model', '')} {lead.get('Year', '')}".strip()
                                    event_title = f"Visita NeoAuto: {vendedor} - {telefono} - {auto_info}"
                                    start_dt   = datetime.datetime.combine(v_date, v_time)
                                    res = create_calendar_event(creds, event_title, v_loc, start_dt, vendedor)
                                    if "link" in res:
                                        st.success(f"Cita agendada: [Ver en Google Calendar]({res['link']})")
                                    else:
                                        st.error(f"Error de Calendar: {res.get('error', 'Desconocido')}")
                            if move_lead_state(lead['url'], estado, n_state, n_history):
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
                    notas = lead.get('notas_actividad', {})
                    if type(notas) is str:
                        try: notas = json.loads(notas)
                        except: notas = {}
                    if not notas:
                        st.caption("No hay actividad registrada todavia.")
                    else:
                        for key, val in notas.items():
                            st.markdown(f"* **{key}**: {val}")
            
            # --- WIDGET DE CALENDAR COMBINADO (SOLO EN PESTAÑA CITAS) ---
            if estado == "Estado 2: Cita Concertada":
                st.divider()
                st.markdown("### Disponibilidad Semanal (Anny + Rich)")
                
                # URL Combinada: Anny (annyred9@gmail.com) + Rich (rich@kaizencapital.pe)
                calendar_url = (
                    "https://calendar.google.com/calendar/embed?height=600&wkst=1&bgcolor=%23ffffff"
                    "&src=annyred9%40gmail.com&color=%23039BE5"
                    "&src=rich%40kaizencapital.pe&color=%23AD1457"
                    "&ctz=America%2FLima&mode=WEEK&hl=es"
                )
                
                import streamlit.components.v1 as components
                components.iframe(calendar_url, height=600, scrolling=True)

    with tabs[-1]:
        st.write("Analizador de Precio de Leads")
        c_url, c_btn = st.columns([5, 1])
        with c_url:
            url_input = st.text_input("URL", placeholder="Pega el enlace o deja en blanco para ingreso manual...", label_visibility="collapsed")
        with c_btn:
            buscar = st.button("Buscar / Extraer", type="primary", use_container_width=True)
            
        if "analyzer_data" not in st.session_state:
            st.session_state.analyzer_data = None
            
        if buscar:
            if url_input:
                resp = supabase.table("autos_detalles_diarios").select("*").eq("URL", url_input).execute()
                if resp.data:
                    data = resp.data[0]
                    st.session_state.analyzer_data = {
                        "Make": data.get("Make"),
                        "Model": data.get("Model"),
                        "Year": int(data.get("Year")) if data.get("Year") else 0,
                        "Price": float(data.get("Price")) if data.get("Price") else 0.0,
                        "Kilometers": int(data.get("Kilometers")) if data.get("Kilometers") else 0,
                        "Transmission": data.get("Transmission", "N/A")
                    }
                else:
                    st.session_state.analyzer_data = "MANUAL"
                    st.caption("Vehículo no encontrado en BD diaria. Ingrese datos manual:")
            else:
                st.session_state.analyzer_data = "MANUAL"
                
        if st.session_state.analyzer_data == "MANUAL":
            with st.form("manual_analysis_form"):
                # Todo en una sola fila minimalista
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 2, 1.5, 2, 2, 2, 2])
                with c1: m_make = st.text_input("Marca", label_visibility="collapsed", placeholder="Marca")
                with c2: m_model = st.text_input("Modelo", label_visibility="collapsed", placeholder="Modelo")
                with c3: m_year = st.number_input("Año", min_value=1990, value=2018, format="%d", label_visibility="collapsed")
                with c4: m_price = st.number_input("US$", min_value=0, value=10000, step=100, label_visibility="collapsed")
                with c5: m_km = st.number_input("KM", min_value=0, value=50000, step=1000, label_visibility="collapsed")
                with c6: m_trans = st.selectbox("Trans.", ["N/A", "Automática", "Mecánica"], label_visibility="collapsed")
                with c7: submit = st.form_submit_button("Calcular", use_container_width=True)
                
                if submit:
                    if m_make and m_model:
                        st.session_state.analyzer_data = {
                            "Make": m_make.strip().capitalize(),
                            "Model": m_model.strip().upper(),
                            "Year": m_year,
                            "Price": m_price,
                            "Kilometers": m_km,
                            "Transmission": m_trans
                        }
                        st.rerun()

        if isinstance(st.session_state.analyzer_data, dict):
            t_data = st.session_state.analyzer_data
            
            with st.spinner("..."):
                query = supabase.table("autos_detalles_diarios") \
                            .select("Price, Kilometers") \
                            .eq("Make", t_data['Make']) \
                            .ilike("Model", f"%{t_data['Model']}%") \
                            .eq("Year", t_data['Year'])
                
                resp = query.execute()
                df_m = pd.DataFrame(resp.data)
                
                if df_m.empty:
                    st.caption(f"Sin históricos para: {t_data['Make']} {t_data['Model']} {t_data['Year']}.")
                else:
                    df_m['Price'] = pd.to_numeric(df_m['Price'], errors='coerce')
                    df_m['Kilometers'] = pd.to_numeric(df_m['Kilometers'], errors='coerce')
                    df_m = df_m.dropna(subset=['Price'])
                    
                    med_price = df_m['Price'].median()
                    med_km = df_m['Kilometers'].median()
                    count = len(df_m)
                    
                    pct_diff = ((t_data['Price'] - med_price) / med_price) * 100 if med_price > 0 else 0
                    
                    color = "#28a745" if pct_diff < -5 else "#dc3545" if pct_diff > 5 else "#17a2b8"
                    verdict = "BUEN TRATO" if pct_diff < -5 else "MAL TRATO" if pct_diff > 5 else "TRATO JUSTO"
                    dif_text = f"Ahorro: ${(med_price - t_data['Price']):,.0f}" if pct_diff < -5 else f"Sobreprecio: ${(t_data['Price'] - med_price):,.0f}" if pct_diff > 5 else "Precio Acorde"
                    
                    html_compact = f"""
                    <div style="background-color: #f8f9fa; border-left: 4px solid {color}; padding: 8px 12px; border-radius: 4px; font-family: sans-serif; font-size: 13px; display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                        <div style="font-size: 12px; color: #555;"><b>{t_data['Make']} {t_data['Model']} {t_data['Year']}</b> (vs {count} un.)</div>
                        <div>
                            <span>Lead: <b>${t_data['Price']:,.0f}</b> ({t_data['Kilometers']:,.0f} km)</span> &nbsp;|&nbsp; 
                            <span style="color:#666;">Mercado: ${med_price:,.0f} ({med_km:,.0f} km)</span>
                        </div>
                        <div style="color: {color}; font-weight: bold;">
                            {verdict} ({abs(pct_diff):.1f}%) | {dif_text}
                        </div>
                    </div>
                    """
                    st.markdown(html_compact, unsafe_allow_html=True)

if __name__ == "__main__":
    if "user_info" not in st.session_state:
        login_ui()
    else:
        main_app()


