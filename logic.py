"""
modules/logic.py
================
Lógica de sincronización: inyecta un <script> al HTML que
conecta localStorage del navegador con la base de datos.
El HTML visual NO se modifica — solo se agrega el script al final.
"""
import json
from typing import Optional


def construir_sync_script(snapshot: Optional[dict]) -> str:
    """
    Genera el bloque <script> de sincronización.
    - Carga datos de la BD en localStorage al abrir la app
    - Conecta el botón 'Guardar en base de datos' con el backend
    - Muestra confirmaciones visuales (toast)
    """
    datos_db = json.dumps(snapshot["datos"]          if snapshot else {})
    hash_db  = json.dumps(snapshot["hash"]            if snapshot else "")
    ts_db    = json.dumps(snapshot["actualizado_en"]  if snapshot else "")

    return f"""
<script>
(function() {{
  var HASH_DB  = {hash_db};
  var DATOS_DB = {datos_db};
  var TS_DB    = {ts_db};
  var MODULOS  = [
    'workers','ausencias','celdasEstado','horasExtras',
    'nextWId','nextAId','filterGrupo','filterAusTipo',
    'filterAusEst','filterAusWk','vac_data','cum_data',
    'comp_ganados','cc_data','che_data'
  ];

  // 1. Cargar datos de la BD en localStorage al abrir
  function cargarDesdeBD() {{
    if (!DATOS_DB || Object.keys(DATOS_DB).length === 0) return;
    if (localStorage.getItem('_db_hash') === HASH_DB) return;
    MODULOS.forEach(function(mod) {{
      if (DATOS_DB[mod] !== undefined) {{
        try {{ localStorage.setItem(mod, JSON.stringify(DATOS_DB[mod])); }}
        catch(e) {{}}
      }}
    }});
    localStorage.setItem('_db_hash', HASH_DB);
    localStorage.setItem('_db_ts', TS_DB);
    setTimeout(function() {{
      ['render','renderHeader','cumRefrescar','vRefrescar',
       'compRefrescar','ccRefrescar'].forEach(function(fn) {{
        if (typeof window[fn] === 'function') window[fn]();
      }});
    }}, 400);
  }}

  // 2. Guardar datos en la BD via query param
  window.guardarEnBD = function() {{
    try {{
      if (typeof buildSnapshot !== 'function') {{
        toast('No se pudo leer el estado actual', '#EF4444'); return;
      }}
      var snap = buildSnapshot();
      var url  = new URL(window.location.href);
      url.searchParams.set('_save', encodeURIComponent(JSON.stringify(snap)));
      toast('Guardando...', '#3B82F6');
      window.location.href = url.toString();
    }} catch(e) {{
      toast('Error: ' + e.message, '#EF4444');
    }}
  }};

  // 3. Interceptar Exportar para guardar en BD también
  function hookExportar() {{
    if (typeof window.exportarDatos !== 'function') return;
    var orig = window.exportarDatos;
    window.exportarDatos = function() {{
      orig();
      try {{
        var snap = buildSnapshot();
        var url  = new URL(window.location.href);
        url.searchParams.set('_save', encodeURIComponent(JSON.stringify(snap)));
        fetch(url.toString()).catch(function() {{}});
        localStorage.setItem('_db_hash', '');
        toast('Exportado y guardado en base de datos', '#10B981');
      }} catch(e) {{}}
    }};
  }}

  // 4. Agregar botón en el panel de Backup existente
  function agregarBotonBD() {{
    var obs = new MutationObserver(function() {{
      var box = document.querySelector('.backup-box');
      if (!box || document.getElementById('_bdSection')) return;
      var sec = document.createElement('div');
      sec.id = '_bdSection';
      sec.className = 'backup-section';
      sec.innerHTML =
        '<h3>🐘 Base de datos</h3>' +
        '<p>Guarda todos los datos en la base de datos del servidor.</p>' +
        '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
          '<button onclick="guardarEnBD()" class="btn btn-primary"' +
            ' style="background:#059669;font-size:.85rem;padding:8px 18px;' +
            'border:none;border-radius:8px;color:#fff;cursor:pointer;font-weight:700">' +
            '🔄 Guardar en base de datos' +
          '</button>' +
          '<span style="font-size:11px;color:#94A3B8">Última sync: ' + (TS_DB || 'Nunca') + '</span>' +
        '</div>';
      box.insertBefore(sec, box.lastElementChild);
      obs.disconnect();
    }});
    obs.observe(document.body, {{ childList: true, subtree: true }});
  }}

  // 5. Toast de notificación
  function toast(msg, color) {{
    var t = document.createElement('div');
    t.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:99999;' +
      'background:' + color + ';color:#fff;border-radius:10px;padding:12px 20px;' +
      'font-size:13px;font-weight:600;box-shadow:0 4px 20px rgba(0,0,0,.2)';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function() {{ t.remove(); }}, 3500);
  }}

  document.addEventListener('DOMContentLoaded', function() {{
    cargarDesdeBD();
    setTimeout(hookExportar, 1200);
    agregarBotonBD();
  }});
}})();
</script>"""


def inyectar_sync(html: str, snapshot: Optional[dict]) -> str:
    """Inyecta el script de sincronización antes del cierre de </body>."""
    script = construir_sync_script(snapshot)
    if "</body>" in html:
        return html.replace("</body>", script + "\n</body>", 1)
    return html + script
