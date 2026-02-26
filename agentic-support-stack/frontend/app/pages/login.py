"""
Página de Login/Registro - Autenticación de usuarios con JWT.
"""

import os

import requests
import streamlit as st

# Configuración
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Login - Neural Code Analyzer", page_icon="🔐", layout="centered")


# ----------------- FUNCIONES DE AUTH -----------------


def login(email: str, password: str) -> dict:
    """Llamar al backend para login."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error = response.json().get("detail", "Error de autenticación")
            return {"success": False, "error": error}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "No se pudo conectar al servidor"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register(email: str, password: str, full_name: str = None, api_key: str = None) -> dict:
    """Llamar al backend para registro."""
    try:
        payload = {"email": email, "password": password}
        if full_name:
            payload["full_name"] = full_name
        if api_key:
            payload["gemini_api_key"] = api_key

        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json=payload,
            timeout=10,
        )
        if response.status_code == 201:
            return {"success": True, "data": response.json()}
        else:
            error = response.json().get("detail", "Error en registro")
            return {"success": False, "error": error}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "No se pudo conectar al servidor"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ----------------- UI -----------------

# Verificar si ya está logueado
if "token" in st.session_state and st.session_state.token:
    st.success(f"✅ Ya estás logueado como {st.session_state.get('user_email', 'usuario')}")
    if st.button("🚀 Ir al Analizador", type="primary"):
        st.switch_page("main.py")
    if st.button("🚪 Cerrar Sesión"):
        del st.session_state["token"]
        if "user" in st.session_state:
            del st.session_state["user"]
        if "user_email" in st.session_state:
            del st.session_state["user_email"]
        st.rerun()
    st.stop()

# Centrar contenido
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.title("🧠 Neural Code Analyzer")

    # Tabs para Login/Registro
    tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta"])

    # ----------------- TAB LOGIN -----------------
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="tu@email.com")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")

            submit = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.error("⚠️ Completa todos los campos")
                else:
                    with st.spinner("Verificando..."):
                        result = login(email, password)

                    if result["success"]:
                        data = result["data"]
                        st.session_state["token"] = data["access_token"]
                        st.session_state["user"] = data["user"]
                        st.session_state["user_email"] = data["user"]["email"]
                        st.success("✅ Login exitoso!")
                        st.balloons()
                        st.switch_page("main.py")
                    else:
                        st.error(f"❌ {result['error']}")

    # ----------------- TAB REGISTRO -----------------
    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("📧 Email", placeholder="tu@email.com", key="reg_email")
            reg_name = st.text_input("👤 Nombre completo", placeholder="Juan Pérez", key="reg_name")
            reg_password = st.text_input(
                "🔒 Contraseña",
                type="password",
                placeholder="Mínimo 8 caracteres, 1 mayúscula, 1 número",
                key="reg_pass",
            )
            reg_password2 = st.text_input(
                "🔒 Confirmar Contraseña", type="password", placeholder="••••••••", key="reg_pass2"
            )

            st.markdown("---")
            st.markdown("### 🔑 API Key de Gemini (Opcional)")
            st.caption("Si tienes tu propia API key, tendrás análisis ilimitados")
            reg_api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="AIza...",
                key="reg_api",
                help="Obtén tu key en https://makersuite.google.com/app/apikey",
            )

            submit_reg = st.form_submit_button("📝 Crear Cuenta", use_container_width=True, type="primary")

            if submit_reg:
                if not reg_email or not reg_password:
                    st.error("⚠️ Email y contraseña son obligatorios")
                elif reg_password != reg_password2:
                    st.error("⚠️ Las contraseñas no coinciden")
                elif len(reg_password) < 8:
                    st.error("⚠️ La contraseña debe tener al menos 8 caracteres")
                else:
                    with st.spinner("Creando cuenta..."):
                        result = register(
                            email=reg_email,
                            password=reg_password,
                            full_name=reg_name or None,
                            api_key=reg_api_key or None,
                        )

                    if result["success"]:
                        st.success("✅ Cuenta creada exitosamente!")
                        st.info("Ahora puedes iniciar sesión en la pestaña 'Iniciar Sesión'")
                    else:
                        st.error(f"❌ {result['error']}")

    st.markdown("---")

    # Modo demo
    st.markdown("### 🎯 Modo Demo")
    st.caption("Prueba la aplicación sin registrarte (funciones limitadas)")

    if st.button("🚀 Continuar sin Login", use_container_width=True):
        st.session_state["token"] = None
        st.session_state["user"] = None
        st.switch_page("main.py")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ by Neural SaaS Platform | v1.0.0</div>",
    unsafe_allow_html=True,
)

