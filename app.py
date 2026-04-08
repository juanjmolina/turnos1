"""
Sistema de Turnos y Compensatorios
Aplicación Flask que sirve el sistema completo como web app.

Para correr localmente:
    pip install flask
    python app.py

Para Streamlit Cloud / plataformas que requieren app.py con Streamlit:
    pip install streamlit
    streamlit run app.py
"""

import os
import sys

# ── Detectar si corre como Streamlit o Flask ──────────────────
def es_streamlit():
    try:
        import streamlit
        # Si streamlit está disponible Y el script se llamó con streamlit run
        return "streamlit" in sys.modules or os.environ.get("STREAMLIT_SERVER_PORT")
    except ImportError:
        return False

# ── Ruta del HTML (mismo directorio que app.py) ───────────────
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

def get_html():
    """Lee el archivo HTML del sistema."""
    if os.path.exists(HTML_FILE):
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: index.html no encontrado. Coloca index.html en la misma carpeta que app.py</h1>"


# ══════════════════════════════════════════════════════════════
# MODO STREAMLIT
# ══════════════════════════════════════════════════════════════
try:
    import streamlit as st

    st.set_page_config(
        page_title="Sistema de Turnos",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Ocultar elementos de Streamlit para que solo se vea la app
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding: 0 !important; max-width: 100% !important;}
        [data-testid="stAppViewContainer"] {padding: 0;}
        [data-testid="stVerticalBlock"] {gap: 0;}
    </style>
    """, unsafe_allow_html=True)

    html_content = get_html()

    # Streamlit renderiza el HTML completo en un componente
    st.components.v1.html(html_content, height=900, scrolling=True)

except ImportError:
    # ══════════════════════════════════════════════════════════
    # MODO FLASK (fallback si no hay streamlit)
    # ══════════════════════════════════════════════════════════
    try:
        from flask import Flask, send_from_directory, Response

        app = Flask(__name__)

        @app.route("/")
        def index():
            html_content = get_html()
            return Response(html_content, mimetype="text/html; charset=utf-8")

        @app.route("/health")
        def health():
            return {"status": "ok", "app": "Sistema de Turnos"}

        if __name__ == "__main__":
            port = int(os.environ.get("PORT", 5000))
            print(f"🏭 Sistema de Turnos corriendo en http://localhost:{port}")
            app.run(host="0.0.0.0", port=port, debug=False)

    except ImportError:
        print("Error: instala flask o streamlit")
        print("  pip install flask")
        print("  pip install streamlit")
        sys.exit(1)
