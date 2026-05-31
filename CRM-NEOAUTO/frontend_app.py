import streamlit as st
import pandas as pd
import json
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import datetime
from google_auth import get_google_creds
from calendar_utils import create_calendar_event
from Market_Research.dynamic_filters import get_unique_brands, get_models_by_brand, get_years_by_model, fetch_market_data, create_pdf_report, extract_year_from_url

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
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
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
    "Estado 5: Comprado (Stock)",
    "Estado 6: Vendido",
    "Estado 4: Cerrado"
]

# --- FUNCIONES DE BASE DE DATOS ---

@st.cache_data(ttl=300) # Caché de 5 minutos
def fetch_leads():
    try:
        # 1. Obtener Leads base - Solo columnas necesarias
        cols = "url, estado_embudo, nombre_vendedor, telefono_whatsapp, notas_actividad, fecha_actualizacion"
        resp = supabase.table("crm_contactos").select(cols).order("fecha_actualizacion", desc=True).execute()
        contacts = resp.data
        if not contacts: return []
        
        # 2. Obtener Detalles de Autos (para Marca, Modelo, Año, Distrito, Precio, KM)
        urls = [c['url'] for c in contacts]
        resp_details = supabase.table("autos_detalles_diarios").select("URL, Make, Model, Year, District, Price, Kilometers, DateTime").in_("URL", urls).execute()
        details = resp_details.data
        
        # 3. Merge en Pandas
        df_c = pd.DataFrame(contacts)
        df_d = pd.DataFrame(details)
        
        if not df_d.empty:
            df_d = df_d.sort_values(by='DateTime', ascending=True).drop_duplicates(subset=['URL'], keep='last')
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

@st.cache_data(ttl=60) # Caché de 1 minuto para GyP
def fetch_all_gyp():
    """Trae todos los registros de crm_gyp y devuelve un dict indexado por lead_url."""
    try:
        res = supabase.table("crm_gyp").select("*").execute()
        if res.data:
            return {item["lead_url"]: item for item in res.data}
        return {}
    except Exception as e:
        st.error(f"Error al leer GyP masivo: {e}")
        return {}

def fetch_gyp(lead_url):
    """Obtiene el GyP de un lead desde la caché masiva."""
    return fetch_all_gyp().get(lead_url, None)

