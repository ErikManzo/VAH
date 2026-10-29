# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/busquedas.py — Búsqueda de Cliente y Filtro (materiales)
VERSIÓN FINAL CORREGIDA
CORRECCIÓN: Scroll automático al último ítem añadido en tablas
Última actualización: 2026
"""
from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QTimer, QObject, QEvent
from PyQt6.QtWidgets import QListWidgetItem, QMessageBox, QListWidget
import logging
import sys
import os

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar función para detectar tipos de paquete
try:
    from presupuestos.core.utils import es_tipo_paquete
except ImportError:
    def es_tipo_paquete(tipo: str) -> bool:
        tipo_up = (tipo or "").strip().upper()
        tipos_paquete = [
            "PAQUETE ALUMINIO", "PAQUETE ALUMIO", "PAQ-AL", "PAQ AL",
            "PAQUETE HERRAJES", "PAQUETE HERRAJE", "PAQ-HR", "PAQ HR"
        ]
        return any(tp in tipo_up for tp in tipos_paquete)

# ============================================================================
# IMPORTACIÓN PARA EL DIÁLOGO DE CLIENTE (fallback)
# ============================================================================
try:
    from presupuestos.ui.dialogs.nuevo_cliente_dialog import NuevoClienteDialog
except ImportError:
    class NuevoClienteDialog:
        def __init__(self, svc, titulo_sugerido="", parent=None):
            self.svc = svc
            self.titulo_sugerido = titulo_sugerido
            self.parent = parent
            self.cliente_guardado = None
        def exec(self):
            return 0

# ----------------- Normalización -----------------
def normalize_token(s: str) -> str:
    import unicodedata
    s = (s or "").upper()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _normalize_buscar_por(s: str) -> str:
    t = normalize_token(s)
    if t.startswith("CL"): return "CLAVE"
    if t.startswith("DE"): return "DESCRIPCION"
    return "CLAVE"

# ----------------- Mapa TIPO → tabla (CON PREFIJOS DE BD) -----------------
_TABLE_MAP = {
    "ALUMINIO": "[aluminio].dbo.materiales_aluminio",
    "PAQUETE ALUMINIO": "[aluminio].dbo.paquetes_aluminio",
    "HERRAJES": "[herrajes].dbo.materiales_herraje",
    "PAQUETE HERRAJES": "[herrajes].dbo.paquetes_herrajes",
    "HERRERIA": "[herreria].dbo.materiales_herreria",
    "HERRERÍA": "[herreria].dbo.materiales_herreria",
    "OTROS": "[otros].dbo.materiales_otros",
    "PLASTICOS": "[plasticos].dbo.materiales_plasticos",
    "PLÁSTICOS": "[plasticos].dbo.materiales_plasticos",
    "VIDRIO": "[vidrio].dbo.materiales_vidrio",
}

def _table_for_tipo(tipo_raw: str) -> Optional[str]:
    t = (tipo_raw or "").strip()
    if not t: return None
    return _TABLE_MAP.get(t) or _TABLE_MAP.get(normalize_token(t))

# ----------------- Servicio de consulta -----------------
def _svc_query(window, tipo_raw: str, buscar_raw: str, filtro_raw: str) -> List[Dict[str, Any]]:
    tabla = _table_for_tipo(tipo_raw)
    buscar = _normalize_buscar_por(buscar_raw)
    filtro = (filtro_raw or "").strip().upper()
    if not tabla: return []
    try:
        rows = window.svc.buscar_por_tabla(tabla=tabla, buscar_por=buscar, filtro=filtro)
        if rows: return rows
    except Exception:
        pass
    return []

def search_rows_uniform(window, tipo_raw: str, buscar_raw: str, filtro: str) -> List[Dict[str, Any]]:
    return _svc_query(window, tipo_raw, buscar_raw, filtro)

# ----------------- FUNCIONES COMUNES PARA LISTAS DE BÚSQUEDA -----------------
def setup_list_behavior(list_widget, accept_callback):
    """Configura comportamiento básico de lista de búsqueda."""
    list_widget.itemClicked.connect(lambda item: accept_callback(item))
    list_widget.itemActivated.connect(lambda item: accept_callback(item))

# ----------------- EVENT FILTER PARA MANEJO DE TECLA ENTER -----------------
class ListaClienteEventFilter(QObject):
    """CORRECCIÓN 1.1: Event filter para manejar tecla Enter en lista de clientes."""
    def __init__(self, window):
        super().__init__()
        self.window = window

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self._handle_enter_key()
                return True
        return super().eventFilter(obj, event)

    def _handle_enter_key(self):
        try:
            if not self.window.lst_clientes.isVisible():
                return False
            it = self.window.lst_clientes.currentItem()
            if it is None and self.window.lst_clientes.count() > 0:
                self.window.lst_clientes.setCurrentRow(0)
                it = self.window.lst_clientes.currentItem()
            if it:
                pick_cliente(self.window, it)
                return True
            return False
        except Exception as e:
            logger.error(f"Error en event filter de clientes: {e}")
            return False

# ----------------- Interacción (barra de búsqueda de materiales) -----------------
def after_choose_filtro(window):
    try:
        window.lst_result.clear()
        window.lst_result.setVisible(False)
        window.le_filtro.clear()
        window.le_filtro.setFocus()
    except Exception:
        pass

def do_search(window):
    """Búsqueda incremental en FILTRO."""
    filtro = (window.le_filtro.text() or "").strip()
    if not filtro:
        window.lst_result.clear()
        window.lst_result.setVisible(False)
        return
    try:
        tipo_raw = (window.cbo_tipo.currentText() or "").strip()
        buscar_raw = (window.cbo_buscar.currentText() or "").strip()
        rows = search_rows_uniform(window, tipo_raw, buscar_raw, filtro)
        error_msg = None
    except Exception as e:
        rows = []
        error_msg = str(e)
    
    window.lst_result.clear()
    if error_msg:
        it = QListWidgetItem(f"— ERROR: {error_msg} —")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_result.addItem(it)
        window.lst_result.setVisible(True)
        return
    
    if not rows:
        it = QListWidgetItem("— SIN RESULTADOS —")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_result.addItem(it)
        window.lst_result.setVisible(True)
        return
    
    for r in rows:
        clave = str(r.get("clave", "")).strip()
        desc = str(r.get("descripcion", "")).strip()
        it = QListWidgetItem(f"{clave} — {desc}")
        it.setData(Qt.ItemDataRole.UserRole, r)
        window.lst_result.addItem(it)
    
    window.lst_result.setVisible(True)
    window.lst_result.setCurrentRow(0)

def on_pick_result(window, item):
    """Usuario selecciona un material/paquete de la lista."""
    rec = item.data(Qt.ItemDataRole.UserRole) or {}
    tipo = (window.cbo_tipo.currentText() or "").strip()
    color = (window.cbo_color.currentText() or "").strip()
    clave = str(rec.get("clave", "")).strip()
    desc = str(rec.get("descripcion", "")).strip()
    texto_filtro = f"{clave} — {desc}"
    
    if es_tipo_paquete(tipo):
        window._on_pick_result_paquete(item)
        window.le_filtro.setText(texto_filtro)
        window.lst_result.clear()
        window.lst_result.setVisible(False)
        return
    
    try:
        ancho = float(window.sp_ancho.value())
    except Exception:
        ancho = 0.0
    try:
        alto = float(window.sp_alto.value())
    except Exception:
        alto = 0.0
    
    t_up = (tipo or "").upper()
    tnorm = (t_up.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U"))
    
    if tnorm.startswith("HERRERIA"):
        window._add_he(rec, tipo, color, ancho, alto, 1)
        target_tbl = window.tbl_he
        row = target_tbl.rowCount() - 1
        focus_col = window.H_CA
    else:
        window._add_std(rec, tipo, color, ancho, alto, 1)
        target_tbl = window.tbl
        row = target_tbl.rowCount() - 1
        if tnorm.startswith("ALUMINIO"):
            if "PAQUETE" not in t_up:
                focus_col = window.C_CA
            else:
                focus_col = window.C_ANCHO
        elif tnorm.startswith("VIDRIO"):
            focus_col = window.C_ANCHO
        elif tnorm.startswith("HERRAJES"):
            focus_col = window.C_PZAS
        else:
            focus_col = window.C_PZAS
    
    window.le_filtro.setText(texto_filtro)
    window.lst_result.clear()
    window.lst_result.setVisible(False)
    
    def _focus_new_row():
        try:
            target_tbl.setFocus()
            target_tbl.setCurrentCell(row, focus_col)
            # CORRECCIÓN: Scroll automático al último ítem añadido
            item_to_scroll = target_tbl.item(row, focus_col)
            if item_to_scroll is not None:
                target_tbl.scrollToItem(item_to_scroll, target_tbl.ScrollHint.PositionAtCenter)
            it = target_tbl.item(row, focus_col)
            if it is not None:
                target_tbl.editItem(it)
        except Exception:
            pass
    
    QTimer.singleShot(0, _focus_new_row)

# ----------------- CLIENTES -----------------
def format_cliente_for_list(rec: Dict[str, Any]) -> str:
    def take(*keys):
        for k in keys:
            v = rec.get(k)
            if v is not None:
                s = str(v).strip()
                if s:
                    return s
        return ""
    
    titulo = take("titulo", "TITULO")
    nombre = take("nombre", "NOMBRE")
    ap = take("a_paterno", "A_PATERNO", "APELLIDO_PATERNO", "APELLIDO1")
    am = take("a_materno", "A_MATERNO", "APELLIDO_MATERNO", "APELLIDO2")
    full = " ".join(x for x in [titulo, nombre, ap, am] if x)
    return full.upper() if full else (nombre or ap or am or "(SIN NOMBRE)").upper()

def clientes_start_search(window, text: str):
    """Búsqueda incremental de clientes."""
    text = (text or "").strip()
    if not text:
        window.lst_clientes.clear()
        window.lst_clientes.setVisible(False)
        return
    try:
        rows = window.svc.clientes_buscar(text)
        error_msg = None
    except Exception as e:
        rows = []
        error_msg = str(e)
    
    window.lst_clientes.clear()
    if error_msg:
        it = QListWidgetItem(f"ERROR: {error_msg}")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_clientes.addItem(it)
        window.lst_clientes.setVisible(True)
        window.btn_nuevo_cliente.setEnabled(True)
        return
    
    if not rows:
        it = QListWidgetItem("— SIN RESULTADOS —")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_clientes.addItem(it)
        window.lst_clientes.setVisible(True)
        window.btn_nuevo_cliente.setEnabled(True)
        return
    
    for r in rows:
        it = QListWidgetItem(format_cliente_for_list(r))
        it.setData(Qt.ItemDataRole.UserRole, r)
        window.lst_clientes.addItem(it)
    
    if window.lst_clientes.count() > 1:
        window.lst_clientes.sortItems(Qt.SortOrder.AscendingOrder)
    
    window.lst_clientes.setVisible(True)
    window.lst_clientes.setCurrentRow(0)

def accept_current_cliente(window):
    """Acepta el cliente actualmente seleccionado en la lista."""
    if not window.lst_clientes.isVisible():
        return
    it = window.lst_clientes.currentItem()
    if it is None and window.lst_clientes.count() > 0:
        window.lst_clientes.setCurrentRow(0)
        it = window.lst_clientes.currentItem()
    if it:
        pick_cliente(window, it)
    else:
        window.btn_nuevo_cliente.setEnabled(True)

def pick_cliente(window, it: QListWidgetItem):
    """Selecciona un cliente de la lista y lo pega en el campo CLIENTE."""
    rec = it.data(Qt.ItemDataRole.UserRole) or {}
    texto = format_cliente_for_list(rec)
    window.le_cliente.setText(texto)
    window.btn_nuevo_cliente.setEnabled(False)
    window.lst_clientes.clear()
    window.lst_clientes.setVisible(False)
    window.le_obra.setFocus()

def _obtener_ultimo_cliente_id(window):
    """Obtiene el ID del último cliente registrado."""
    try:
        sql = "SELECT MAX(id) FROM [clientes].dbo.clientes"
        with window.svc.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            return row[0] if row and row[0] else 0
    except Exception:
        return 0

def _obtener_cliente_por_id(window, cliente_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene los datos de un cliente por su ID."""
    try:
        sql = """
        SELECT titulo, nombre, a_paterno, a_materno
        FROM [clientes].dbo.clientes
        WHERE id = ?
        """
        with window.svc.cursor() as cur:
            cur.execute(sql, [cliente_id])
            row = cur.fetchone()
            if row:
                return {
                    "titulo": row[0],
                    "nombre": row[1],
                    "a_paterno": row[2],
                    "a_materno": row[3]
                }
    except Exception as e:
        logger.error(f"Error obteniendo cliente {cliente_id}: {e}")
    return None

