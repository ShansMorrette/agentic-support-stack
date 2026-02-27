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

    # Custom CSS for high-end look
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

    # Fetch data
    prospects = fetch_data("/api/atencion/prospects")
    tickets = fetch_data("/api/atencion/tickets?status=open")
    
    # --- METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Prospects", len(prospects), delta=None)
    with col2:
        st.metric("Tickets Abiertos", len(tickets), delta=None, delta_color="inverse")
    with col3:
        # Dummy or integrated from code stats if available
        st.metric("Calidad Promedio", "88/100", delta="+3%")
    with col4:
        st.metric("SLA Cumplido", "96%", delta="99%")

    st.markdown("---")

    # --- MAIN CONTENT ---
    if menu == "📊 Dashboard General":
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🚀 Últimos Prospectos")
            if prospects:
                df_p = pd.DataFrame(prospects)
                if 'created_at' in df_p.columns:
                    df_p['created_at'] = pd.to_datetime(df_p['created_at']).dt.tz_convert('America/Caracas')
                st.dataframe(df_p, use_container_width=True, hide_index=True)
            else:
                st.write("No hay prospectos registrados.")

        with col_right:
            st.subheader("🛠️ Tickets de Soporte Pendientes")
            if tickets:
                df_t = pd.DataFrame(tickets)
                # Map priority to emojis
                if 'priority' in df_t.columns:
                    df_t['priority'] = df_t['priority'].apply(lambda x: '🔴 Alta' if x >= 4 else '🟡 Media' if x == 3 else '🟢 Baja')
                st.dataframe(df_t, use_container_width=True, hide_index=True)
            else:
                st.write("No hay tickets pendientes.")

    elif menu == "🚀 Ventas / Prospects":
        st.subheader("Gestión de Prospectos de Ventas")
        if prospects:
            df_p = pd.DataFrame(prospects)
                if 'created_at' in df_p.columns:
                    df_p['created_at'] = pd.to_datetime(df_p['created_at']).dt.tz_convert('America/Caracas')
            st.table(df_p)
        else:
            st.info("Sin datos de ventas.")

    elif menu == "🛠️ Soporte / Tickets":
        st.subheader("Gestión de Tickets de Soporte")
        if tickets:
            df_t = pd.DataFrame(tickets)
            st.table(df_t)
        else:
            st.info("Sin tickets activos.")

    st.markdown("---")
    st.caption("Neural SaaS Platform | WebLanMasters Atención © 2026")

if __name__ == '__main__':
    main()