def clear_crm_caches():
    fetch_leads.clear()
    fetch_all_gyp.clear()


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
    # --- HEADER COMPACTO ---
    col_t, col_r, col_l = st.columns([5, 1, 1])
    
    with col_t:
        st.title(f"CRM NeoAuto - Bienvenido {st.session_state.user_info.get('name', '')}")
        st.markdown(f"Usuario: `{st.session_state.user_info.get('email', '')}`")
    
    with col_r:
        st.markdown("<br>", unsafe_allow_html=True) # Alineación vertical
        if st.button("🔄 Recargar", use_container_width=True):
            clear_crm_caches()
            st.rerun()
            
    with col_l:
        st.markdown("<br>", unsafe_allow_html=True) # Alineación vertical
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.divider()

    # === MENU PRINCIPAL DE SECCIONES ===
    seccion = st.radio(
        "Seccion",
        options=["CRM", "Investigación"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")

    # --- CARGA DE DATOS ---

    with st.spinner("Sincronizando con Supabase..."):
        all_leads_data = fetch_leads()

    if not all_leads_data:
        st.info("No hay contactos en la base de datos.")
        st.stop()

    df = pd.DataFrame(all_leads_data)

    # === SECCIÓN INVESTIGACIÓN (early return antes de crear tabs) ===
    if seccion == "Investigación":
        inv_tab, lead_tab, mercado_v2_tab = st.tabs(["Mercado", "LEAD NEOAUTO", "MERCADO V2 (UNIFICADO)"])

        with inv_tab:
            st.subheader("Investigación de Mercado Dinámica")
            c1, c2, c3 = st.columns(3)
            brands = get_unique_brands(supabase)
            s_brand = c1.selectbox("1. Marca", [""] + brands, key="m_brand")
            if s_brand:
                models = get_models_by_brand(supabase, s_brand)
                s_model = c2.selectbox("2. Modelo", [""] + models, key="m_model")
                if s_model:
                    years = get_years_by_model(supabase, s_brand, s_model)
                    s_year = c3.selectbox("3. Año", [""] + [str(y) for y in years], key="m_year")
                    if s_year:
                        if st.button("Analizar Mercado", type="primary"):
                            data = fetch_market_data(supabase, s_brand, s_model, int(s_year))
                            if data:
                                df_mkt = pd.DataFrame(data)
                                m1, m2, m3 = st.columns(3)
                                m1.metric("Precio Mediano", f"${df_mkt['Price'].median():,.0f}")
                                m2.metric("KM Mediano", f"{df_mkt['Kilometers'].median():,.0f}")
                                m3.metric("Muestra", len(df_mkt))
                                
                                # --- GRÁFICO INTERACTIVO PLOTLY ---
                                import plotly.express as px
                                fig = px.scatter(
                                    df_mkt, 
                                    x="Kilometers", 
                                    y="Price",
                                    hover_data=["URL", "District"],
                                    title=f"Distribución de Mercado: {s_brand} {s_model} ({s_year})",
                                    labels={"Kilometers": "Kilometraje (KM)", "Price": "Precio ($)"},
                                    template="plotly_white",
                                    color="Price",
                                    color_continuous_scale="Viridis"
                                )
                                # Añadir línea de mediana de precio
                                fig.add_hline(y=df_mkt['Price'].median(), line_dash="dash", line_color="red", annotation_text="Mediana Mercado")
                                st.plotly_chart(fig, use_container_width=True)

                                pdf = create_pdf_report(df_mkt, s_brand, s_model, int(s_year))
                                if pdf:
                                    st.download_button("📄 Bajar Reporte PDF", pdf, f"Mercado_{s_brand}_{s_model}_{s_year}.pdf", "application/pdf")
                                st.dataframe(df_mkt[['URL', 'Price', 'Kilometers', 'District']], use_container_width=True)
                            else:
                                st.warning("No se encontraron datos para esta combinación.")

        with lead_tab:
            st.subheader("Análisis de Lead Neoauto")
            st.write("Ingresa el link de Neoauto para analizar el precio contra el mercado actual.")
            
            url_input = st.text_input("URL de Neoauto", placeholder="https://neoauto.com/auto/usado/...")
            
            if st.button("Analizar Lead", type="primary", use_container_width=True):
                if not url_input:
                    st.error("Por favor ingresa una URL válida.")
                else:
                    with st.spinner("Analizando vehículo..."):
                        # 1. Intentar buscar en la base de datos maestra (autos_detalles)
                        resp = supabase.table("autos_detalles").select("*").eq("URL", url_input).execute()
                        
                        if resp.data:
                            data = resp.data[0]
                            real_year = extract_year_from_url(url_input)
                            
                            t_data = {
                                "Make": data.get("Make"),
                                "Model": data.get("Model"),
                                "Year": real_year if real_year > 0 else (int(data.get("Year")) if data.get("Year") else 0),
                                "Price": float(data.get("Price")) if data.get("Price") else 0.0,
                                "Kilometers": int(data.get("Kilometers")) if data.get("Kilometers") else 0
                            }
                            
                            # 2. Consultar Mercado en la tabla maestra (filtrando luego por año de URL)
                            query = supabase.table("autos_detalles") \
                                        .select("*") \
                                        .eq("Make", t_data['Make']) \
                                        .eq("Model", t_data['Model'])
                            
                            mkt_resp = query.execute()
                            
                            # Filtrar mercado por año real de URL
                            filtered_mkt = []
                            for m in mkt_resp.data:
                                if extract_year_from_url(m.get('URL', '')) == t_data['Year']:
                                    filtered_mkt.append(m)
                                    
                            df_m = pd.DataFrame(filtered_mkt)
                            
                            if not df_m.empty:
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
                                
                                st.success(f"Análisis completado para {t_data['Make']} {t_data['Model']} {t_data['Year']}")
                                
                                # UI de Resultado Estilo Richard
                                res_col1, res_col2, res_col3 = st.columns(3)
                                res_col1.metric("Precio Lead", f"${t_data['Price']:,.0f}")
                                res_col2.metric("Precio Mercado (Mediana)", f"${med_price:,.0f}")
                                res_col3.metric("Diferencia (%)", f"{pct_diff:.1f}%", delta=f"{pct_diff:.1f}%", delta_color="inverse")
                                
                                html_res = f"""
                                <div style="background-color: #f8f9fa; border-left: 10px solid {color}; padding: 20px; border-radius: 8px; margin-top: 20px;">
                                    <h3 style="margin-top:0; color:{color};">{verdict}</h3>
                                    <p style="font-size:1.2em;">Este vehículo está <b>{abs(pct_diff):.1f}%</b> {'por debajo' if pct_diff < 0 else 'por encima'} del precio mediano de mercado.</p>
                                    <p style="font-size:1.1em; font-weight:bold;">{dif_text}</p>
                                    <p style="color:#666;">Basado en una muestra de {count} vehículos similares encontrados.</p>
                                </div>
                                """
                                st.markdown(html_res, unsafe_allow_html=True)
                                
                                # Botón para registrar en CRM si es Buen Trato
                                if st.button("🚀 Registrar este Lead en CRM", type="primary"):
                                    try:
                                        now = datetime.datetime.now().isoformat()
                                        supabase.table("crm_contactos").upsert({
                                            "url": url_input,
                                            "nombre_vendedor": "Lead Web Analizador",
                                            "telefono_whatsapp": "N/A",
                                            "estado_embudo": "Estado 1: 1er Contacto WhatsApp",
                                            "fecha_actualizacion": now
                                        }).execute()
                                        st.success("¡Lead enviado al CRM correctamente!")
                                        clear_crm_caches()
                                    except Exception as e:
                                        st.error(f"Error al registrar: {e}")
                            else:
                                st.warning("No hay suficientes datos de mercado para comparar este modelo/año.")
                        else:
                            st.error("No se encontró información de este link en nuestra base de datos diaria. Asegúrate de que el link sea correcto o que el scraper lo haya procesado.")
        with mercado_v2_tab:
            st.subheader("Investigación de Mercado Dinámica (Unificada)")
            c1, c2, c3 = st.columns(3)
            brands = get_unique_brands(supabase)
            s_brand = c1.selectbox("1. Marca", [""] + brands, key="m2_brand")
            if s_brand:
                models = get_models_by_brand(supabase, s_brand)
                s_model = c2.selectbox("2. Modelo", [""] + models, key="m2_model")
                if s_model:
                    years = get_years_by_model(supabase, s_brand, s_model)
                    s_year = c3.selectbox("3. Año", [""] + [str(y) for y in years], key="m2_year")
                    
                    st.write("---")
                    url_input_v2 = st.text_input("URL del Lead (Opcional)", placeholder="https://neoauto.com/auto/usado/...", key="m2_url")
                    
                    if s_year:
                        if st.button("Analizar Mercado V2", type="primary", use_container_width=True):
                            # VALIDACION AGUAS ARRIBA
                            lead_data = None
                            abort_analysis = False
                            
                            if url_input_v2:
                                with st.spinner("Validando Lead..."):
                                    resp = supabase.table("autos_detalles").select("*").eq("URL", url_input_v2).execute()
                                    if resp.data:
                                        lead_data = resp.data[0]
                                        real_year = extract_year_from_url(url_input_v2)
                                        l_year = real_year if real_year > 0 else (int(lead_data.get("Year")) if lead_data.get("Year") else 0)
                                        
                                        # OPCION A: BLOQUEO ESTRICTO (Ignorando Mayúsculas/Minúsculas)
                                        l_make = str(lead_data.get("Make", "")).strip().upper()
                                        l_model = str(lead_data.get("Model", "")).strip().upper()
                                        s_make = str(s_brand).strip().upper()
                                        s_mod = str(s_model).strip().upper()
                                        
                                        if l_make != s_make or l_model != s_mod or str(l_year) != s_year:
                                            st.error(f"❌ Error: El link pertenece a un {lead_data.get('Make')} {lead_data.get('Model')} {l_year}, pero seleccionaste {s_brand} {s_model} {s_year}. Por favor corrige los selectores o el link.")
                                            abort_analysis = True
                                        else:
                                            # Formatear lead_data para plot
                                            lead_data['Price'] = float(lead_data.get("Price")) if lead_data.get("Price") else 0.0
                                            lead_data['Kilometers'] = int(lead_data.get("Kilometers")) if lead_data.get("Kilometers") else 0
                                            lead_data['Year'] = l_year
                                    else:
                                        st.error("❌ No se encontró información de este link en nuestra BD diaria.")
                                        abort_analysis = True
                            
                            if not abort_analysis:
                                data = fetch_market_data(supabase, s_brand, s_model, int(s_year))
                                if data:
                                    df_mkt = pd.DataFrame(data)
                                    m1, m2, m3 = st.columns(3)
                                    m1.metric("Precio Mediano", f"${df_mkt['Price'].median():,.0f}")
                                    m2.metric("KM Mediano", f"{df_mkt['Kilometers'].median():,.0f}")
                                    m3.metric("Muestra", len(df_mkt))
                                    
                                    # --- GRAFICO INTERACTIVO PLOTLY ---
                                    import plotly.express as px
                                    import plotly.graph_objects as go
                                    
                                    fig = px.scatter(
                                        df_mkt, 
                                        x="Kilometers", 
                                        y="Price",
                                        hover_data=["URL", "District"],
                                        title=f"Distribución de Mercado: {s_brand} {s_model} ({s_year})",
                                        labels={"Kilometers": "Kilometraje (KM)", "Price": "Precio ($)"},
                                        template="plotly_white",
                                        color="Price",
                                        color_continuous_scale="Viridis"
                                    )
                                    med_price = df_mkt['Price'].median()
                                    fig.add_hline(y=med_price, line_dash="dash", line_color="red", annotation_text="Mediana Mercado")
                                    
                                    # ESTRELLA SI HAY LEAD
                                    if lead_data:
                                        fig.add_trace(go.Scatter(
                                            x=[lead_data['Kilometers']],
                                            y=[lead_data['Price']],
                                            mode='markers',
                                            marker=dict(symbol='star', size=24, color='orange', line=dict(width=2, color='DarkSlateGrey')),
                                            name='LEAD ANALIZADO',
                                            hoverinfo='text',
                                            hovertext=f"Precio: ${lead_data['Price']}<br>KM: {lead_data['Kilometers']}"
                                        ))
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # ALGORITMO VEREDICTO SI HAY LEAD
                                    if lead_data:
                                        df_m = df_mkt.dropna(subset=['Price'])
                                        count = len(df_m)
                                        
                                        t_price = lead_data['Price']
                                        pct_diff = ((t_price - med_price) / med_price) * 100 if med_price > 0 else 0
                                        color = "#28a745" if pct_diff < -5 else "#dc3545" if pct_diff > 5 else "#17a2b8"
                                        verdict = "BUEN TRATO" if pct_diff < -5 else "MAL TRATO" if pct_diff > 5 else "TRATO JUSTO"
                                        dif_text = f"Ahorro: ${(med_price - t_price):,.0f}" if pct_diff < -5 else f"Sobreprecio: ${(t_price - med_price):,.0f}" if pct_diff > 5 else "Precio Acorde"
                                        
                                        st.success(f"Análisis completado para {s_brand} {s_model} {s_year}")
                                        
                                        res_col1, res_col2, res_col3 = st.columns(3)
                                        res_col1.metric("Precio Lead", f"${t_price:,.0f}")
                                        res_col2.metric("Precio Mercado (Mediana)", f"${med_price:,.0f}")
                                        res_col3.metric("Diferencia (%)", f"{pct_diff:.1f}%", delta=f"{pct_diff:.1f}%", delta_color="inverse")
                                        
                                        html_res = f"""
                                        <div style="background-color: #f8f9fa; border-left: 10px solid {color}; padding: 20px; border-radius: 8px; margin-top: 20px;">
                                            <h3 style="margin-top:0; color:{color};">{verdict}</h3>
                                            <p style="font-size:1.2em;">Este vehículo está <b>{abs(pct_diff):.1f}%</b> {'por debajo' if pct_diff < 0 else 'por encima'} del precio mediano de mercado.</p>
                                            <p style="font-size:1.1em; font-weight:bold;">{dif_text}</p>
                                            <p style="color:#666;">Basado en una muestra de {count} vehículos similares encontrados.</p>
                                        </div>
                                        """
                                        st.markdown(html_res, unsafe_allow_html=True)
                                        
                                        if st.button("🚀 Registrar Lead V2 en CRM", type="primary"):
                                            try:
                                                now = datetime.datetime.now().isoformat()
                                                supabase.table("crm_contactos").upsert({
                                                    "url": url_input_v2,
                                                    "nombre_vendedor": "Lead Web Analizador",
                                                    "telefono_whatsapp": "N/A",
                                                    "estado_embudo": "Estado 1: 1er Contacto WhatsApp",
                                                    "fecha_actualizacion": now
                                                }).execute()
                                                st.success("¡Lead enviado al CRM correctamente!")
                                                clear_crm_caches()
                                            except Exception as e:
                                                st.error(f"Error al registrar: {e}")
                                    
                                    pdf = create_pdf_report(df_mkt, s_brand, s_model, int(s_year))
                                    if pdf:
                                        st.download_button("📄 Bajar Reporte PDF", pdf, f"Mercado_V2_{s_brand}_{s_model}_{s_year}.pdf", "application/pdf", key="dl_v2")
                                    st.dataframe(df_mkt[['URL', 'Price', 'Kilometers', 'District']], use_container_width=True)
                                else:
                                    st.warning("No se encontraron datos para esta combinación.")

        return  # <- early return: no ejecutar el bloque CRM

    # === SECCIÓN CRM ===
    tabs = st.tabs(["WhatsApp", "Citas", "Visitas", "Comprados", "Vendidos", "Cerrado"])

    for tab, estado in zip(tabs, ESTADOS):
        with tab:
            state_df = df[df["estado_embudo"] == estado] if not df.empty else pd.DataFrame()
            st.subheader(f"{estado} ({len(state_df)})")
            
            if state_df.empty:
                st.write("Sin contactos en esta etapa.")
                continue
                
            # Preparar Grilla con datos enriquecidos
            grid_data = []
            ganancia_total_acumulada = 0.0
            
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
                    
                row_data = {
                    "Seleccionar": False,
                    "Vendedor": row.get('nombre_vendedor', 'N/A'),
                    "Vehiculo": f"{marca} {modelo}".strip(),
                    "Precio": precio_f,
                    "Anio": row.get('Year', 'N/A'),
                    "Distrito": row.get('District', 'N/A'),
                    "KM": km_f,
                }
                
                if estado == "Estado 6: Vendido":
                    gyp_data_row = fetch_gyp(row['url']) or {}
                    utilidad = float(gyp_data_row.get("utilidad_neta_usd", 0) or 0)
                    ganancia_total_acumulada += utilidad
                    
                    tc = float(gyp_data_row.get("tipo_cambio", 3.4) or 3.4)
                    
                    p_compra_usd = float(gyp_data_row.get("precio_compra_usd", 0) or 0)
                    p_compra_pen = float(gyp_data_row.get("precio_compra_pen", 0) or 0)
                    p_compra_total = p_compra_usd + (p_compra_pen / tc if tc > 0 else 0)
                    
                    p_venta_usd = float(gyp_data_row.get("precio_venta_usd", 0) or 0)
                    p_venta_pen = float(gyp_data_row.get("precio_venta_pen", 0) or 0)
                    p_venta_total = p_venta_usd + (p_venta_pen / tc if tc > 0 else 0)
                    
                    pct_ganancia = (utilidad / p_compra_total * 100) if p_compra_total > 0 else 0.0
                    
                    f_compra_str = gyp_data_row.get("fecha_notaria_compra")
                    f_venta_str = gyp_data_row.get("fecha_notaria_venta")
                    dias_stock = "N/A"
                    if f_compra_str and f_venta_str:
                        try:
                            d_compra = pd.to_datetime(f_compra_str)
                            d_venta = pd.to_datetime(f_venta_str)
                            d_val = (d_venta - d_compra).days
                            dias_stock = f"{d_val} días" if d_val >= 0 else "0 días"
                        except: pass
                        
                    row_data["P. Compra"] = f"${p_compra_total:,.0f}" if p_compra_total > 0 else "N/A"
                    row_data["P. Venta"] = f"${p_venta_total:,.0f}" if p_venta_total > 0 else "N/A"
                    row_data["Placa"] = str(gyp_data_row.get("placa", "N/A")).strip()
                    row_data["F. Compra"] = f_compra_str[:10] if f_compra_str else "N/A"
                    row_data["F. Venta"] = f_venta_str[:10] if f_venta_str else "N/A"
                    row_data["Días Stock"] = dias_stock
                    row_data["Ganancia %"] = f"{pct_ganancia:.1f}%"
                    row_data["Ganancia USD"] = f"${utilidad:,.2f}"
                    row_data["_raw_f_venta"] = f_venta_str if f_venta_str else "1900-01-01"

                row_data.update({
                    "Chat": f"https://wa.me/{tel}" if tel and tel != "None" else None,
                    "NeoAuto": row['url'],
                    "Fecha": str(row.get('fecha_actualizacion', ''))[:10] if row.get('fecha_actualizacion') else "N/A",
                    "_raw_url": row['url'],
                    "_raw_notas": row.get('notas_actividad', {}),
                    "_raw_row": row.to_dict()
                })
                grid_data.append(row_data)
                
            grid_df = pd.DataFrame(grid_data)
            if estado == "Estado 6: Vendido":
                grid_df = grid_df.sort_values(by="_raw_f_venta", ascending=False)
            
            col_config = {
                "Seleccionar": st.column_config.CheckboxColumn("Sel.", required=True),
                "Chat": st.column_config.LinkColumn("WhatsApp", display_text=r"(\d+)"),
                "NeoAuto": st.column_config.LinkColumn("Link", display_text="Ver Auto"),
                "Vehiculo": st.column_config.TextColumn("Marca/Modelo"),
                "_raw_url": None, "_raw_notas": None, "_raw_row": None
            }
            
            editor_kwargs = {
                "data": grid_df,
                "column_config": col_config,
                "hide_index": True,
                "use_container_width": True,
                "key": f"grid_v45_{estado}"
            }
            
            if estado == "Estado 6: Vendido":
                editor_kwargs["column_order"] = [
                    "Seleccionar", "Vendedor", "Vehiculo", "Anio", "Distrito", 
                    "Precio", "P. Compra", "P. Venta", "Placa", "F. Compra", "F. Venta", 
                    "Días Stock", "Ganancia %", "Ganancia USD"
                ]
                col_config["Precio"] = st.column_config.TextColumn("P. Anuncio")
                col_config["P. Compra"] = st.column_config.TextColumn("P. Compra")
                col_config["P. Venta"] = st.column_config.TextColumn("P. Venta")
                col_config["Placa"] = st.column_config.TextColumn("Placa")
                col_config["F. Compra"] = st.column_config.TextColumn("F. Compra")
                col_config["F. Venta"] = st.column_config.TextColumn("F. Venta")
                col_config["Días Stock"] = st.column_config.TextColumn("Días Stock")
                col_config["Ganancia %"] = st.column_config.TextColumn("Ganancia %")
                col_config["Ganancia USD"] = st.column_config.TextColumn("Ganancia USD")

            # Grid Maestro Estilo Inandes
            edited_df = st.data_editor(**editor_kwargs)
            
            if estado == "Estado 6: Vendido":
                st.markdown(f'''
                <br>
                <div style="text-align:center; background-color:#e8f5e9; border: 2px solid #4caf50; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color:#2e7d32; margin:0;">💰 GANANCIA TOTAL ACUMULADA: ${ganancia_total_acumulada:,.2f}</h2>
                </div>
                ''', unsafe_allow_html=True)
            
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
                if estado == "Estado 6: Vendido":
                    st.markdown(f"#### 🚗 Vehículo Vendido por: {lead.get('nombre_vendedor', 'N/A')} ({lead.get('Make', '')} {lead.get('Model', '')})")
                else:
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
                        tc = st.number_input("T. Cambio", min_value=1.0, value=float(g.get("tipo_cambio", 3.4)), step=0.01, format="%.2f", key=f"tc_{lead['url']}")

                    # --- ENCABEZADOS DE 4 COLUMNAS ---
                    h1, h2, h3, h4 = st.columns([3, 1, 1, 1.5])
                    h1.markdown("**RUBRO**")
                    h2.markdown("**USD ($)**")
                    h3.markdown("**PEN (S/)**")
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

                    # Inicializar resultados en session_state si no existen (Cargar de DB)
                    if f"calc_{lead['url']}" not in st.session_state:
                         # El Total GyP (Columna 4) debe ser la suma de lo que hay en DB: USD + (PEN/TC)
                         db_calcs = {}
                         total_inc_db = 0.0
                         total_exp_db = 0.0
                         for _, kn in rubros:
                             val_u_db = float(g.get(f"{kn}_usd", 0) or 0)
                             val_p_db = float(g.get(f"{kn}_pen", 0) or 0)
                             subtotal_db = val_u_db + (val_p_db / tc if tc > 0 else 0)
                             db_calcs[kn] = round(subtotal_db, 2)
                             if kn == "precio_venta": total_inc_db = subtotal_db
                             else: total_exp_db += subtotal_db
                         
                         db_calcs["utilidad"] = round(total_inc_db - total_exp_db, 2)
                         st.session_state[f"calc_{lead['url']}"] = db_calcs

                    resultados_finales = {}

                    for label, key_name in rubros:
                        c1, c2, c3, c4 = st.columns([3, 1, 1, 1.5])
                        c1.write(label)
                        
                        k_usd = f"u_{key_name}_{lead['url']}"
                        k_pen = f"p_{key_name}_{lead['url']}"
                        
                        # Insumos (USD y PEN) - Cargan directamente de sus respectivas columnas en DB
                        v_usd = c2.number_input("USD", min_value=0.0, value=float(g.get(f"{key_name}_usd", 0) or 0), step=1.0, label_visibility="collapsed", key=k_usd)
                        v_pen = c3.number_input("PEN", min_value=0.0, value=float(g.get(f"{key_name}_pen", 0) or 0), step=1.0, label_visibility="collapsed", key=k_pen)
                        
                        # El total se muestra desde el session_state (actualizado por el botón Calcular o cargado de DB)
                        total_item = st.session_state[f"calc_{lead['url']}"].get(key_name, 0.0)
                        
                        if key_name == "precio_venta":
                            c4.markdown(f"<div style='text-align:center; background-color:#e8f5e9; color:#1b5e20; padding:4px; border-radius:4px; font-weight:bold; border: 1px solid #c8e6c9;'>${total_item:,.2f}</div>", unsafe_allow_html=True)
                        else:
                            c4.markdown(f"<div style='text-align:center; background-color:#ffebee; color:#b71c1c; padding:4px; border-radius:4px; border: 1px solid #ffcdd2;'>-${total_item:,.2f}</div>", unsafe_allow_html=True)

                    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)
                    
                    # Totales (desde session_state)
                    utilidad = st.session_state[f"calc_{lead['url']}"]["utilidad"]
                    total_ingresos = st.session_state[f"calc_{lead['url']}"]["precio_venta"]
                    margen_pct = (utilidad / total_ingresos * 100) if total_ingresos > 0 else 0.0

                    color = "green" if utilidad > 0 else "red"
                    st.markdown(f"<h5 style='text-align:right'>UTILIDAD NETA ESTIMADA: <span style='color:{color}'>${utilidad:,.2f} ({margen_pct:.1f}%)</span></h5>", unsafe_allow_html=True)

                    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)
                    
                    # --- CAMPOS DE NOTARÍA Y VEHÍCULO ---
                    st.markdown("##### Datos de Notaría y Vehículo")
                    # Fila Compra + Placa
                    nc1, nc2, nc3 = st.columns(3)
                    with nc1:
                        notaria_compra = st.text_input("Notaría Compra:", value=g.get("notaria_compra", ""), key=f"nc_{lead['url']}")
                    with nc2:
                        def_date_c = datetime.date.fromisoformat(g["fecha_notaria_compra"]) if g.get("fecha_notaria_compra") else datetime.date.today()
                        fecha_compra = st.date_input("Fecha Compra:", value=def_date_c, key=f"fdc_{lead['url']}")
                    with nc3:
                        placa = st.text_input("PLACA:", value=g.get("placa", ""), key=f"pl_{lead['url']}").upper()

                    # Fila Venta + Año
                    nv1, nv2, nv3 = st.columns(3)
                    with nv1:
                        notaria_venta = st.text_input("Notaría Venta:", value=g.get("notaria_venta", ""), key=f"nv_{lead['url']}")
                    with nv2:
                        def_date_v = datetime.date.fromisoformat(g["fecha_notaria_venta"]) if g.get("fecha_notaria_venta") else datetime.date.today()
                        fecha_venta = st.date_input("Fecha Venta:", value=def_date_v, key=f"fdv_{lead['url']}")
                    with nv3:
                        st.empty() 

                    st.divider()
                    
                    col_com, col_btns = st.columns([3, 2])
                    with col_com:
                        com_val = g.get("comentarios", {})
                        com_text = com_val.get("texto", "") if isinstance(com_val, dict) else str(com_val)
                        comentarios_txt = st.text_area("Notas Adicionales:", value=com_text, height=130, label_visibility="collapsed", placeholder="Notas de GyP...", key=f"g_com_{lead['url']}")
                        
                    with col_btns:
                        # BOTÓN CALCULAR (Actualiza la visualización temporal)
                        if st.button("Calcular GyP", use_container_width=True, key=f"btn_calc_{lead['url']}"):
                            new_calcs = {}
                            total_inc = 0.0
                            total_exp = 0.0
                            for _, kn in rubros:
                                val_u = st.session_state.get(f"u_{kn}_{lead['url']}", 0.0)
                                val_p = st.session_state.get(f"p_{kn}_{lead['url']}", 0.0)
                                subtotal = val_u + (val_p / tc if tc > 0 else 0)
                                new_calcs[kn] = round(subtotal, 2)
                                if kn == "precio_venta": total_inc = subtotal
                                else: total_exp += subtotal
                            
                            new_calcs["utilidad"] = round(total_inc - total_exp, 2)
                            st.session_state[f"calc_{lead['url']}"] = new_calcs
                            st.rerun()

                        # BOTÓN GUARDAR (Recalcula antes de enviar a DB para asegurar consistencia)
                        if st.button("Guardar GyP", type="primary", use_container_width=True, key=f"btn_save_{lead['url']}"):
                            final_inc = 0.0
                            final_exp = 0.0
                            gyp_payload = {
                                "tipo_cambio": tc,
                                "comentarios": {"texto": comentarios_txt} if comentarios_txt else {},
                                "notaria_compra": notaria_compra,
                                "notaria_venta": notaria_venta,
                                "fecha_notaria_compra": fecha_compra.isoformat(),
                                "fecha_notaria_venta": fecha_venta.isoformat(),
                                "placa": placa.upper(),
                                "anio": str(lead.get("Year", "N/A"))
                            }




                            
                            # Recalcular y Mapear para DB
                            for _, kn in rubros:
                                val_u = st.session_state.get(f"u_{kn}_{lead['url']}", 0.0)
                                val_p = st.session_state.get(f"p_{kn}_{lead['url']}", 0.0)
                                subtotal = val_u + (val_p / tc if tc > 0 else 0)
                                
                                gyp_payload[f"{kn}_usd"] = val_u
                                gyp_payload[f"{kn}_pen"] = val_p
                                
                                if kn == "precio_venta": final_inc = subtotal
                                else: final_exp += subtotal
                            
                            gyp_payload["utilidad_neta_usd"] = round(final_inc - final_exp, 2)
                                
                            if save_gyp(lead['url'], gyp_payload):
                                # Limpiar caché para reflejar cambios
                                clear_crm_caches()
                                # Limpiar estado de calculo para forzar recarga de DB en el proximo render
                                if f"calc_{lead['url']}" in st.session_state:
                                    del st.session_state[f"calc_{lead['url']}"]
                                st.success("¡GyP guardado exitosamente!")
                                st.rerun()


                        vendido_habilitado = total_ingresos > 0
                        if st.button("Mover a Vendido", use_container_width=True, disabled=not vendido_habilitado, key=f"btn_vendido_{lead['url']}"):
                            if move_lead_state(lead['url'], estado, "Estado 6: Vendido", n_history):
                                clear_crm_caches()
                                st.success("Lead movido a Vendido.")
                                st.rerun()


                # ============================================================
                # PANEL VENDIDOS — solo para Estado 6: Vendido
                # ============================================================
                elif estado == "Estado 6: Vendido":
                    c_datos, c_notas = st.columns([1.2, 1.3])
                    
                    with c_datos:
                        st.write("📊 **Resumen Financiero (GyP)**")
                        
                        gyp_data_v = fetch_gyp(lead['url']) or {}
                        tc = float(gyp_data_v.get("tipo_cambio", 3.4) or 3.4)
                        
                        v_rubros = [
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
                        
                        total_compra = 0.0
                        total_gastos = 0.0
                        precio_venta = 0.0
                        gastos_desglosados = []
                        
                        for label, key_name in v_rubros:
                            val_u = float(gyp_data_v.get(f"{key_name}_usd", 0) or 0)
                            val_p = float(gyp_data_v.get(f"{key_name}_pen", 0) or 0)
                            subtotal = val_u + (val_p / tc if tc > 0 else 0)
                            
                            if subtotal > 0:
                                if key_name == "precio_venta":
                                    precio_venta = subtotal
                                elif key_name == "precio_compra":
                                    total_compra = subtotal
                                else:
                                    total_gastos += subtotal
                                    gastos_desglosados.append((label, subtotal))
                        
                        utilidad = precio_venta - (total_compra + total_gastos)
                        pct_ganancia = (utilidad / total_compra * 100) if total_compra > 0 else 0.0
                        
                        # Función para limpiar sangrías y evitar que Streamlit renderice HTML como texto de código
                        def clean_html(html_str):
                            return "".join(line.strip() for line in html_str.split("\n"))
                        
                        # Tabla resumen HTML
                        rows_html = f"""
                        <tr style="border-bottom: 2px solid #ddd; font-weight: bold; color: #1b5e20;">
                            <td style="padding: 6px 0;">Precio Venta</td>
                            <td style="text-align: right; padding: 6px 0;">${precio_venta:,.2f}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee; color: #b71c1c;">
                            <td style="padding: 4px 0;">Precio Compra</td>
                            <td style="text-align: right; padding: 4px 0;">-${total_compra:,.2f}</td>
                        </tr>
                        """
                        
                        for label_g, monto_g in gastos_desglosados:
                            rows_html += f"""
                            <tr style="border-bottom: 1px solid #f3f3f3; color: #555; font-size: 0.9rem;">
                                <td style="padding: 3px 0; padding-left: 10px; color: #666;">• {label_g}</td>
                                <td style="text-align: right; padding: 3px 0; color: #b71c1c;">-${monto_g:,.2f}</td>
                            </tr>
                            """
                            
                        if total_gastos > 0:
                            rows_html += f"""
                            <tr style="border-bottom: 1px solid #eee; font-weight: bold; color: #b71c1c;">
                                <td style="padding: 4px 0;">Total Gastos Operativos</td>
                                <td style="text-align: right; padding: 4px 0;">-${total_gastos:,.2f}</td>
                            </tr>
                            """
                            
                        color_utilidad = "#1b5e20" if utilidad >= 0 else "#b71c1c"
                        bg_utilidad = "#e8f5e9" if utilidad >= 0 else "#ffebee"
                        border_utilidad = "#c8e6c9" if utilidad >= 0 else "#ffcdd2"
                        
                        html_table = f"""
                        <table style="width:100%; border-collapse: collapse; margin-bottom: 15px;">
                            {rows_html}
                        </table>
                        <div style="background-color:{bg_utilidad}; border: 1px solid {border_utilidad}; border-radius: 6px; padding: 10px; text-align: center; margin-bottom: 15px;">
                            <span style="font-size: 0.85rem; color: #555; display: block; font-weight: bold; text-transform: uppercase;">Utilidad Neta Real</span>
                            <span style="font-size: 1.35rem; color: {color_utilidad}; font-weight: bold; display: block;">${utilidad:,.2f} ({pct_ganancia:.1f}%)</span>
                        </div>
                        <span style="font-size: 0.8rem; color: #888; display: block; margin-bottom: 15px;">T.C. aplicado: {tc:.3f} | Todos los montos expresados en USD</span>
                        """
                        st.markdown(clean_html(html_table), unsafe_allow_html=True)
                        

                    with c_notas:
                        st.write("**Bitácora / Notas (Historial)**")
                        
                        # 1. Notas CRM de crm_contactos (filtrar campos técnicos del auto)
                        CAMPOS_AUTO = {"Make","Model","Year","Price","District","Province","Fuel_Type",
                                       "Kilometers","Engine_Size","unico_dueno","Transmission","Registro",
                                       "estado_embudo","url","nombre_vendedor","telefono_whatsapp"}
                        crm_notas = {k: v for k, v in n_history.items() if k not in CAMPOS_AUTO}
                        
                        # 2. Comentarios de crm_gyp
                        gyp_data_v = fetch_gyp(lead['url']) or {}
                        com_val = gyp_data_v.get("comentarios", {})
                        gyp_com_text = com_val.get("texto", "").strip() if isinstance(com_val, dict) else str(com_val).strip()
                        gyp_com_fecha = com_val.get("fecha", "") if isinstance(com_val, dict) else ""
                        
                        # 3. Construir HTML del historial
                        notas_html = ""
                        # Primero las notas de trayecto CRM
                        for key, val in crm_notas.items():
                            notas_html += f"<div style='margin-bottom:8px; font-size:14px;'><strong style='color:#333;'>{key}:</strong> <span style='color:#555;'>{val}</span></div>"
                        # Luego los comentarios de GyP (si los hay)
                        if gyp_com_text and gyp_com_text not in ("", "{}"):
                            fecha_label = f" <span style='font-weight:normal; color:#999; font-size:12px;'>({gyp_com_fecha})</span>" if gyp_com_fecha else ""
                            notas_html += f"<div style='margin-bottom:8px; font-size:14px; border-top:1px solid #eee; padding-top:8px;'><strong style='color:#b71c1c;'>📝 Comentarios GyP:{fecha_label}</strong><br><span style='color:#555; white-space:pre-wrap;'>{gyp_com_text}</span></div>"
                        
                        if not notas_html:
                            notas_html = "<div style='color:#777; font-size:14px;'>No hay actividad CRM registrada todavía.</div>"
                                
                        st.markdown(f"""
                        <div style="max-height: 250px; overflow-y: auto; padding: 12px; border: 1px solid #ddd; border-radius: 6px; background: #fdfdfd; margin-bottom: 15px;">
                            {notas_html}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 4. Campo para agregar nota adicional — se guarda en crm_gyp.comentarios
                        st.write("**Agregar Nota Adicional (se guarda en GyP)**")
                        n_text = st.text_area("Escribe aquí...", key=f"v_txt_{lead['url']}", height=80, label_visibility="collapsed")
                        
                        if st.button("Guardar Nota Adicional", use_container_width=True, type="primary", key=f"v_btn_n_{lead['url']}"):
                            if n_text and n_text.strip():
                                timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
                                nueva_linea = f"[{timestamp}] {n_text.strip()}"
                                # Concatenar sobre el texto existente
                                texto_actual = gyp_com_text if gyp_com_text and gyp_com_text not in ("", "{}") else ""
                                texto_nuevo = (texto_actual + "\n" + nueva_linea).strip()
                                # Guardar texto + fecha de ultima modificacion
                                if save_gyp(lead['url'], {"comentarios": {"texto": texto_nuevo, "fecha": timestamp}}):
                                    clear_crm_caches()
                                    st.success("Nota adicional guardada en GyP.")
                                    st.rerun()
                            else:
                                st.warning("Escribe algo antes de guardar.")

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
                                clear_crm_caches()
                                st.success("Estado actualizado")
                                st.rerun()
                    with b2:
                        if st.button("Guardar Nota", use_container_width=True, key=f"btn_n_{lead['url']}"):
                            if add_note_to_lead(lead['url'], n_history, estado, n_text):
                                clear_crm_caches()
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
                
                # Embed iframe nativo sin wrapper (evita crasheo React de pantalla blanca)
                st.markdown(f'''
                <div style="display:flex; justify-content:center;">
                    <iframe src="{calendar_url}" style="border: 0; width: 100%; height: 600px;" frameborder="0" scrolling="yes"></iframe>
                </div>
                ''', unsafe_allow_html=True)

if __name__ == "__main__":
    if "user_info" not in st.session_state:
        login_ui()
    else:
        main_app()
