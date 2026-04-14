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
    /* Asegurar que las tabs resalten visualmente */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff;
        border-bottom: 2px solid #0068c9;
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

def save_gyp_and_move(url, gyp_data, current_state, new_state, notes_history, new_note_text):
    try:
        # Guardar en la nueva tabla dedicada
        supabase.table("crm_gyp").insert(gyp_data).execute()
        # Mover de estado
        return move_lead_state(url, current_state, new_state, notes_history, new_note_text)
    except Exception as e:
        st.error(f"Error al guardar GyP: {e}")
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
                    
                    # LOGICA GyP: Si se quiere pasar a Vendido
                    if avanzar_a == "Estado 6: Vendido":
                        if estado != "Estado 5: Comprado (Stock)":
                            st.error("❌ Solo los vehículos en 'Comprado (Stock)' pueden liquidarse y pasar a 'Vendido'.")
                        else:
                            st.markdown("### 📊 Liquidación GyP (Venta)")
                            tc = st.number_input("Tipo de Cambio (TC)", value=3.40, step=0.01, format="%.2f", key=f"tc_{lead['url']}")
                            
                            col_ing1, col_ing2 = st.columns(2)
                            with col_ing1:
                                p_compra = st.number_input("Precio Compra (USD)", value=0.0, step=100.0, key=f"pcompra_{lead['url']}")
                            with col_ing2:
                                p_venta = st.number_input("Precio Venta (USD)", value=0.0, step=100.0, key=f"pventa_{lead['url']}")
                            
                            st.markdown("#### Costos Operativos (PEN)")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                notarial = st.number_input("Notarial (PEN)", value=0.0, step=10.0, key=f"notarial_{lead['url']}")
                                lavado = st.number_input("Lavado (PEN)", value=0.0, step=10.0, key=f"lavado_{lead['url']}")
                                mecanica = st.number_input("Mecánica (PEN)", value=0.0, step=10.0, key=f"mecanica_{lead['url']}")
                                cheque = st.number_input("Cheque Gcia (PEN)", value=0.0, step=10.0, key=f"cheque_{lead['url']}")
                            with c2:
                                registral = st.number_input("Registral (PEN)", value=0.0, step=10.0, key=f"registral_{lead['url']}")
                                gasolina = st.number_input("Gasolina (PEN)", value=0.0, step=10.0, key=f"gasolina_{lead['url']}")
                                llantas = st.number_input("Llantas (PEN)", value=0.0, step=10.0, key=f"llantas_{lead['url']}")
                                intereses = st.number_input("Intereses (PEN)", value=0.0, step=10.0, key=f"intereses_{lead['url']}")
                            with c3:
                                pintura = st.number_input("Pintura/Aros (PEN)", value=0.0, step=10.0, key=f"pintura_{lead['url']}")
                                cochera = st.number_input("Cochera (PEN)", value=0.0, step=10.0, key=f"cochera_{lead['url']}")
                                neoauto_ad = st.number_input("Neoauto (PEN)", value=0.0, step=10.0, key=f"neoauto_{lead['url']}")
                            
                            comentarios_gyp = st.text_area("Comentarios Financieros:", key=f"comm_gyp_{lead['url']}")
                            
                            # Calculos dinámicos
                            total_costos_pen = (notarial + registral + pintura + lavado + gasolina + cochera + mecanica + llantas + neoauto_ad + cheque + intereses)
                            total_costos_usd = total_costos_pen / tc if tc > 0 else 0
                            costo_total_inv_usd = p_compra + total_costos_usd
                            utilidad_usd = p_venta - costo_total_inv_usd
                            tir_pct = (utilidad_usd / costo_total_inv_usd * 100) if costo_total_inv_usd > 0 else 0
                            
                            st.markdown("---")
                            rc1, rc2, rc3 = st.columns(3)
                            rc1.metric("Total Costos", f"S/ {total_costos_pen:,.2f}", f"${total_costos_usd:,.2f} USD")
                            rc2.metric("Utilidad Neta", f"${utilidad_usd:,.2f}", delta_color="normal")
                            rc3.metric("TIR (%)", f"{tir_pct:,.2f}%", delta_color="normal")
                            
                            if st.button("✅ Grabar GyP y Marcar Vendido", type="primary", key=f"save_gyp_{lead['url']}"):
                                gyp_data = {
                                    "lead_url": lead['url'],
                                    "tipo_cambio": tc,
                                    "precio_compra_usd": p_compra,
                                    "precio_venta_usd": p_venta,
                                    "notarial_pen": notarial,
                                    "registral_pen": registral,
                                    "pintura_aros_pen": pintura,
                                    "lavado_pen": lavado,
                                    "gasolina_pen": gasolina,
                                    "cochera_pen": cochera,
                                    "mecanica_pen": mecanica,
                                    "llantas_pen": llantas,
                                    "neoauto_pen": neoauto_ad,
                                    "cheque_gerencia_pen": cheque,
                                    "intereses_pen": intereses,
                                    "utilidad_neta_usd": utilidad_usd,
                                    "tasa_tir_porcentaje": tir_pct,
                                    "comentarios": {"notas": comentarios_gyp}
                                }
                                if save_gyp_and_move(lead['url'], gyp_data, estado, avanzar_a, notas, motivo):
                                    st.success(f"GyP guardado y auto movido a {avanzar_a}")
                                    del st.session_state.current_lead
                                    st.rerun()

                    else:
                        # Para cualquier otro estado que no sea Vendido
                        if st.button("Confirmar Movimiento", type="primary", key=f"confirm_move_{lead['url']}"):
                            if move_lead_state(lead['url'], estado, avanzar_a, notas, motivo):
                                st.success(f"Movido a {avanzar_a}")
                                del st.session_state.current_lead
                                st.rerun()
            else:
                st.info("👈 Selecciona 'Inspeccionar Lead' en un contacto para ver los detalles y actualizar su estado.")