def _iniciar_polling_nuevo_cliente(window, proceso, ultimo_id_antes):
    """Inicia un timer para detectar cuando se registre un nuevo cliente."""
    from PyQt6.QtCore import QTimer
    
    def verificar():
        if proceso.poll() is None:
            QTimer.singleShot(2000, verificar)
            return
        ultimo_id_despues = _obtener_ultimo_cliente_id(window)
        if ultimo_id_despues > ultimo_id_antes:
            cliente = _obtener_cliente_por_id(window, ultimo_id_despues)
            if cliente:
                partes = []
                if cliente.get("titulo"): partes.append(cliente["titulo"])
                if cliente.get("nombre"): partes.append(cliente["nombre"])
                if cliente.get("a_paterno"): partes.append(cliente["a_paterno"])
                if cliente.get("a_materno"): partes.append(cliente["a_materno"])
                nombre_completo = " ".join(partes)
                window.le_cliente.setText(nombre_completo)
                window.btn_nuevo_cliente.setEnabled(False)
                window.le_obra.setFocus()
            else:
                pass
        else:
            pass
    QTimer.singleShot(1000, verificar)

def nuevo_cliente(window):
    """
    Abre el módulo de clientes como proceso externo con PYTHONPATH configurado.
    SIN AVISOS - Solo abre el módulo y detecta automáticamente el nuevo cliente.
    """
    try:
        import subprocess
        import sys
        import os
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        clientes_path = os.path.join(project_root, "clientes", "art", "pantalla_clientes.py")
        if os.path.exists(clientes_path):
            ultimo_id_antes = _obtener_ultimo_cliente_id(window)
            env = os.environ.copy()
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = project_root + os.pathsep + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = project_root
            proceso = subprocess.Popen(
                [sys.executable, clientes_path],
                env=env,
                cwd=project_root
            )
            # SIN QMessageBox.information - Solo iniciar polling
            _iniciar_polling_nuevo_cliente(window, proceso, ultimo_id_antes)
        else:
            QMessageBox.critical(
                window, 
                "Error",
                f"No se encontró el módulo de clientes en:\n{clientes_path}"
            )
    except Exception as e:
        QMessageBox.critical(
            window, 
            "Error",
            f"No se pudo abrir el módulo de clientes:\n{str(e)}"
        )

# ============================================================================
# FUNCIÓN PARA INSTALAR EL EVENT FILTER EN MODULO_PRESUPUESTOS.PY
# ============================================================================
def install_cliente_list_filter(window):
    """CORRECCIÓN 1.1: Instala el event filter para manejar Enter en lista de clientes."""
    event_filter = ListaClienteEventFilter(window)
    window.lst_clientes.installEventFilter(event_filter)
    return event_filter