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

    # Pre-processing
    df_p_orig = pd.DataFrame(prospects)
    df_t_orig = pd.DataFrame(tickets)

    # Universal TZ Conversion
    for df in [df_p_orig, df_t_orig]:
        if not df.empty and 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('America/Caracas')

    # Mapping for tickets
    if not df_t_orig.empty and 'priority' in df_t_orig.columns:
        df_t_orig['priority_label'] = df_t_orig['priority'].apply(lambda x: '🔴 Alta' if x >= 4 else '🟡 Media' if x == 3 else '🟢 Baja')

    # Filtering Logic (Applied to detail views and summary)
    df_p = df_p_orig.copy()
    df_t = df_t_orig.copy()
    
    if not df_t.empty:
        if f_priority != "Todas":
            df_t = df_t[df_t['priority_label'] == f_priority]
        if f_category != "Todas":
            df_t = df_t[df_t['category'].str.contains(f_category.split()[-1], case=False, na=False)]
        if f_status != "Todos":
            status_map = {"Abierto": "open", "Pendiente": "pending", "Cerrado": "closed"}
            df_t = df_t[df_t['status'] == status_map.get(f_status, "open")]

    # --- MAIN CONTENT ---
    if menu == "📊 Dashboard General":
        st.subheader("📋 Resumen de Actividad Reciente")
        
        # Informativos rápidos
        col_inf1, col_inf2 = st.columns(2)
        with col_inf1:
            st.info(f"🚀 **Ventas:** {len(df_p)} prospectos")
        with col_inf2:
            st.info(f"🛠️ **Soporte:** {len(df_t)} tickets")
            
        # Unificación de datos para la tabla única
        parts = []
        if not df_p.empty:
            p_sub = df_p[['created_at']].copy()
            p_sub['Categoría'] = "🚀 Ventas"
            p_sub['Prioridad'] = "🟢 Baja"
            parts.append(p_sub)
        
        if not df_t.empty:
            t_sub = df_t[['created_at', 'category', 'priority_label']].copy()
            t_sub = t_sub.rename(columns={'category': 'Categoría', 'priority_label': 'Prioridad'})
            # Asegurar icono en categoría de soporte
            t_sub['Categoría'] = t_sub['Categoría'].apply(lambda x: f"🛠️ {x}")
            parts.append(t_sub)
            
        if parts:
            df_resumen = pd.concat(parts).sort_values('created_at', ascending=False)
            df_resumen['Fecha'] = df_resumen['created_at'].dt.strftime('%Y-%m-%d %H:%M')
            df_resumen = df_resumen[['Categoría', 'Prioridad', 'Fecha']]
            
            st.dataframe(df_resumen, use_container_width=True, hide_index=True, height=500)
        else:
            st.write("No hay actividad reciente para mostrar.")

    elif menu == "🚀 Ventas / Prospects":
        st.subheader("Gestión Detallada de Prospectos")
        if not df_p.empty:
            st.dataframe(df_p, use_container_width=True, hide_index=True, height=600)
        else:
            st.info("Sin datos de ventas.")

    elif menu == "🛠️ Soporte / Tickets":
        st.subheader("Gestión Detallada de Tickets")
        if not df_t.empty:
            # Map labels for display
            cols = list(df_t.columns)
            if 'priority_label' in cols:
                df_t_disp = df_t.drop(columns=['priority']).rename(columns={'priority_label': 'Prioridad'})
            else:
                df_t_disp = df_t
            st.dataframe(df_t_disp, use_container_width=True, hide_index=True, height=600)
        else:
            st.info("Sin tickets activos para los filtros seleccionados.")

    st.markdown("---")
    st.caption("Neural SaaS Platform | WebLanMasters Atención © 2026")

if __name__ == '__main__':
    main()
