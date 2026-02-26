import os
import requests
import streamlit as st

# Backend base URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def main():
    st.set_page_config(page_title="WebLanMasters - Atención", layout="wide")
    st.title("WebLanMasters - Atención")
    st.markdown("---")

    colA, colB = st.columns([1, 1])
    # Prospectos (Ventas)
    with colA:
        st.header("🚀 Prospectos (Ventas)")
        try:
            resp = requests.get(f"{BACKEND_URL}/api/atencion/prospects", timeout=5)
            data = resp.json() if resp.status_code == 200 else []
        except Exception:
            data = []
        st.json(data)

    # Soporte (Tickets)
    with colB:
        st.header("🛠️ Soporte (Tickets)")
        try:
            resp = requests.get(f"{BACKEND_URL}/api/atencion/tickets?status=open", timeout=5)
            data = resp.json() if resp.status_code == 200 else []
        except Exception:
            data = []
        st.json(data)

    st.markdown("---")


if __name__ == '__main__':
    main()
