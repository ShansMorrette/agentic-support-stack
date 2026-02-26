"""
Componentes reutilizables para el frontend de Streamlit.
"""

import streamlit as st
from typing import Optional


def render_code_editor(
    label: str = "Código Python",
    height: int = 400,
    placeholder: str = "# Tu código aquí...",
    help_text: Optional[str] = None
) -> str:
    """
    Renderiza un editor de código con syntax highlighting.
    
    Args:
        label: Etiqueta del editor
        height: Altura del editor en píxeles
        placeholder: Texto placeholder
        help_text: Texto de ayuda
    
    Returns:
        str: Código ingresado por el usuario
    """
    return st.text_area(
        label,
        height=height,
        placeholder=placeholder,
        help=help_text or "Escribe o pega tu código Python aquí"
    )


def render_metric_card(label: str, value: str, delta: Optional[str] = None):
    """
    Renderiza una tarjeta de métrica.
    
    Args:
        label: Etiqueta de la métrica
        value: Valor de la métrica
        delta: Cambio en la métrica (opcional)
    """
    st.metric(label=label, value=value, delta=delta)


def render_analysis_result(
    analysis_text: str,
    timestamp: str,
    model_used: str,
    show_download: bool = True
):
    """
    Renderiza los resultados del análisis de código.
    
    Args:
        analysis_text: Texto del análisis en formato Markdown
        timestamp: Timestamp del análisis
        model_used: Modelo de IA usado
        show_download: Si mostrar botón de descarga
    """
    st.success("✅ Análisis completado!")
    
    # Timestamp
    st.caption(f"🕐 {timestamp}")
    
    # Análisis
    st.markdown(analysis_text)
    
    # Información adicional
    with st.expander("ℹ️ Información del Análisis"):
        st.json({
            "modelo_usado": model_used,
            "timestamp": timestamp
        })
    
    # Botón de descarga
    if show_download:
        from datetime import datetime
        st.download_button(
            label="📥 Descargar Análisis",
            data=analysis_text,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )


def render_error_message(error_type: str, message: str):
    """
    Renderiza un mensaje de error formateado.
    
    Args:
        error_type: Tipo de error (timeout, connection, etc.)
        message: Mensaje de error
    """
    error_icons = {
        "timeout": "⏱️",
        "connection": "🔌",
        "validation": "⚠️",
        "server": "🔥",
        "unknown": "❌"
    }
    
    icon = error_icons.get(error_type, "❌")
    st.error(f"{icon} {message}")


def render_loading_spinner(message: str = "Procesando..."):
    """
    Renderiza un spinner de carga.
    
    Args:
        message: Mensaje a mostrar durante la carga
    
    Returns:
        Context manager para usar con 'with'
    """
    return st.spinner(message)


def render_sidebar_stats(
    analyses_today: int = 0,
    avg_score: float = 0.0,
    total_analyses: int = 0
):
    """
    Renderiza estadísticas en el sidebar.
    
    Args:
        analyses_today: Análisis realizados hoy
        avg_score: Score promedio
        total_analyses: Total de análisis
    """
    st.markdown("### 📊 Estadísticas")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Hoy", str(analyses_today))
    with col2:
        st.metric("Score", f"{avg_score:.1f}")
    
    if total_analyses > 0:
        st.metric("Total", str(total_analyses))


def render_info_box(title: str, content: str, icon: str = "ℹ️"):
    """
    Renderiza una caja de información.
    
    Args:
        title: Título de la caja
        content: Contenido en formato Markdown
        icon: Icono a mostrar
    """
    st.markdown(f"### {icon} {title}")
    st.markdown(content)


def render_button_group(buttons: list[dict]) -> Optional[str]:
    """
    Renderiza un grupo de botones en columnas.
    
    Args:
        buttons: Lista de diccionarios con configuración de botones
                 Cada dict debe tener: label, key, type (opcional), icon (opcional)
    
    Returns:
        str: Key del botón presionado, o None
    """
    cols = st.columns(len(buttons))
    
    for idx, button_config in enumerate(buttons):
        with cols[idx]:
            label = button_config.get("label", "Button")
            key = button_config.get("key", f"btn_{idx}")
            btn_type = button_config.get("type", "secondary")
            
            if st.button(label, key=key, type=btn_type, use_container_width=True):
                return key
    
    return None
