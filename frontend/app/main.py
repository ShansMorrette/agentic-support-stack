import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# Backend base URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://app:8001")

def fetch_data(endpoint):
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

def main():
    st.set_page_config(
        page_title="WebLanMasters | Smart Attention",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for peak aesthetics and stability
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 5px solid #4e73df;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        .stButton>button {
            border-radius: 20px;
        }
        .main .block-container {
            max-width: 95%;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stDataFrame {
            width: 100% !important;
        }
        div[data-testid="stTable"] {
            overflow: visible !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
        st.title("WebLan Masters")
        st.markdown("### 🤖 Smart Attention")
        st.markdown("---")
        
        menu = st.radio(
            "Navegación",
            ["📊 Dashboard General", "🚀 Ventas / Prospects", "🛠️ Soporte / Tickets"],
            index=0
        )
        
        st.markdown("---")
        st.info(f"🌐 Server: {BACKEND_URL}")
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            st.rerun()

    # --- HEADER ---
    st.title("🧠 Panel de Control Inteligente")
    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")

    # Fetch initial data
    prospects = fetch_data("/api/atencion/prospects")
    tickets = fetch_data("/api/atencion/tickets?status=open")
    
    # Deduplicación por ID
    all_raw_data = prospects + tickets
    dedup_map = {item['id']: item for item in all_raw_data}
    unified_data = list(dedup_map.values())
    
    # --- METRICS ---
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Total Prospects", len(prospects))
    with m_col2:
        st.metric("Tickets Abiertos", len(tickets))
    with m_col3:
        st.metric("Calidad Promedio", "88/100", delta="+3%")
    with m_col4:
        st.metric("SLA Cumplido", "96%", delta="99%")

    st.markdown("---")

    # --- CENTRAL FILTERS Row ---
    st.markdown("### 🔍 Filtros de Visualización")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        f_priority = st.selectbox("Prioridad", ["Todas", "🔴 Alta", "🟡 Media", "🟢 Baja"])
    with f_col2:
        f_category = st.selectbox("Categoría", ["Todas", "Soporte Técnico", "Ventas", "Facturación", "Otros"])
    with f_col3:
        f_status = st.selectbox("Estado", ["Todos", "Abierto", "Pendiente", "Cerrado"])

    st.markdown("---")

    # Process Data
    df_unified = pd.DataFrame(unified_data)
    
    if not df_unified.empty:
        # TZ Conversion
        if 'created_at' in df_unified.columns:
            df_unified['created_at'] = pd.to_datetime(df_unified['created_at']).dt.tz_convert('America/Caracas')
            
        # Normalización de Prioridad
        if 'priority' in df_unified.columns:
            df_unified['priority_label'] = df_unified['priority'].apply(
                lambda x: '🔴 Alta' if x >= 4 else '🟡 Media' if x == 3 else '🟢 Baja'
            )
        
        # Normalización de Categoría para filtrado
        def normalize_cat(row):
            cat = str(row.get('category', '')).lower()
            if 'ventas' in cat: return 'Ventas'
            if 'soporte' in cat or 'técnico' in cat: return 'Soporte Técnico'
            if 'factura' in cat: return 'Facturación'
            return 'Otros'
        
        df_unified['category_display'] = df_unified.apply(normalize_cat, axis=1)
        
        # Normalización de Estado
        status_map_db = {'open': 'Abierto', 'pending': 'Pendiente', 'closed': 'Cerrado'}
        df_unified['status_display'] = df_unified['status'].map(status_map_db).fillna(df_unified['status'])

        # FILTRADO SECUENCIAL ESTRICTO
        df_filtered = df_unified.copy()
        
        if f_priority != "Todas":
            df_filtered = df_filtered[df_filtered['priority_label'] == f_priority]
            
        if f_category != "Todas":
            df_filtered = df_filtered[df_filtered['category_display'] == f_category]
            
        if f_status != "Todos":
            df_filtered = df_filtered[df_filtered['status_display'] == f_status]

        # Separar para vistas de detalle (pero usando el set filtrado si corresponde)
        df_p = df_filtered[df_filtered['category_display'] == 'Ventas']
        df_t = df_filtered[df_filtered['category_display'] != 'Ventas']
    else:
        df_filtered = pd.DataFrame()
        df_p = pd.DataFrame()
        df_t = pd.DataFrame()

    # --- MAIN CONTENT ---
    if menu == "📊 Dashboard General":
        st.subheader("📋 Resumen de Actividad Reciente")
        
        # Informativos rápidos
        col_inf1, col_inf2 = st.columns(2)
        with col_inf1:
            st.info(f"🚀 **Ventas:** {len(df_p)} registros")
        with col_inf2:
            st.info(f"🛠️ **Soporte:** {len(df_t)} registros")
            
        if not df_filtered.empty:
            # Crear vista de previsualización
            df_resumen = df_filtered.copy().sort_values('created_at', ascending=False)
            
            # Trimming (truncado) del summary
            df_resumen['Mensaje (Previsualización)'] = df_resumen['summary'].apply(
                lambda x: (str(x)[:60] + '...') if len(str(x)) > 60 else x
            )
            
            # Iconos en categoría para la tabla
            df_resumen['Categoría'] = df_resumen['category_display'].apply(
                lambda x: f"🚀 {x}" if x == 'Ventas' else f"🛠️ {x}"
            )
            
            # Formateo de fecha y nombres legibles
            df_resumen['Fecha'] = df_resumen['created_at'].dt.strftime('%Y-%m-%d %H:%M')
            df_resumen = df_resumen.rename(columns={'cliente': 'Cliente', 'priority_label': 'Prioridad'})
            
            # Reordenar columnas
            df_resumen = df_resumen[['Fecha', 'Prioridad', 'Categoría', 'Cliente', 'Mensaje (Previsualización)']]
            
            st.dataframe(df_resumen, use_container_width=True, hide_index=True, height=500)
        else:
            st.warning("No hay registros que coincidan con los filtros seleccionados.")

    elif menu == "🚀 Ventas / Prospects":
        st.subheader("Gestión Detallada de Prospectos")
        if not df_p.empty:
            st.dataframe(df_p, use_container_width=True, hide_index=True, height=600)
        else:
            st.info("No hay datos de ventas para estos filtros.")

    elif menu == "🛠️ Soporte / Tickets":
        st.subheader("Gestión Detallada de Tickets")
        if not df_t.empty:
            # Seleccionar columnas relevantes para detalle
            disp_cols = ['created_at', 'priority_label', 'category', 'cliente', 'status', 'summary']
            df_t_disp = df_t[disp_cols].rename(columns={
                'created_at': 'Fecha', 
                'priority_label': 'Prioridad',
                'cliente': 'Cliente',
                'category': 'Categoría Interna'
            })
            st.dataframe(df_t_disp, use_container_width=True, hide_index=True, height=600)
        else:
            st.info("No hay tickets de soporte para estos filtros.")

    st.markdown("---")
    st.caption("Neural SaaS Platform | WebLanMasters Atención © 2026")

if __name__ == '__main__':
    main()
