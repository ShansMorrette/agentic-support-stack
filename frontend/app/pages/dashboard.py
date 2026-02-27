"""
Página de Dashboard - Estadísticas y métricas del usuario.
Conecta con el backend para obtener datos reales de la base de datos.
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# Configuración
BACKEND_URL = os.getenv("BACKEND_URL", "http://app:8001")

st.set_page_config(
    page_title="Dashboard - Neural Code Analyzer",
    page_icon="📊",
    layout="wide"
)


# ----------------- HELPERS -----------------

def get_auth_headers() -> dict:
    """Obtener headers con token JWT si está logueado."""
    if "token" in st.session_state and st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def is_logged_in() -> bool:
    """Verificar si el usuario está logueado."""
    return "token" in st.session_state and st.session_state.token is not None


def get_stats_from_backend() -> dict:
    """Obtener estadísticas del backend."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/analysis/stats",
            headers=get_auth_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error al obtener estadísticas: {e}")
    return {}


def get_history_from_backend(limit: int = 20) -> dict:
    """Obtener historial del backend."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/analysis/history?limit={limit}",
            headers=get_auth_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error al obtener historial: {e}")
    return {"analyses": [], "total": 0}


# ----------------- INSIGHTS Y LOGROS -----------------

def generar_insight(historial: list, score_promedio: float, total_analisis: int) -> str:
    """Genera un insight personalizado basado en los datos del usuario."""
    if total_analisis < 3:
        return "🔍 Sigue analizando código para obtener insights personalizados"
    
    # Calcular tendencia (últimos 5 vs anteriores 5)
    scores = [h.get('quality_score') for h in historial if h.get('quality_score')]
    if len(scores) >= 6:
        recientes = sum(scores[:3]) / 3
        anteriores = sum(scores[3:6]) / 3
        tendencia = recientes - anteriores
        
        if tendencia > 5:
            return f"📈 ¡Vas mejorando! Tu score subió **+{tendencia:.0f} puntos** recientemente"
        elif tendencia < -5:
            return f"📉 Tu score bajó **{abs(tendencia):.0f} puntos**. ¡Revisa las sugerencias!"
    
    # Verificar scores excelentes recientes
    if any(s >= 95 for s in scores[:3] if s):
        return "🎯 ¡Excelente! Lograste scores de **95+** recientemente"
    
    # Verificar consistencia
    if all(s >= 80 for s in scores[:5] if s):
        return "🔥 ¡Racha de calidad! Todos tus últimos análisis tienen **80+**"
    
    # Tip genérico basado en score promedio
    if score_promedio >= 85:
        return "💪 Tu código es de alta calidad. ¡Sigue así!"
    elif score_promedio >= 70:
        return "💡 Tip: Revisa los 'code smells' para subir tu score a 90+"
    else:
        return "📚 Enfócate en type hints y manejo de excepciones para mejorar"


def verificar_logros(total_analisis: int, score_promedio: float, scores: list) -> list:
    """Verifica qué logros ha desbloqueado el usuario."""
    logros_desbloqueados = []
    
    logros = {
        1: ("🎉", "Primer Análisis", "¡Completaste tu primer análisis!"),
        5: ("🔰", "Primeros Pasos", "5 análisis completados"),
        10: ("📚", "Aprendiz", "10 análisis completados"),
        25: ("🏅", "Constante", "25 análisis completados"),
        50: ("🏆", "Code Master", "50 análisis completados"),
        100: ("💎", "Experto", "100 análisis completados"),
    }
    
    for meta, (emoji, nombre, desc) in logros.items():
        if total_analisis >= meta:
            logros_desbloqueados.append((emoji, nombre, desc, meta))
    
    # Logros por score
    if any(s >= 95 for s in scores if s):
        logros_desbloqueados.append(("⭐", "Excelencia", "Score de 95+ alcanzado", 95))
    
    if score_promedio >= 90:
        logros_desbloqueados.append(("🌟", "Calidad Premium", "Score promedio de 90+", 90))
    
    return logros_desbloqueados


# ----------------- VERIFICAR LOGIN -----------------

if not is_logged_in():
    st.warning("🔐 Debes iniciar sesión para ver tu dashboard")
    if st.button("🔑 Ir a Login", type="primary"):
        st.switch_page("pages/login.py")
    st.stop()

# Título
st.title("📊 Dashboard")
user = st.session_state.get("user", {})
st.markdown(f"### Estadísticas de **{user.get('email', 'Usuario')}**")
st.markdown("---")

# Obtener datos del backend
stats = get_stats_from_backend()
history_data = get_history_from_backend(limit=20)
historial = history_data.get("analyses", [])

# Sidebar
with st.sidebar:
    st.header("👤 Tu Cuenta")
    
    # Info del usuario
    st.success(f"📧 {user.get('email', 'Usuario')}")
    st.caption(f"Plan: **{user.get('role', 'free').upper()}**")
    
    if stats.get("tiene_api_propia"):
        st.caption("🔑 API Key propia configurada")
    
    st.markdown("---")
    
    # Límite diario con progreso
    st.header("📊 Uso Diario")
    analisis_hoy = stats.get("analisis_hoy", 0)
    limite_diario = stats.get("limite_diario", 5)
    restantes = max(0, limite_diario - analisis_hoy)
    
    st.metric("Análisis Hoy", f"{analisis_hoy}/{limite_diario}", f"{restantes} restantes")
    st.progress(min(analisis_hoy / limite_diario, 1.0) if limite_diario > 0 else 0)
    
    st.markdown("---")
    
    # Botón de actualizar
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.rerun()
    
    # Volver a análisis
    if st.button("🏠 Ir a Análisis", use_container_width=True, type="primary"):
        st.switch_page("main.py")

# Métricas del backend (asegurar tipos numéricos)
total_analisis = int(stats.get("total_analisis", 0) or 0)
score_promedio = float(stats.get("score_promedio", 0) or 0)
analisis_hoy = int(stats.get("analisis_hoy", 0) or 0)
limite_diario = int(stats.get("limite_diario", 5) or 5)

# Calcular estadísticas del historial
scores = [h.get('quality_score') for h in historial if h.get('quality_score') is not None]
excelentes = sum(1 for s in scores if s and s >= 90)
buenos = sum(1 for s in scores if s and 70 <= s < 90)

# ============== INSIGHT AUTOMÁTICO ==============
insight = generar_insight(historial, score_promedio, total_analisis)
st.info(f"💡 **Insight:** {insight}")
st.markdown("")

# Métricas principales
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📝 Análisis Totales",
        value=total_analisis,
        delta=f"+{analisis_hoy} hoy" if analisis_hoy > 0 else None,
        help="Total de análisis realizados"
    )

with col2:
    # Emoji según score
    emoji = "🟢" if score_promedio >= 90 else "🟡" if score_promedio >= 70 else "🟠" if score_promedio >= 50 else "🔴"
    st.metric(
        label=f"{emoji} Score Promedio",
        value=f"{score_promedio}/100",
        delta=None,
        help="Score promedio de calidad de código"
    )

with col3:
    st.metric(
        label="🏆 Excelentes (90+)",
        value=excelentes,
        delta=None,
        help="Análisis con score 90 o más"
    )

with col4:
    st.metric(
        label="👍 Buenos (70-89)",
        value=buenos,
        delta=None,
        help="Análisis con score entre 70 y 89"
    )

st.markdown("---")

# Gráficos y tablas
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Evolución de Scores")
    
    if len(historial) > 0:
        # Crear DataFrame con el historial del backend
        df = pd.DataFrame(historial)
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Gráfico de línea de scores
        if 'quality_score' in df.columns and df['quality_score'].notna().any():
            scores_df = df[df['quality_score'].notna()].copy()
            scores_df = scores_df.sort_values('created_at')
            
            st.line_chart(
                data=scores_df.set_index('created_at')['quality_score'],
                use_container_width=True,
                height=200
            )
        else:
            st.info("📊 Realiza más análisis para ver el gráfico de evolución")
    else:
        st.info("📊 Aún no hay análisis. Ve a la página principal para analizar código.")
    
    st.markdown("---")
    
    # Tabla de análisis recientes
    st.subheader("📋 Historial de Análisis")
    
    if len(historial) > 0:
        # Crear tabla con datos del backend
        tabla_data = []
        for h in historial:
            tabla_data.append({
                "Fecha": pd.to_datetime(h['created_at']).strftime('%Y-%m-%d %H:%M'),
                "Código": h.get('code_preview', 'N/A'),
                "Score": h.get('quality_score', '-') or '-',
                "Modelo": h.get('model_used', 'N/A')
            })
        
        df_tabla = pd.DataFrame(tabla_data)
        st.dataframe(
            df_tabla,
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Mostrando {len(historial)} de {history_data.get('total', 0)} análisis")
    else:
        st.info("📝 No hay análisis recientes. Comienza analizando código en la página principal.")

with col_right:
    st.subheader("📊 Distribución de Scores")
    
    if len(scores) > 0:
        # Distribución de scores
        regulares = sum(1 for s in scores if s and 50 <= s < 70)
        mejorables = sum(1 for s in scores if s and s < 50)
        
        score_data = {
            "🟢 Excelente (90+)": excelentes,
            "🟡 Bueno (70-89)": buenos,
            "🟠 Regular (50-69)": regulares,
            "🔴 Mejorable (<50)": mejorables
        }
        
        for rango, cantidad in score_data.items():
            if cantidad > 0:
                porcentaje = (cantidad / len(scores)) * 100
                st.metric(rango, cantidad, f"{porcentaje:.0f}%")
    else:
        st.info("📊 Realiza análisis para ver estadísticas")
    
    st.markdown("---")
    
    st.subheader("💡 Tu Nivel")
    
    if score_promedio > 0:
        if score_promedio >= 90:
            st.success("🏆 **Experto**\n\n¡Tu código es de alta calidad!")
        elif score_promedio >= 70:
            st.info("👍 **Avanzado**\n\nBuen trabajo, sigue mejorando.")
        elif score_promedio >= 50:
            st.warning("📚 **Intermedio**\n\nRevisa las sugerencias de mejora.")
        else:
            st.error("🎯 **Principiante**\n\nEnfócate en las buenas prácticas.")
    
    st.markdown("---")
    
    st.subheader("📌 Tips Rápidos")
    st.markdown("""
    - ✅ Type hints en funciones
    - ✅ Docstrings descriptivos
    - ✅ Manejo de excepciones
    - ✅ Nombres claros
    - ✅ Funciones pequeñas
    """)

# ============== LOGROS DESBLOQUEADOS ==============
st.markdown("---")
st.subheader("🏆 Tus Logros")

logros = verificar_logros(total_analisis, score_promedio, scores)

if logros:
    # Mostrar logros en columnas
    cols = st.columns(min(len(logros), 4))
    for i, (emoji, nombre, desc, meta) in enumerate(logros[-4:]):  # Últimos 4 logros
        with cols[i % 4]:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin: 5px;">
                <span style="font-size: 2em;">{emoji}</span><br>
                <strong style="color: white;">{nombre}</strong><br>
                <small style="color: #ddd;">{desc}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Próximo logro
    proximos = {5: "🔰 Primeros Pasos", 10: "📚 Aprendiz", 25: "🏅 Constante", 50: "🏆 Code Master", 100: "💎 Experto"}
    for meta, nombre in proximos.items():
        if total_analisis < meta:
            faltantes = meta - total_analisis
            st.caption(f"🎯 Próximo logro: **{nombre}** - Te faltan {faltantes} análisis")
            break
else:
    st.info("🎯 ¡Realiza tu primer análisis para desbloquear logros!")

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3, col_footer4 = st.columns(4)

with col_footer1:
    if total_analisis > 0:
        st.success(f"✅ **{total_analisis}** análisis")
    else:
        st.info("💡 Comienza a analizar")

with col_footer2:
    restantes = max(0, limite_diario - analisis_hoy)
    if restantes > 0:
        st.info(f"📊 **{restantes}** restantes hoy")
    else:
        st.warning("⚠️ Límite alcanzado")

with col_footer3:
    # Exportar historial como CSV
    if len(historial) > 0:
        csv_data = "Fecha,Score,Modelo,Código Preview\n"
        for h in historial:
            fecha = h.get('created_at', 'N/A')[:19]
            score = h.get('quality_score', 'N/A')
            modelo = h.get('model_used', 'N/A')
            codigo = h.get('code_preview', '').replace('"', "'").replace('\n', ' ')[:50]
            csv_data += f'"{fecha}",{score},"{modelo}","{codigo}"\n'
        
        st.download_button(
            "📥 Exportar CSV",
            csv_data,
            file_name="historial_analisis.csv",
            mime="text/csv",
            use_container_width=True
        )

with col_footer4:
    st.caption(f"🔗 `{BACKEND_URL}`")
