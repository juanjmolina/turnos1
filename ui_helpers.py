"""
modules/ui_helpers.py
=====================
Configuración de Streamlit: oculta la UI nativa completamente
para que solo se vea el sistema de turnos original.
"""
import streamlit as st


def pagina_config() -> None:
    """Configura la página Streamlit."""
    st.set_page_config(
        page_title="Sistema de Turnos",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def ocultar_ui_streamlit() -> None:
    """
    Inyecta CSS que oculta TODOS los elementos nativos de Streamlit.
    El usuario solo verá el HTML del sistema de turnos.
    """
    st.markdown("""
    <style>
        #MainMenu,
        footer,
        header,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        section[data-testid="stSidebar"] { display: none !important; }

        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
            margin: 0 !important;
        }
        [data-testid="stAppViewContainer"] > div {
            padding: 0 !important;
        }
        [data-testid="stVerticalBlock"] {
            gap: 0 !important;
            padding: 0 !important;
        }
        iframe { border: none !important; display: block !important; }
    </style>
    """, unsafe_allow_html=True)
