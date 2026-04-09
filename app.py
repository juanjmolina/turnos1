"""
app.py — Sistema de Turnos y Compensatorios
============================================
Punto de entrada principal.

El HTML del sistema está embebido en modules/html_content.py
100% Python — sin archivos .html externos.
GitHub detectará: Python 100%

Uso local:
    pip install streamlit psycopg2-binary
    streamlit run app.py

Producción (PostgreSQL):
    Agrega DATABASE_URL en variables de entorno o Streamlit Secrets.
"""
import json
import streamlit as st
import streamlit.components.v1 as components

from database.db     import init_db, guardar_snapshot, cargar_snapshot, registrar_log
from modules.ui_helpers  import pagina_config, ocultar_ui_streamlit
from modules.logic       import inyectar_sync
from modules.html_content import get_html

# ── 1. Configurar página (primera llamada a Streamlit) ────────
pagina_config()
ocultar_ui_streamlit()

# ── 2. Inicializar base de datos ──────────────────────────────
init_db()

# ── 3. Procesar datos entrantes (guardado desde el frontend) ──
params = st.query_params
if "_save" in params:
    try:
        datos   = json.loads(params["_save"])
        usuario = datos.pop("__usuario__", "web")
        ok = guardar_snapshot("sistema_turnos_v1", datos, usuario)
        if ok:
            registrar_log(usuario, "guardar:sistema_turnos_v1")
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        print(f"[app] Error procesando _save: {e}")

# ── 4. Cargar snapshot más reciente de la BD ──────────────────
snapshot = cargar_snapshot("sistema_turnos_v1")

# ── 5. Obtener HTML e inyectar sincronización ─────────────────
html = get_html()
html = inyectar_sync(html, snapshot)

# ── 6. Renderizar — el sistema aparece idéntico al HTML original
components.html(html, height=960, scrolling=True)
