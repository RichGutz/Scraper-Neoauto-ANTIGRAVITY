import streamlit as st

def render_drive_tree(service, folder_vehiculo_name, root_folder_id, key_prefix="dt"):
    """
    Renderiza un explorador visual de Google Drive para la carpeta de un vehículo específico.
    Si la carpeta no existe, muestra un aviso amigable.
    """
    st.markdown("---")
    st.subheader("🗂️ Explorador en Vivo (Google Drive)")

    # 1. Buscar si la carpeta madre del vehículo existe (por PLACA, ignorando la fecha exacta)
    try:
        placa_id = folder_vehiculo_name.split('_')[-1]
        query = f"'{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and name contains '{placa_id}' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)', supportsAllDrives=True).execute()
        existing = results.get('files', [])
    except Exception as e:
        st.error(f"Error al conectar con Google Drive: {e}")
        return

    if not existing:
        st.info("ℹ️ Todavía no hay documentos subidos en Google Drive para este auto. Usa los botones de arriba para empezar.")
        return

    vehiculo_folder_id = existing[0]['id']

    # 2. Configurar State de Navegación
    nav_key_id = f"{key_prefix}_nav_folder_id"
    nav_key_name = f"{key_prefix}_nav_folder_name"
    nav_key_history = f"{key_prefix}_nav_history"

    # Inicializar estado si no existe o si cambió el auto
    if nav_key_id not in st.session_state or st.session_state.get(f"{key_prefix}_root") != vehiculo_folder_id:
        st.session_state[nav_key_id] = vehiculo_folder_id
        st.session_state[nav_key_name] = f"🚗 {folder_vehiculo_name}"
        st.session_state[nav_key_history] = []
        st.session_state[f"{key_prefix}_root"] = vehiculo_folder_id

    current_id = st.session_state[nav_key_id]
    current_name = st.session_state[nav_key_name]

    # 3. UI del Navegador (Header)
    with st.container(border=True):
        col_path, col_back = st.columns([4, 1])
        with col_path:
            path_str = " > ".join([h[1] for h in st.session_state[nav_key_history]] + [current_name])
            st.markdown(f"**Ruta:** `{path_str}`")
        
        with col_back:
            if st.session_state[nav_key_history]:
                if st.button("⬅️ Subir Nivel", key=f"{key_prefix}_btn_back", use_container_width=True):
                    last_id, last_name = st.session_state[nav_key_history].pop()
                    st.session_state[nav_key_id] = last_id
                    st.session_state[nav_key_name] = last_name
                    st.rerun()

        st.divider()

        # 4. Traer contenido actual (Archivos y Carpetas)
        try:
            content_query = f"'{current_id}' in parents and trashed=false"
            content_results = service.files().list(
                q=content_query, 
                pageSize=100, 
                fields="files(id, name, mimeType, webViewLink, iconLink)", 
                orderBy="folder, name",
                supportsAllDrives=True
            ).execute()
            items = content_results.get('files', [])
        except Exception as e:
            st.error(f"Error leyendo carpeta: {e}")
            items = []

        if not items:
            st.caption("*(Carpeta vacía)*")
        else:
            # Separar carpetas y archivos
            folders = [f for f in items if f['mimeType'] == 'application/vnd.google-apps.folder']
            files = [f for f in items if f['mimeType'] != 'application/vnd.google-apps.folder']

            # Pintar Carpetas (Botones navegables)
            if folders:
                st.markdown("📂 **Subcarpetas**")
                cols = st.columns(min(4, len(folders)))
                for idx, folder in enumerate(folders):
                    with cols[idx % len(cols)]:
                        if st.button(f"📁 {folder['name']}", key=f"{key_prefix}_go_{folder['id']}", use_container_width=True):
                            st.session_state[nav_key_history].append((current_id, current_name))
                            st.session_state[nav_key_id] = folder['id']
                            st.session_state[nav_key_name] = folder['name']
                            st.rerun()
            
            # Pintar Archivos (Links)
            if files:
                if folders:
                    st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("📄 **Archivos**")
                for f in files:
                    # Usar iconLink si existe, o emoji fallback
                    icon = f"<img src='{f.get('iconLink')}' width='16' style='vertical-align: middle; margin-right: 5px;'>" if f.get('iconLink') else "📎 "
                    st.markdown(f"{icon} <a href='{f.get('webViewLink')}' target='_blank' style='text-decoration:none; color:#1f77b4;'><b>{f.get('name')}</b></a>", unsafe_allow_html=True)
