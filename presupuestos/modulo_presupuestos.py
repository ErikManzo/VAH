# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/modulo_presupuestos.py
Versión FINAL con todas las correcciones:
Color global: maneja VARIOS y color específico correctamente
Desperdicio/F.V.: se propagan a TODAS las partidas del presupuesto
Ancho/Alto: se propagan a materiales fuera de paquete; los paquetes siguen
solo si no están personalizados (regla sigue/se respeta)
M.O./Accesorios/Piezas: solo afectan la partida actual
F5: GLOBAL - ciclo 1..X en BD mediante RecalculoGlobalController
Recálculo automático: diferido tras cálculos y post-menú (excepto Abrir/Imprimir)
Vista Previa: separada de Imprimir, usa QPdfView
Anidadas: valores independientes, se recalculan al modificar
Menú reorganizado:
Archivo:
  - Imprimir → submenú (Imprimir directo, Vista Previa, Enviar por Email)
Edición: eliminado
Mantenimiento:
  - Catálogo de Materiales → submenú con todos los tipos de materiales
  - Definir Paquetes → submenú (Aluminio/Herrajes)
  - Parámetros del Sistema abre diálogo completo
Ayuda: Manual Operativo y Manual Técnico abren PDFs correspondientes
Última actualización: 2026
"""
from __future__ import annotations
import sys
import os
import warnings
import importlib
from typing import Any, Dict, List, Optional, Tuple, Set

warnings.filterwarnings("ignore", category=RuntimeWarning)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtCore import Qt, QTimer, QDate, QObject, QEvent
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox,
    QTextEdit, QPushButton, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSplitter, QSizePolicy, QMenu
)

try:
    from presupuestos.core.utils import initialize_module

    initialize_module()
except ImportError:
    from core.utils import initialize_module

    initialize_module()

from presupuestos.core.constants import (
    C_TIPO, C_COLOR, C_CLAVE, C_DESC, C_CA, C_ANCHO, C_CH, C_ALTO, C_PZAS, C_PU, C_IMP,
    H_TIPO, H_CLAVE, H_DESC, H_CA, H_ANCHO, H_CH, H_ALTO, H_METROS, H_KG_M, H_KGS,
    H_PKG, H_PZAS, H_PU, H_IMP,
    P_TIPO, P_CLAVE, P_DESC, P_ANCHO, P_ALTO, P_PZAS,
    A_TIPO, A_COLOR, A_CLAVE, A_DESC, A_CA, A_ANCHO, A_CH, A_ALTO, A_PZAS, A_PU, A_IMP,
    EDITABILIDAD,
    ICON_PATH, WINDOW_TITLE, DEFAULT_COLOR_GLOBAL, SPLITTER_LEFT_RATIO,
    STYLESHEET,
    TIPOS_MATERIAL, TIPOS_BUSQUEDA, COLORES_GLOBAL, COLORES_PARTIDA,
)
from presupuestos.core.utils import (
    to_float as _f, to_int as _i, format_money as _money,
    connect_upper_lineedit as _connect_upper_lineedit,
    connect_upper_textedit as _connect_upper_textedit,
    connect_upper_combobox as _connect_upper_combobox,
    round_up_to_005 as _round_up_to_005,
    ajustar_medidas_industriales as _ajustar_medidas_industriales,
    safe_table_text, set_table_item_text, set_table_money,
    es_tipo_paquete,
    limpiar_texto, normalizar_clave,
)

try:
    from . import busquedas
    from .core.navigation.focus_manager import install_focus_manager
    from .foco import focus_col, focus_after_add, force_focus_on_pzas
    from .calculators.dimensioning import adjust_dimension
except Exception:
    import busquedas
    from core.navigation.focus_manager import install_focus_manager
    from foco import focus_col, focus_after_add, force_focus_on_pzas

    try:
        from calculators.dimensioning import adjust_dimension
    except ImportError:
        import math


        def adjust_dimension(value: float, step: float = 0.05) -> float:
            return math.ceil(value / step) * step if value > 0 else 0.0

try:
    from presupuestos.service import Service
    from presupuestos.calculators import EspecificacionesCtx, dispatch_calculo
    from presupuestos.rules_zero_price import guard_before_add
except Exception:
    try:
        from service import Service
        from calculators import EspecificacionesCtx, dispatch_calculo
        from rules_zero_price import guard_before_add
    except Exception:
        class Service:
            def buscar_por_tipo(self, **kwargs): return []

            def buscar_por_tabla(self, **kwargs): return []

            def clientes_buscar(self, args): return []

            def herreria_kg_por_m(self, clave): return 0.0

            def paquete_aluminio_items(self, clave_paquete): return []

            def paquete_herrajes_items(self, clave_paquete): return []

            def obtener_descripcion_material(self, tipo_base, clave_real): return f"Componente {clave_real}"


        from dataclasses import dataclass


        @dataclass
        class EspecificacionesCtx:
            svc: Any
            tipo: str
            clave: str
            color: str | None
            ancho: float
            alto: float
            piezas: int
            ca: float
            ch: float
            extra: Dict[str, Any]


        def dispatch_calculo(ctx):
            return 0.0, 0.0


        def guard_before_add(**__):
            class R:
                proceed = True
                faltantes = []

            return R()

from .ui.tables.paquetes import TablaPaquetes
from .ui.tables.anidada import TablaAnidada
from .controllers.paquetes_controller import PaquetesController
from .controllers.presupuesto_controller import PresupuestoController

try:
    from .controllers.recalculo_global_controller import RecalculoGlobalController
except Exception:
    from controllers.recalculo_global_controller import RecalculoGlobalController

# ==================================================================
# MAPEO DE MÓDULOS DE MATERIALES Y PAQUETES
# ==================================================================
MATERIALES_MODULES = {
    "aluminio": {
        "import": "materiales.aluminio.pantalla_materiales_aluminio",
        "class": "PantallaMaterialesAluminio"
    },
    "herreria": {
        "import": "materiales.herreria.pantalla_herreria",
        "class": "PantallaHerreria"
    },
    "vidrio": {
        "import": "materiales.vidrio.pantalla_vidrio",
        "class": "PantallaVidrio"
    },
    "herrajes": {
        "import": "materiales.herrajes.pantalla_herrajes",
        "class": "PantallaHerrajes"
    },
    "plasticos": {
        "import": "materiales.plasticos.pantalla_plasticos",
        "class": "PantallaPlasticos"
    },
    "otros": {
        "import": "materiales.otros.pantalla_otros",
        "class": "PantallaOtros"
    },
}

PAQUETES_MODULES = {
    "aluminio": {
        "import": "paquetes.aluminio.pantalla_paquete_aluminio",
        "class": "PaquetesAluminioUI"
    },
    "herrajes": {
        "import": "paquetes.herrajes.pantalla_paquete_herrajes",
        "class": "PaqueteHerrajesUI"
    },
}


class PresupuestosWindow(QMainWindow):
    C_TIPO = C_TIPO
    C_COLOR = C_COLOR
    C_CLAVE = C_CLAVE
    C_DESC = C_DESC
    C_CA = C_CA
    C_ANCHO = C_ANCHO
    C_CH = C_CH
    C_ALTO = C_ALTO
    C_PZAS = C_PZAS
    C_PU = C_PU
    C_IMP = C_IMP
    H_TIPO = H_TIPO
    H_CLAVE = H_CLAVE
    H_DESC = H_DESC
    H_CA = H_CA
    H_ANCHO = H_ANCHO
    H_CH = H_CH
    H_ALTO = H_ALTO
    H_METROS = H_METROS
    H_KG_M = H_KG_M
    H_KGS = H_KGS
    H_PKG = H_PKG
    H_PZAS = H_PZAS
    H_PU = H_PU
    H_IMP = H_IMP
    P_TIPO = P_TIPO
    P_CLAVE = P_CLAVE
    P_DESC = P_DESC
    P_ANCHO = P_ANCHO
    P_ALTO = P_ALTO
    P_PZAS = P_PZAS
    A_TIPO = A_TIPO
    A_COLOR = A_COLOR
    A_CLAVE = A_CLAVE
    A_DESC = A_DESC
    A_CA = A_CA
    A_ANCHO = A_ANCHO
    A_CH = A_CH
    A_ALTO = A_ALTO
    A_PZAS = A_PZAS
    A_PU = A_PU
    A_IMP = A_IMP

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.svc = Service()
        self._prog = False
        self._search_timer = QTimer(self, interval=160, singleShot=True)
        self._search_timer.timeout.connect(lambda: busquedas.do_search(self))
        self._paquete_actual = None
        self._paquete_seleccionado = None
        self._paquetes_desglosados = {}
        self._paquetes_anidados_pendientes = {}
        self._cantidades_base_componentes = {}
        self._instancias_paquetes = {}
        self._tabla_anidada_activa = False
        self._paquete_anidado_actual = None
        self._componentes_base_actuales = []
        self._build_ui()
        try:
            self._build_menu()
        except Exception:
            pass
        self.fm = install_focus_manager(self)
        self.keyfilter = self.fm
        self._ensure_focusable_widgets()
        self.paquetes_ctrl = PaquetesController(self, self.svc)
        self.presupuesto_ctrl = PresupuestoController(self, self.svc)
        self.recalculo_global_ctrl = RecalculoGlobalController(self, self.svc, self.presupuesto_ctrl)
        self._dim_prev_partida = (float(self.sp_ancho.value()), float(self.sp_alto.value()))
        self._conectar_disparadores_automaticos()
        try:
            self.presupuesto_ctrl.nuevo_presupuesto()
        except Exception as e:
            print(f"[DEBUG] Error inicializando número de presupuesto: {e}")

    def _ensure_focusable_widgets(self):
        focusable_widgets = [
            self.le_cliente, self.le_obra, self.sp_presupuesto, self.sp_partida,
            self.le_fecha, self.cbo_color_global, self.cbo_color, self.le_titulo,
            self.te_desc, self.sb_desperdicio, self.sb_fv_pct, self.sp_precio_kg,
            self.sp_ancho, self.sp_alto, self.sp_mo, self.sp_acc,
            self.sb_pzas_global, self.cbo_tipo, self.cbo_buscar, self.le_filtro,
            self.tbl, self.tbl_he, self.tbl_paquetes, self.tbl_anidada
        ]
        for widget in focusable_widgets:
            if widget:
                if hasattr(widget, 'setFocusPolicy'):
                    if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
                        if not getattr(widget, 'isReadOnly', lambda: False)():
                            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _conectar_disparadores_automaticos(self) -> None:
        ctrl = self.recalculo_global_ctrl
        self.sp_precio_kg.valueChanged.connect(ctrl.programar_auto)
        self.sb_desperdicio.valueChanged.connect(ctrl.programar_auto)
        self.sb_fv_pct.valueChanged.connect(ctrl.programar_auto)
        self.cbo_color_global.currentTextChanged.connect(lambda _t=None: ctrl.programar_auto())
        self.cbo_color.currentTextChanged.connect(lambda _t=None: ctrl.programar_auto())
        self.tbl.itemChanged.connect(lambda _it=None: ctrl.programar_auto())
        self.tbl_he.itemChanged.connect(lambda _it=None: ctrl.programar_auto())
        self.tbl_paquetes.paqueteAgregado.connect(lambda _d=None: ctrl.programar_auto())
        self.tbl_paquetes.piezasCambiadas.connect(lambda _f=None, _v=None: ctrl.programar_auto())
        self.tbl_paquetes.anchoCambiado.connect(lambda _f=None, _v=None: ctrl.programar_auto())
        self.tbl_paquetes.altoCambiado.connect(lambda _f=None, _v=None: ctrl.programar_auto())
        self.tbl_paquetes.paqueteEliminado.connect(lambda _f=None: ctrl.programar_auto())

    def _post_accion_recálculo_global(self) -> None:
        if getattr(self, '_prog', False):
            return
        if hasattr(self, 'presupuesto_ctrl') and self.presupuesto_ctrl:
            if self.presupuesto_ctrl._cargando:
                return
        if hasattr(self, 'recalculo_global_ctrl') and self.recalculo_global_ctrl:
            self.recalculo_global_ctrl.ejecutar(mostrar_mensaje=False)

    def _propagar_dimensiones_con_regla_paquetes(self, viejo=None) -> None:
        nuevo_ancho = float(self.sp_ancho.value())
        nuevo_alto = float(self.sp_alto.value())
        if viejo is None:
            viejo = (nuevo_ancho, nuevo_alto)
        viejo_ancho = float(viejo[0])
        viejo_alto = float(viejo[1])
        filas_paquete: Set[int] = set()
        if hasattr(self, 'paquetes_ctrl') and self.paquetes_ctrl:
            try:
                filas_paquete = self.paquetes_ctrl.filas_de_paquetes()
            except Exception:
                filas_paquete = set()
        for r in range(self.tbl.rowCount()):
            if r in filas_paquete:
                continue
            item_ancho = self.tbl.item(r, C_ANCHO)
            item_alto = self.tbl.item(r, C_ALTO)
            if item_ancho:
                item_ancho.setText(f"{nuevo_ancho:.2f}")
            if item_alto:
                item_alto.setText(f"{nuevo_alto:.2f}")
        for r in range(self.tbl_he.rowCount()):
            item_ancho = self.tbl_he.item(r, H_ANCHO)
            item_alto = self.tbl_he.item(r, H_ALTO)
            if item_ancho:
                item_ancho.setText(f"{nuevo_ancho:.2f}")
            if item_alto:
                item_alto.setText(f"{nuevo_alto:.2f}")
        if hasattr(self, 'paquetes_ctrl') and self.paquetes_ctrl:
            if hasattr(self.paquetes_ctrl, 'aplicar_dimensiones_paquete'):
                for fila in range(self.tbl_paquetes.rowCount()):
                    datos = self.tbl_paquetes.obtener_datos_paquete(fila)
                    if datos.get("es_anidado"):
                        continue
                    paq_ancho = float(datos.get("ancho", 0.0))
                    paq_alto = float(datos.get("alto", 0.0))
                    if abs(paq_ancho - viejo_ancho) < 0.001 and abs(paq_alto - viejo_alto) < 0.001:
                        self.paquetes_ctrl.aplicar_dimensiones_paquete(fila, nuevo_ancho, nuevo_alto)

    def showEvent(self, e):
        super().showEvent(e)
        if not self.isMaximized():
            self.showMaximized()
        try:
            self._set_fecha_hoy()
        except Exception:
            pass
        QTimer.singleShot(0, self._apply_split_20_80)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._apply_split_20_80()

    def _apply_split_20_80(self) -> None:
        try:
            if hasattr(self, "split") and self.split is not None:
                w = max(1, self.width())
                left = int(w * SPLITTER_LEFT_RATIO)
                right = max(1, w - left)
                sizes = self.split.sizes()
                if not sizes or abs(sizes[0] - left) > 3:
                    self.split.setSizes([left, right])
        except Exception:
            pass

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)
        rl = QHBoxLayout(root)
        rl.setContentsMargins(8, 8, 8, 8)
        rl.setSpacing(8)
        self.split = QSplitter(Qt.Orientation.Horizontal, self)
        self.split.setHandleWidth(6)
        rl.addWidget(self.split)
        left = QWidget(self)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(8)
        gb_d = QGroupBox("Datos del presupuesto", self)
        g = QGridLayout(gb_d)
        g.setContentsMargins(8, 8, 8, 8)
        g.setSpacing(6)
        r = 0
        g.addWidget(QLabel("CLIENTE:"), r, 0)
        self.le_cliente = QLineEdit(self)
        g.addWidget(self.le_cliente, r, 1)
        r += 1
        self.le_cliente.textEdited.connect(lambda s: busquedas.clientes_start_search(self, s))
        _connect_upper_lineedit(self.le_cliente)
        self.btn_nuevo_cliente = QPushButton("Nuevo cliente", self, clicked=lambda: busquedas.nuevo_cliente(self))
        self.btn_nuevo_cliente.setEnabled(False)
        g.addWidget(self.btn_nuevo_cliente, r, 1)
        r += 1
        self.lst_clientes = QListWidget(self)
        self.lst_clientes.setVisible(False)
        self.lst_clientes.itemClicked.connect(lambda it: busquedas.pick_cliente(self, it))
        self.lst_clientes.itemActivated.connect(lambda it: busquedas.pick_cliente(self, it))
        self.lst_clientes.installEventFilter(self)
        g.addWidget(self.lst_clientes, r, 0, 1, 2)
        r += 1
        g.addWidget(QLabel("OBRA:"), r, 0)
        self.le_obra = QLineEdit(self)
        g.addWidget(self.le_obra, r, 1)
        r += 1
        _connect_upper_lineedit(self.le_obra)
        g.addWidget(QLabel("PRESUPUESTO:"), r, 0)
        self.sp_presupuesto = QSpinBox(self, minimum=1, maximum=999999)
        self.sp_presupuesto.setValue(1)
        self.sp_presupuesto.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_presupuesto.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_presupuesto.setReadOnly(True)
        g.addWidget(self.sp_presupuesto, r, 1)
        r += 1
        g.addWidget(QLabel("PARTIDA:"), r, 0)
        self.sp_partida = QSpinBox(self, minimum=1, maximum=999999)
        self.sp_partida.setValue(1)
        self.sp_partida.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_partida.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_partida.setReadOnly(True)
        g.addWidget(self.sp_partida, r, 1)
        r += 1
        self.btn_navegar_partidas = QPushButton(" Ver Partidas", self)
        self.btn_navegar_partidas.clicked.connect(self._on_navegar_partidas)
        self.btn_navegar_partidas.setToolTip("Ver lista de partidas y navegar entre ellas")
        g.addWidget(self.btn_navegar_partidas, r, 1)
        r += 1
        g.addWidget(QLabel("FECHA:"), r, 0)
        self.le_fecha = QLineEdit(self)
        self.le_fecha.setInputMask("99/99/9999")
        self.le_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.le_fecha.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.le_fecha.textChanged.connect(self._on_fecha_text_changed)
        g.addWidget(self.le_fecha, r, 1)
        r += 1
        g.addWidget(QLabel("COLOR:"), r, 0)
        self.cbo_color_global = QComboBox(self)
        self.cbo_color_global.setEditable(True)
        self.cbo_color_global.addItems(COLORES_GLOBAL)
        self.cbo_color_global.setCurrentText(DEFAULT_COLOR_GLOBAL)
        self.cbo_color_global.currentTextChanged.connect(self._on_color_global_changed)
        g.addWidget(self.cbo_color_global, r, 1)
        r += 1
        _connect_upper_combobox(self.cbo_color_global)
        lv.addWidget(gb_d)
        gb_p = QGroupBox("Datos de la partida", self)
        pv = QVBoxLayout(gb_p)
        pv.setContentsMargins(8, 8, 8, 8)
        pv.setSpacing(6)
        self.le_titulo = QLineEdit(self)
        self.le_titulo.setPlaceholderText("TÍTULO DE PARTIDA")
        pv.addWidget(self.le_titulo)
        _connect_upper_lineedit(self.le_titulo)
        self.te_desc = QTextEdit(self)
        self.te_desc.setPlaceholderText("DESCRIPCIÓN DE LA PARTIDA")
        pv.addWidget(self.te_desc, 1)
        _connect_upper_textedit(self.te_desc)
        lv.addWidget(gb_p)
        gb_v = QGroupBox("Valores de la partida", self)
        gv = QGridLayout(gb_v)
        gv.setContentsMargins(8, 8, 8, 8)
        gv.setSpacing(6)
        rr = 0
        gv.addWidget(QLabel("DESPERDICIO:"), rr, 0)
        self.sb_desperdicio = QSpinBox(self, minimum=0, maximum=999)
        self.sb_desperdicio.setValue(2)
        self.sb_desperdicio.setSuffix("%")
        self.sb_desperdicio.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sb_desperdicio.focusInEvent = lambda event: self.sb_desperdicio.selectAll()
        gv.addWidget(self.sb_desperdicio, rr, 1)
        rr += 1
        self.sb_desperdicio.valueChanged.connect(self._on_campo_global_cambiado)
        gv.addWidget(QLabel("F.V. (%):"), rr, 0)
        self.sb_fv_pct = QSpinBox(self, minimum=0, maximum=999)
        self.sb_fv_pct.setValue(25)
        self.sb_fv_pct.setSuffix("%")
        self.sb_fv_pct.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sb_fv_pct.focusInEvent = lambda event: self.sb_fv_pct.selectAll()
        gv.addWidget(self.sb_fv_pct, rr, 1)
        rr += 1
        self.sb_fv_pct.valueChanged.connect(self._on_campo_global_cambiado)
        gv.addWidget(QLabel("COLOR (PARTIDA):"), rr, 0)
        self.cbo_color = QComboBox(self)
        self.cbo_color.setEditable(True)
        self.cbo_color.addItems(COLORES_PARTIDA)
        self.cbo_color.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if self.cbo_color.lineEdit():
            self.cbo_color.lineEdit().focusInEvent = lambda event: self.cbo_color.lineEdit().selectAll()
        gv.addWidget(self.cbo_color, rr, 1)
        rr += 1
        _connect_upper_combobox(self.cbo_color)
        self.cbo_color.currentTextChanged.connect(self._on_color_partida_changed)
        gv.addWidget(QLabel("$ / KG:"), rr, 0)
        self.sp_precio_kg = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=99999999.99)
        self.sp_precio_kg.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_precio_kg.focusInEvent = lambda event: self.sp_precio_kg.selectAll()
        gv.addWidget(self.sp_precio_kg, rr, 1)
        rr += 1
        self.sp_precio_kg.valueChanged.connect(self._on_campo_global_cambiado)
        gv.addWidget(QLabel("KG:"), rr, 0)
        self.sp_kg = QDoubleSpinBox(self, decimals=3, minimum=0.0, maximum=99999999.999)
        self.sp_kg.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_kg.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sp_kg.setEnabled(False)
        self.sp_kg.setReadOnly(True)
        gv.addWidget(self.sp_kg, rr, 1)
        rr += 1
        gv.addWidget(QLabel("ANCHO:"), rr, 0)
        self.sp_ancho = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999.99)
        self.sp_ancho.setValue(0.0)
        self.sp_ancho.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_ancho.focusInEvent = lambda event: self.sp_ancho.selectAll()
        gv.addWidget(self.sp_ancho, rr, 1)
        rr += 1
        self.sp_ancho.valueChanged.connect(self._on_campo_global_cambiado)
        gv.addWidget(QLabel("ALTO:"), rr, 0)
        self.sp_alto = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999.99)
        self.sp_alto.setValue(0.0)
        self.sp_alto.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_alto.focusInEvent = lambda event: self.sp_alto.selectAll()
        gv.addWidget(self.sp_alto, rr, 1)
        rr += 1
        self.sp_alto.valueChanged.connect(self._on_campo_global_cambiado)
        gv.addWidget(QLabel("MANO DE OBRA:"), rr, 0)
        self.sp_mo = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=99999999.99)
        self.sp_mo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_mo.focusInEvent = lambda event: self.sp_mo.selectAll()
        gv.addWidget(self.sp_mo, rr, 1)
        rr += 1
        self.sp_mo.valueChanged.connect(self._on_campo_global_cambiado)
        gv.addWidget(QLabel("ACCESORIOS:"), rr, 0)
        self.sp_acc = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=99999999.99)
        self.sp_acc.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_acc.focusInEvent = lambda event: self.sp_acc.selectAll()
        gv.addWidget(self.sp_acc, rr, 1)
        rr += 1
        self.sp_acc.valueChanged.connect(self._on_campo_global_cambiado)
        gv.addWidget(QLabel("P.U.:"), rr, 0)
        self.sp_pu_partida = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999999999.99)
        self.sp_pu_partida.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_pu_partida.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sp_pu_partida.setReadOnly(True)
        self.sp_pu_partida.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.sp_pu_partida.setEnabled(False)
        gv.addWidget(self.sp_pu_partida, rr, 1)
        rr += 1
        gv.addWidget(QLabel("PIEZAS:"), rr, 0)
        self.sb_pzas_global = QSpinBox(self, minimum=1, maximum=999999)
        self.sb_pzas_global.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sb_pzas_global.focusInEvent = lambda event: self.sb_pzas_global.selectAll()
        gv.addWidget(self.sb_pzas_global, rr, 1)
        rr += 1
        self.sb_pzas_global.valueChanged.connect(self._on_campo_global_cambiado)
        lv.addWidget(gb_v)
        gb_r = QGroupBox("Resumen de partida y presupuesto", self)

        def mk_disp():
            w = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999999999.99)
            w.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            w.setReadOnly(True)
            w.setAlignment(Qt.AlignmentFlag.AlignRight)
            w.setEnabled(False)
            return w

        gr = QGridLayout(gb_r)
        gr.setContentsMargins(8, 8, 8, 8)
        gr.setSpacing(6)
        rsum = 0
        gr.addWidget(QLabel("TOTAL DE LA PARTIDA:"), rsum, 0)
        self.sp_total_partida = mk_disp()
        gr.addWidget(self.sp_total_partida, rsum, 1)
        rsum += 1
        gr.addWidget(QLabel("SUB TOTAL:"), rsum, 0)
        self.sp_subtotal = mk_disp()
        gr.addWidget(self.sp_subtotal, rsum, 1)
        rsum += 1
        gr.addWidget(QLabel("I.V.A. (16%):"), rsum, 0)
        self.sp_iva = mk_disp()
        gr.addWidget(self.sp_iva, rsum, 1)
        rsum += 1
        gr.addWidget(QLabel("TOTAL:"), rsum, 0)
        self.sp_total = mk_disp()
        gr.addWidget(self.sp_total, rsum, 1)
        rsum += 1
        lv.addWidget(gb_r)
        self.split.addWidget(left)
        right = QWidget(self)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(8)
        bar = QWidget(self)
        b = QGridLayout(bar)
        b.setContentsMargins(0, 0, 0, 0)
        b.setSpacing(6)
        b.addWidget(QLabel("TIPO:"), 0, 0)
        self.cbo_tipo = QComboBox(self)
        self.cbo_tipo.addItems(TIPOS_MATERIAL)
        self.cbo_tipo.currentTextChanged.connect(lambda _=None: self._after_choose_filtro())
        b.addWidget(self.cbo_tipo, 0, 1)
        _connect_upper_combobox(self.cbo_tipo)
        b.addWidget(QLabel("BUSCAR POR:"), 0, 2)
        self.cbo_buscar = QComboBox(self)
        self.cbo_buscar.addItems(TIPOS_BUSQUEDA)
        b.addWidget(self.cbo_buscar, 0, 3)
        self.cbo_buscar.activated.connect(lambda _=None: self.le_filtro.setFocus())
        _connect_upper_combobox(self.cbo_buscar)
        b.addWidget(QLabel("FILTRO:"), 0, 4)
        self.le_filtro = QLineEdit(self)
        self.le_filtro.textChanged.connect(
            lambda _t: (
                self._search_timer.start(),
                self.lst_result.setVisible(bool((self.le_filtro.text() or '').strip()))
            )
        )
        b.addWidget(self.le_filtro, 0, 5)
        _connect_upper_lineedit(self.le_filtro)
        self.lst_result = QListWidget(self)
        self.lst_result.setVisible(False)
        self.lst_result.setMinimumHeight(220)
        self.lst_result.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.lst_result.itemClicked.connect(
            lambda it: self._on_pick_result_paquete(it) if self._es_tipo_paquete() else busquedas.on_pick_result(self,
                                                                                                                 it)
        )
        self.lst_result.itemActivated.connect(
            lambda it: self._on_pick_result_paquete(it) if self._es_tipo_paquete() else busquedas.on_pick_result(self,
                                                                                                                 it)
        )
        b.addWidget(self.lst_result, 1, 0, 1, 6)
        b.setRowStretch(0, 0)
        b.setRowStretch(1, 1)
        rv.addWidget(bar)
        tablas_container = QWidget(self)
        tablas_layout = QVBoxLayout(tablas_container)
        tablas_layout.setContentsMargins(0, 0, 0, 0)
        tablas_layout.setSpacing(4)
        self.gb_tabla_paquetes = QGroupBox("📦 Paquetes", self)
        vm_paquetes = QVBoxLayout(self.gb_tabla_paquetes)
        self.tbl_paquetes = TablaPaquetes(self)
        vm_paquetes.addWidget(self.tbl_paquetes, 1)
        tablas_layout.addWidget(self.gb_tabla_paquetes, 1)
        self.gb_tabla_anidada = QGroupBox(" Anidada (Componentes del paquete actual)", self)
        self.gb_tabla_anidada.setVisible(False)
        vm_anidada = QVBoxLayout(self.gb_tabla_anidada)
        self.tbl_anidada = TablaAnidada(self)
        vm_anidada.addWidget(self.tbl_anidada, 1)
        tablas_layout.addWidget(self.gb_tabla_anidada, 1)
        self.gb_tabla_materiales = QGroupBox(" Materiales", self)
        vm_materiales = QVBoxLayout(self.gb_tabla_materiales)
        self.tbl = QTableWidget(0, 11, self)
        self.tbl.setHorizontalHeaderLabels([
            "Tipo", "Color", "Clave", "Descripción", "Cant. Ancho",
            "Ancho", "Cant. Alto", "Alto", "Piezas", "P.U.", "Importe"
        ])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.itemChanged.connect(lambda it: (
                getattr(self, "_on_tbl_std_changed", None) and self._on_tbl_std_changed(it)
        ))
        vm_materiales.addWidget(self.tbl)
        tablas_layout.addWidget(self.gb_tabla_materiales, 1)
        self.gb_tabla_herreria = QGroupBox("🔧 Herrería", self)
        vm_herreria = QVBoxLayout(self.gb_tabla_herreria)
        self.tbl_he = QTableWidget(0, 14, self)
        self.tbl_he.setHorizontalHeaderLabels([
            "Tipo", "Clave", "Descripción", "Cant. Ancho",
            "Ancho", "Cant. Alto", "Alto", "Metros", "Kg/m", "Kgs.", "$/kg",
            "Piezas", "P.U.", "Importe"
        ])
        self.tbl_he.verticalHeader().setVisible(False)
        self.tbl_he.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_he.itemChanged.connect(lambda it: (
                getattr(self, "_on_tbl_he_changed", None) and self._on_tbl_he_changed(it)
        ))
        vm_herreria.addWidget(self.tbl_he)
        tablas_layout.addWidget(self.gb_tabla_herreria, 1)
        rv.addWidget(tablas_container, 1)
        self.split.addWidget(right)
        self.setStyleSheet(STYLESHEET)
        QTimer.singleShot(0, lambda: (
            self._sync_color_rule(from_user=False),
            self.le_cliente.setFocus()
        ))

    def _build_menu(self) -> None:
        mb = self.menuBar()
        m_archivo = mb.addMenu("&Archivo")
        act_nuevo = QAction("&Nuevo Presupuesto", self, shortcut=QKeySequence("Ctrl+N"),
                            triggered=self._on_nuevo_presupuesto)
        m_archivo.addAction(act_nuevo)
        act_abrir = QAction("&Abrir Presupuesto", self, shortcut=QKeySequence("Ctrl+O"),
                            triggered=self._on_abrir_presupuesto)
        m_archivo.addAction(act_abrir)
        m_archivo.addSeparator()
        act_guardar = QAction("&Guardar Presupuesto", self, shortcut=QKeySequence("Ctrl+S"),
                              triggered=self._on_guardar_presupuesto)
        m_archivo.addAction(act_guardar)
        act_guardar_como = QAction("&Guardar Como...", self, shortcut=QKeySequence("Ctrl+Shift+S"),
                                   triggered=self._on_guardar_como_presupuesto)
        m_archivo.addAction(act_guardar_como)
        m_archivo.addSeparator()

        # NUEVO: Submenú Imprimir con 3 opciones
        m_imprimir = m_archivo.addMenu("&Imprimir")
        act_imprimir_directo = QAction("&Imprimir directo", self, shortcut=QKeySequence("Ctrl+P"),
                                       triggered=self._on_imprimir)
        m_imprimir.addAction(act_imprimir_directo)
        act_vista_previa = QAction("Vista &Previa", self, triggered=self._on_vista_previa)
        m_imprimir.addAction(act_vista_previa)
        act_enviar_email = QAction("Enviar por &Email", self, triggered=self._on_enviar_email)
        m_imprimir.addAction(act_enviar_email)

        m_archivo.addSeparator()
        act_salir = QAction("&Salir", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close)
        m_archivo.addAction(act_salir)

        m_presupuesto = mb.addMenu("&Presupuesto")
        act_nueva_partida = QAction("Nueva &Partida", self, shortcut=QKeySequence("Ctrl+T"),
                                    triggered=self._on_nueva_partida)
        m_presupuesto.addAction(act_nueva_partida)
        act_duplicar_partida = QAction("&Duplicar Partida", self, triggered=self._on_duplicar_partida)
        m_presupuesto.addAction(act_duplicar_partida)
        act_eliminar_partida = QAction("&Eliminar Partida", self, shortcut=QKeySequence("Del"),
                                       triggered=self._on_eliminar_partida)
        m_presupuesto.addAction(act_eliminar_partida)
        m_presupuesto.addSeparator()
        act_recalcular_todo = QAction("&Recalcular Todo (F5)", self, shortcut=QKeySequence("F5"),
                                      triggered=self._on_recalcular_todo)
        m_presupuesto.addAction(act_recalcular_todo)

        m_mantenimiento = mb.addMenu("&Mantenimiento")
        m_catalogo = m_mantenimiento.addMenu("&Catálogo de Materiales")
        self._add_materiales_actions(m_catalogo)
        m_mantenimiento.addSeparator()
        m_paquetes = m_mantenimiento.addMenu("Definir &Paquetes")
        self._add_paquetes_actions(m_paquetes)
        m_mantenimiento.addSeparator()
        act_parametros_sistema = QAction("&Parámetros del Sistema", self, triggered=self._on_parametros_sistema)
        m_mantenimiento.addAction(act_parametros_sistema)

        m_ayuda = mb.addMenu("&Ayuda")
        act_manual_operativo = QAction("&Manual Operativo", self, triggered=self._on_manual_operativo)
        m_ayuda.addAction(act_manual_operativo)
        act_manual_tecnico = QAction("Manual &Técnico", self, triggered=self._on_manual_tecnico)
        m_ayuda.addAction(act_manual_tecnico)
        m_ayuda.addSeparator()
        act_acerca_de = QAction("&Acerca de VAH", self, triggered=self._on_acerca_de)
        m_ayuda.addAction(act_acerca_de)

    def _add_materiales_actions(self, menu: QMenu) -> None:
        self._add_material_action(menu, "Aluminio", "aluminio")
        self._add_material_action(menu, "Herrería", "herreria")
        self._add_material_action(menu, "Vidrio", "vidrio")
        self._add_material_action(menu, "Herrajes", "herrajes")
        self._add_material_action(menu, "Plásticos", "plasticos")
        self._add_material_action(menu, "Otros", "otros")

    def _add_paquetes_actions(self, menu: QMenu) -> None:
        self._add_paquete_action(menu, "Aluminio", "aluminio")
        self._add_paquete_action(menu, "Herrajes", "herrajes")

    def _add_material_action(self, menu: QMenu, texto: str, modulo_key: str) -> None:
        act = QAction(texto, self)
        act.triggered.connect(lambda: self._launch_material_module(modulo_key))
        menu.addAction(act)

    def _add_paquete_action(self, menu: QMenu, texto: str, modulo_key: str) -> None:
        act = QAction(texto, self)
        act.triggered.connect(lambda: self._launch_paquete_module(modulo_key))
        menu.addAction(act)

    def _launch_material_module(self, modulo_key: str) -> None:
        config = MATERIALES_MODULES.get(modulo_key)
        if not config:
            QMessageBox.critical(self, "Error", f"No se encontró configuración para el módulo: {modulo_key}")
            return
        try:
            mod = importlib.import_module(config["import"])
            cls = getattr(mod, config["class"])
            ventana = cls()
            ventana.show()
        except ImportError as e:
            QMessageBox.critical(self, "Error de importación",
                                 f"No se pudo importar el módulo '{config['import']}'.\n\n{str(e)}")
        except AttributeError as e:
            QMessageBox.critical(self, "Error de clase",
                                 f"No se encontró la clase '{config['class']}' en el módulo.\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error inesperado", f"No se pudo abrir el catálogo de {modulo_key}:\n\n{str(e)}")

    def _launch_paquete_module(self, modulo_key: str) -> None:
        config = PAQUETES_MODULES.get(modulo_key)
        if not config:
            QMessageBox.critical(self, "Error", f"No se encontró configuración para el módulo: {modulo_key}")
            return
        try:
            mod = importlib.import_module(config["import"])
            cls = getattr(mod, config["class"])
            ventana = cls()
            ventana.show()
        except ImportError as e:
            QMessageBox.critical(self, "Error de importación",
                                 f"No se pudo importar el módulo '{config['import']}'.\n\n{str(e)}")
        except AttributeError as e:
            QMessageBox.critical(self, "Error de clase",
                                 f"No se encontró la clase '{config['class']}' en el módulo.\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error inesperado",
                                 f"No se pudo abrir la definición de paquetes de {modulo_key}:\n\n{str(e)}")

    def _safe_text(self, table: QTableWidget, r: int, c: int, default: str = "0") -> str:
        return safe_table_text(table, r, c, default)

    def _set_or_update_item(self, tbl: QTableWidget, r: int, c: int, text: str, editable: bool = True) -> None:
        set_table_item_text(tbl, r, c, text, editable)

    def _set_money(self, tbl: QTableWidget, r: int, c: int, value: float) -> None:
        set_table_money(tbl, r, c, value)

    def _get_tipo(self, row: int) -> str:
        return self._safe_text(self.tbl, row, C_TIPO, "")

    def _get_color_partida_o_global(self) -> str:
        g = (self.cbo_color_global.currentText() or "").strip().upper()
        if g and g != "VARIOS":
            return g
        return (self.cbo_color.currentText() or "").strip().upper()

    def _es_tipo_paquete(self) -> bool:
        tipo_seleccionado = (self.cbo_tipo.currentText() or "").strip().upper()
        return es_tipo_paquete(tipo_seleccionado)

    def _sync_color_rule(self, from_user: bool = False) -> None:
        g = (self.cbo_color_global.currentText() or "").strip().upper()
        if g == "VARIOS":
            self.cbo_color.setEnabled(True)
            if from_user:
                self.cbo_color.setFocus()
        else:
            self.cbo_color.setCurrentText(g)
            self.cbo_color.setEnabled(False)
        try:
            if hasattr(self, "fm") and self.fm:
                self.fm.refresh_navigation_cache()
        except Exception:
            pass

    def _on_color_global_changed(self, nuevo_color: str) -> None:
        self._sync_color_rule(from_user=True)
        try:
            if hasattr(self, 'presupuesto_ctrl') and self.presupuesto_ctrl:
                if not self.presupuesto_ctrl.presupuesto_id:
                    self.presupuesto_ctrl.guardar_partida_actual_silencioso()
                if self.presupuesto_ctrl.presupuesto_id:
                    self.presupuesto_ctrl.recalcular_por_color()
                else:
                    self._actualizar_color_en_tabla_materiales()
                    for r in range(self.tbl.rowCount()):
                        self._calc_std_row(r)
                    for r in range(self.tbl_he.rowCount()):
                        self._calc_he_row(r)
                    self._recalc_summary()
        except Exception as e:
            print(f"[DEBUG] Error recalculando por color: {e}")

    def _on_color_partida_changed(self, nuevo_color: str) -> None:
        if getattr(self, '_prog', False):
            return
        g = (self.cbo_color_global.currentText() or "").strip().upper()
        if g != "VARIOS":
            return
        try:
            self._prog = True
            self._actualizar_color_en_tabla_materiales()
            self._actualizar_color_en_tabla_anidada()
            for r in range(self.tbl.rowCount()):
                self._calc_std_row(r)
            for r in range(self.tbl_he.rowCount()):
                self._calc_he_row(r)
            if hasattr(self, 'tbl_anidada') and self._tabla_anidada_activa:
                for r in range(self.tbl_anidada.rowCount()):
                    self._calc_anidada_row(r)
            self._recalc_summary()
        except Exception as e:
            print(f"[DEBUG] Error recalculando partida por cambio de color: {e}")
        finally:
            self._prog = False

    def _actualizar_color_en_tabla_materiales(self) -> None:
        nuevo_color = self._get_color_partida_o_global()
        for r in range(self.tbl.rowCount()):
            item = self.tbl.item(r, C_COLOR)
            if item is not None:
                item.setText(nuevo_color)

    def _actualizar_color_en_tabla_anidada(self) -> None:
        nuevo_color = self._get_color_partida_o_global()
        for r in range(self.tbl_anidada.rowCount()):
            item = self.tbl_anidada.item(r, A_COLOR)
            if item is not None:
                item.setText(nuevo_color)

    def _set_fecha_hoy(self) -> None:
        if hasattr(self, "le_fecha") and self.le_fecha:
            from datetime import datetime
            self.le_fecha.setText(datetime.now().strftime("%d/%m/%Y"))

    def _after_choose_filtro(self):
        return busquedas.after_choose_filtro(self)

    def _on_fecha_text_changed(self, text):
        if not hasattr(self, 'le_fecha') or not self.le_fecha:
            return
        cursor_pos = self.le_fecha.cursorPosition()
        pass

    def _on_pick_result_paquete(self, item: QListWidgetItem) -> None:
        if item is None:
            return
        datos = item.data(Qt.ItemDataRole.UserRole)
        if not datos:
            return
        tipo = (self.cbo_tipo.currentText() or "").strip().upper()
        clave = datos.get("clave", "").strip()
        desc = datos.get("descripcion", "").strip()
        ancho = float(self.sp_ancho.value())
        alto = float(self.sp_alto.value())
        self.tbl_paquetes.agregar_paquete(tipo, clave, desc, ancho, alto)
        self.le_filtro.setText(f"{clave} — {desc}")
        self.lst_result.setVisible(False)
        fila_nueva = self.tbl_paquetes.rowCount() - 1
        if "HERRAJES" in tipo:
            QTimer.singleShot(100, lambda: self._enfocar_celda_piezas_paquetes(fila_nueva))
        else:
            QTimer.singleShot(100, lambda: self._enfocar_celda_ancho_paquetes(fila_nueva))

    def _enfocar_celda_ancho_paquetes(self, fila: int) -> None:
        if fila < self.tbl_paquetes.rowCount():
            self.tbl_paquetes.setCurrentCell(fila, P_ANCHO)
            self.tbl_paquetes.editItem(self.tbl_paquetes.item(fila, P_ANCHO))

    def _enfocar_celda_piezas_paquetes(self, fila: int) -> None:
        if fila < self.tbl_paquetes.rowCount():
            self.tbl_paquetes.setCurrentCell(fila, P_PZAS)
            self.tbl_paquetes.editItem(self.tbl_paquetes.item(fila, P_PZAS))

    def _calc_anidada_row(self, r: int) -> None:
        try:
            tipo = self._safe_text(self.tbl_anidada, r, A_TIPO, "").strip().upper()
            clave = self._safe_text(self.tbl_anidada, r, A_CLAVE, "")
            color = self._get_color_partida_o_global()
            ancho_original = _f(self._safe_text(self.tbl_anidada, r, A_ANCHO, "0"))
            alto_original = _f(self._safe_text(self.tbl_anidada, r, A_ALTO, "0"))
            ca = _f(self._safe_text(self.tbl_anidada, r, A_CA, "1"), 1)
            ch = _f(self._safe_text(self.tbl_anidada, r, A_CH, "1"), 1)
            pzas = _i(self._safe_text(self.tbl_anidada, r, A_PZAS, "1"), 1)
            precio_kg = float(self.sp_precio_kg.value())
            ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_original, alto_original)
            ctx = EspecificacionesCtx(
                svc=self.svc, tipo=tipo, clave=clave, color=color,
                ancho=ancho_ajustado, alto=alto_ajustado, piezas=pzas, ca=ca, ch=ch,
                extra={"precio_kg": precio_kg}
            )
            pu, imp = dispatch_calculo(ctx)
            self._set_money(self.tbl_anidada, r, A_PU, pu)
            self._set_money(self.tbl_anidada, r, A_IMP, imp)
        except Exception as e:
            print(f"Error calculando fila anidada: {e}")

    def _add_std(self, rec: Dict[str, Any], tipo: str, color: str, ancho: float, alto: float,
                 _pzas_ignored: int) -> None:
        if self._es_tipo_paquete():
            return
        r = self.tbl.rowCount()
        self.tbl.insertRow(r)
        try:
            self._prog = True
            clave = rec.get("clave", "")
            descripcion = rec.get("descripcion", "")
            self._set_or_update_item(self.tbl, r, C_TIPO, tipo, editable=False)
            self._set_or_update_item(self.tbl, r, C_COLOR, self._get_color_partida_o_global(), editable=False)
            self._set_or_update_item(self.tbl, r, C_CLAVE, clave, editable=False)
            self._set_or_update_item(self.tbl, r, C_DESC, descripcion, editable=False)
            self._set_or_update_item(self.tbl, r, C_CA, "1", editable=True)
            self._set_or_update_item(self.tbl, r, C_ANCHO, f"{ancho:.2f}", editable=True)
            self._set_or_update_item(self.tbl, r, C_CH, "1", editable=True)
            self._set_or_update_item(self.tbl, r, C_ALTO, f"{alto:.2f}", editable=True)
            self._set_or_update_item(self.tbl, r, C_PZAS, "1", editable=True)
            self._set_or_update_item(self.tbl, r, C_PU, "0.00", editable=False)
            self._set_or_update_item(self.tbl, r, C_IMP, "0.00", editable=False)
            self._apply_editabilidad_std(r)
            self._calc_std_row(r)
        finally:
            self._prog = False
            self._recalc_summary()
            if self.tbl.item(r, 0) is not None:
                QTimer.singleShot(100, lambda: self._scroll_a_ultima_fila_materiales(r))

    def _scroll_a_ultima_fila_materiales(self, fila: int) -> None:
        try:
            if fila < self.tbl.rowCount() and self.tbl.item(fila, 0) is not None:
                self.tbl.scrollToItem(self.tbl.item(fila, 0), self.tbl.ScrollHint.PositionAtBottom)
        except Exception:
            pass

    def _add_he(self, rec: Dict[str, Any], tipo: str, color: str, ancho: float, alto: float,
                _pzas_ignored: int) -> None:
        if not hasattr(self, "tbl_he"):
            return
        r = self.tbl_he.rowCount()
        self.tbl_he.insertRow(r)
        try:
            self._prog = True
            tipo_txt = (tipo or "").strip().upper()
            clave = str(rec.get("clave", "") or "")
            desc = str(rec.get("descripcion", "") or "")
            ancho_val = float(ancho or 0.0)
            alto_val = float(alto or 0.0)
            ca_val = 1.0
            ch_val = 1.0
            pzas_val = 1
            try:
                kg_m_val = self.svc.herreria_kg_por_m(clave) or 0.0
                kg_m_val = float(kg_m_val)
            except Exception:
                kg_m_val = 0.0
            precio_kg_val = float(self.sp_precio_kg.value())
            ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_val, alto_val)
            metros_val = (ca_val * ancho_ajustado) + (ch_val * alto_ajustado)
            kgs_val = metros_val * kg_m_val
            ctx = EspecificacionesCtx(
                svc=self.svc, tipo="HERRERIA", clave=clave, color=self._get_color_partida_o_global(),
                ancho=ancho_ajustado, alto=alto_ajustado, piezas=pzas_val, ca=ca_val, ch=ch_val,
                extra={"precio_kg": precio_kg_val},
            )
            pu_val, imp_val = dispatch_calculo(ctx)
            self._set_or_update_item(self.tbl_he, r, H_TIPO, tipo_txt, editable=False)
            self._set_or_update_item(self.tbl_he, r, H_CLAVE, clave, editable=False)
            self._set_or_update_item(self.tbl_he, r, H_DESC, desc, editable=False)
            self._set_or_update_item(self.tbl_he, r, H_CA, f"{ca_val:.0f}", editable=True)
            self._set_or_update_item(self.tbl_he, r, H_ANCHO, f"{ancho_val:.2f}", editable=True)
            self._set_or_update_item(self.tbl_he, r, H_CH, f"{ch_val:.0f}", editable=True)
            self._set_or_update_item(self.tbl_he, r, H_ALTO, f"{alto_val:.2f}", editable=True)
            self._set_or_update_item(self.tbl_he, r, H_METROS, f"{metros_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KG_M, f"{kg_m_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KGS, f"{kgs_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_PKG, f"{precio_kg_val:.2f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_PZAS, f"{pzas_val:d}", editable=True)
            self._set_money(self.tbl_he, r, H_PU, pu_val)
            self._set_money(self.tbl_he, r, H_IMP, imp_val)
            self._recalc_summary()
        finally:
            self._prog = False
            if self.tbl_he.item(r, 0) is not None:
                QTimer.singleShot(100, lambda: self._scroll_a_ultima_fila_herreria(r))

    def _scroll_a_ultima_fila_herreria(self, fila: int) -> None:
        try:
            if fila < self.tbl_he.rowCount() and self.tbl_he.item(fila, 0) is not None:
                self.tbl_he.scrollToItem(self.tbl_he.item(fila, 0), self.tbl_he.ScrollHint.PositionAtBottom)
        except Exception:
            pass

    def _apply_editabilidad_std(self, row: int) -> None:
        tipo = (self._get_tipo(row) or "").strip().upper()
        rules = EDITABILIDAD.get(tipo, EDITABILIDAD.get(busquedas.normalize_token(tipo), EDITABILIDAD["OTROS"]))

        def set_editable(c: int, editable: bool):
            it = self.tbl.item(row, c)
            if it is None:
                it = QTableWidgetItem("")
                self.tbl.setItem(row, c, it)
            flags = it.flags()
            it.setFlags((flags | Qt.ItemFlag.ItemIsEditable) if editable else (flags & ~Qt.ItemFlag.ItemIsEditable))

        set_editable(C_CA, bool(rules["CA"]))
        set_editable(C_CH, bool(rules["CH"]))
        set_editable(C_ANCHO, bool(rules["ANCHO"]))
        set_editable(C_ALTO, bool(rules["ALTO"]))
        set_editable(C_PZAS, bool(rules["PZAS"]))

    def _on_tbl_std_changed(self, item: QTableWidgetItem) -> None:
        if item is None or getattr(self, "_prog", False):
            return
        row = item.row()
        col = item.column()
        if col not in (C_CA, C_ANCHO, C_CH, C_ALTO, C_PZAS, C_PU):
            return
        try:
            self._prog = True
            self._calc_std_row(row)
        except Exception as e:
            QMessageBox.warning(self, "Cálculo", f"Hubo un problema al calcular la fila:\n{e}")
        finally:
            self._prog = False

    def _on_tbl_he_changed(self, item: QTableWidgetItem) -> None:
        if item is None or getattr(self, "_prog", False):
            return
        row = item.row()
        col = item.column()
        if col not in (H_CA, H_ANCHO, H_CH, H_ALTO, H_PZAS):
            return
        try:
            self._prog = True
            self._calc_he_row(row)
        except Exception as e:
            QMessageBox.warning(self, "Cálculo Herrería", f"Hubo un problema al calcular la fila:\n{e}")
        finally:
            self._prog = False

    def _calc_he_row(self, r: int) -> None:
        try:
            self._prog = True
            ca_val = _f(self._safe_text(self.tbl_he, r, H_CA, "1"), 1.0)
            ancho_val = _f(self._safe_text(self.tbl_he, r, H_ANCHO, "0"), 0.0)
            ch_val = _f(self._safe_text(self.tbl_he, r, H_CH, "1"), 1.0)
            alto_val = _f(self._safe_text(self.tbl_he, r, H_ALTO, "0"), 0.0)
            pzas_val = _i(self._safe_text(self.tbl_he, r, H_PZAS, "1"), 1)
            clave = self._safe_text(self.tbl_he, r, H_CLAVE, "")
            try:
                kg_m_val = self.svc.herreria_kg_por_m(clave) or 0.0
                kg_m_val = float(kg_m_val)
            except Exception:
                kg_m_val = 0.0
            precio_kg_val = float(self.sp_precio_kg.value())
            ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_val, alto_val)
            metros_val = (ca_val * ancho_ajustado) + (ch_val * alto_ajustado)
            kgs_val = metros_val * kg_m_val
            self._set_or_update_item(self.tbl_he, r, H_METROS, f"{metros_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KG_M, f"{kg_m_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KGS, f"{kgs_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_PKG, f"{precio_kg_val:.2f}", editable=False)
            ctx = EspecificacionesCtx(
                svc=self.svc, tipo="HERRERIA", clave=clave, color=self._get_color_partida_o_global(),
                ancho=ancho_ajustado, alto=alto_ajustado, piezas=pzas_val, ca=ca_val, ch=ch_val,
                extra={"precio_kg": precio_kg_val},
            )
            pu_val, imp_val = dispatch_calculo(ctx)
            self._set_money(self.tbl_he, r, H_PU, pu_val)
            self._set_money(self.tbl_he, r, H_IMP, imp_val)
            self._recalc_summary()
        except Exception as e:
            QMessageBox.warning(self, "Error en cálculo", f"Error al calcular fila {r}:\n{str(e)}")
        finally:
            self._prog = False

    def _calc_std_row(self, r: int) -> None:
        tipo = (self._get_tipo(r) or "").strip().upper()
        clave = self._safe_text(self.tbl, r, C_CLAVE, "")
        color = self._get_color_partida_o_global()
        ancho_original = _f(self._safe_text(self.tbl, r, C_ANCHO, "0"))
        alto_original = _f(self._safe_text(self.tbl, r, C_ALTO, "0"))
        ca = _f(self._safe_text(self.tbl, r, C_CA, "1"), 1)
        ch = _f(self._safe_text(self.tbl, r, C_CH, "1"), 1)
        pzas = _i(self._safe_text(self.tbl, r, C_PZAS, "1"), 1)
        precio_kg = float(self.sp_precio_kg.value())
        try:
            g = guard_before_add(svc=self.svc, tipo=tipo, clave=clave, color=color, precio_kg=precio_kg)
        except Exception as e:
            g = type("G", (), {"proceed": True, "faltantes": []})()
            QMessageBox.warning(self, "Reglas previas", f"No fue posible validar reglas previas:\n{e}")
        if not getattr(g, "proceed", True):
            self._set_money(self.tbl, r, C_PU, 0.0)
            self._set_money(self.tbl, r, C_IMP, 0.0)
            self._recalc_summary()
            return
        ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_original, alto_original)
        ctx = EspecificacionesCtx(
            svc=self.svc, tipo=tipo, clave=clave, color=color,
            ancho=ancho_ajustado, alto=alto_ajustado, piezas=pzas, ca=ca, ch=ch,
            extra={"precio_kg": precio_kg}
        )
        try:
            pu, imp = dispatch_calculo(ctx)
        except Exception as e:
            pu, imp = 0.0, 0.0
            QMessageBox.warning(self, "Cálculo", f"No fue posible calcular el P.U./Importe:\n{e}")
        self._set_money(self.tbl, r, C_PU, pu)
        self._set_money(self.tbl, r, C_IMP, imp)
        self._recalc_summary()

    def _recalc_summary(self) -> None:
        A = 0.0
        for r in range(self.tbl.rowCount()):
            A += _f(self._safe_text(self.tbl, r, C_IMP, "0"), 0.0)
        try:
            if hasattr(self, "tbl_he"):
                for r in range(self.tbl_he.rowCount()):
                    A += _f(self._safe_text(self.tbl_he, r, H_IMP, "0"), 0.0)
        except Exception:
            pass
        try:
            if hasattr(self, "tbl_he") and hasattr(self, "sp_kg"):
                total_kgs = 0.0
                for r in range(self.tbl_he.rowCount()):
                    total_kgs += _f(self._safe_text(self.tbl_he, r, H_KGS, "0"), 0.0)
                self.sp_kg.setValue(total_kgs)
        except Exception:
            pass
        B = float(self.sp_mo.value()) + float(self.sp_acc.value())
        C = A + B
        D = C + (C * (float(self.sb_desperdicio.value()) / 100.0))
        E = D + (D * (float(self.sb_fv_pct.value()) / 100.0))
        piezas = max(1, int(self.sb_pzas_global.value()))
        total_partida = E * piezas
        self.sp_pu_partida.setValue(E)
        self.sp_total_partida.setValue(total_partida)
        sub = total_partida
        iva = sub * 0.16
        tot = sub + iva
        self.sp_subtotal.setValue(sub)
        self.sp_iva.setValue(iva)
        self.sp_total.setValue(tot)

    def _on_campo_global_cambiado(self):
        nuevo = (float(self.sp_ancho.value()), float(self.sp_alto.value()))
        viejo = getattr(self, "_dim_prev_partida", nuevo)
        self._dim_prev_partida = nuevo
        if getattr(self, '_prog', False):
            return
        try:
            self._prog = True
            sender = self.sender()
            if sender in (self.sp_ancho, self.sp_alto):
                self._propagar_dimensiones_con_regla_paquetes(viejo)
            elif sender in (self.sb_desperdicio, self.sb_fv_pct):
                if hasattr(self, 'presupuesto_ctrl') and self.presupuesto_ctrl:
                    self.presupuesto_ctrl.propagar_desperdicio_fv(self.sb_desperdicio.value(), self.sb_fv_pct.value())
            for r in range(self.tbl.rowCount()):
                self._calc_std_row(r)
            for r in range(self.tbl_he.rowCount()):
                self._calc_he_row(r)
            self._recalc_summary()
        except Exception as e:
            print(f"Error en recálculo automático: {e}")
        finally:
            self._prog = False

    def _on_nuevo_presupuesto(self):
        if hasattr(self, 'recalculo_global_ctrl') and self.recalculo_global_ctrl:
            self.recalculo_global_ctrl.cancelar_auto()
        if self.presupuesto_ctrl._hay_datos_en_partida():
            resp = QMessageBox.question(self, "Nuevo Presupuesto",
                                        "Hay datos sin guardar. ¿Desea guardarlos antes de crear un nuevo presupuesto?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if resp == QMessageBox.StandardButton.Cancel:
                return
            if resp == QMessageBox.StandardButton.Yes:
                self.presupuesto_ctrl.guardar_partida_actual_silencioso()
        self.presupuesto_ctrl.nuevo_presupuesto()
        self.presupuesto_ctrl.limpiar_todo()
        self._post_accion_recálculo_global()

    def _on_abrir_presupuesto(self):
        if hasattr(self, 'recalculo_global_ctrl') and self.recalculo_global_ctrl:
            self.recalculo_global_ctrl.cancelar_auto()
        hay_cliente = bool(self.le_cliente.text().strip())
        if hay_cliente:
            self.presupuesto_ctrl.guardar_partida_actual_silencioso()
        from presupuestos.ui.dialogs.abrir_presupuesto_dialog import AbrirPresupuestoDialog
        dlg = AbrirPresupuestoDialog(self, self.svc)
        if dlg.exec():
            presupuesto_id = dlg.get_selected_id()
            if presupuesto_id:
                self.presupuesto_ctrl.cargar_presupuesto(presupuesto_id)

    def _on_guardar_presupuesto(self):
        self.presupuesto_ctrl.guardar_partida_actual()
        self._post_accion_recálculo_global()

    def _on_guardar_como_presupuesto(self):
        self.presupuesto_ctrl.duplicar_presupuesto_actual()
        self._post_accion_recálculo_global()

    def _on_imprimir(self):
        self.presupuesto_ctrl.exportar_pdf()

    def _on_vista_previa(self):
        self.presupuesto_ctrl.vista_previa_pdf()

    def _on_enviar_email(self):
        """
        NUEVO: Envía el presupuesto por email.
        Genera el PDF primero, luego abre el diálogo de envío.
        """
        self.presupuesto_ctrl.enviar_por_email()

    def _on_parametros_sistema(self):
        try:
            from presupuestos.ui.dialogs.parametros_sistema_dialog import ParametrosSistemaDialog
            dlg = ParametrosSistemaDialog(self.svc, self)
            if dlg.exec():
                params = self.svc.obtener_parametros_sistema()
                self.sb_desperdicio.setValue(int(params.get('desperdicio_defecto', 2)))
                self.sb_fv_pct.setValue(int(params.get('fv_defecto', 25)))
                self.cbo_color_global.setCurrentText(params.get('color_global_defecto', 'VARIOS'))
                QMessageBox.information(self, "Parámetros Actualizados",
                                        "Los parámetros del sistema se han actualizado correctamente.\n\nLos nuevos valores de Desperdicio y F.V. se aplicarán a las próximas partidas.")
        except ImportError as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el diálogo de Parámetros del Sistema:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al abrir Parámetros del Sistema:\n\n{str(e)}")

    def _on_manual_operativo(self):
        manual_path = r"D:\vah\manuales\pdf\operativo\VAH_Manual_Operativo_Presupuestos.pdf"
        if os.path.exists(manual_path):
            try:
                os.startfile(manual_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el Manual Operativo:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Manual no encontrado",
                                f"El archivo del Manual Operativo no existe:\n{manual_path}\n\nPor favor, contacte al área de soporte.")

    def _on_manual_tecnico(self):
        manual_path = r"D:\vah\manuales\pdf\técnico\VAH_Manual_Tecnico_Presupuestos.pdf"
        if os.path.exists(manual_path):
            try:
                os.startfile(manual_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el Manual Técnico:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Manual no encontrado",
                                f"El archivo del Manual Técnico no existe:\n{manual_path}\n\nPor favor, contacte al área de soporte.")

    def _on_acerca_de(self):
        about_text = """<h3>VAH - Sistema de Presupuestos</h3>
<p style="text-align: center;"><b>Versión:</b> 2.0.0</p>
<p style="text-align: center;"><b>Desarrollado por:</b> Equipo de Desarrollo VAH</p>
<p style="text-align: center;"><b>Fecha:</b> 2024</p>
<p style="text-align: center;"><b>Contacto:</b> soporte@vah.com</p>
<hr>
<p style="text-align: center;">Sistema integral para gestión de presupuestos en aluminio y herrería.</p>
"""
        QMessageBox.about(self, "Acerca de VAH", about_text)

    def _on_nueva_partida(self):
        if hasattr(self, 'presupuesto_ctrl') and self.presupuesto_ctrl:
            self.presupuesto_ctrl.crear_nueva_partida()
        else:
            QMessageBox.warning(self, "Nueva Partida", "El controlador de presupuestos no está disponible.")
        self._post_accion_recálculo_global()

    def _on_duplicar_partida(self):
        if hasattr(self, 'presupuesto_ctrl') and self.presupuesto_ctrl:
            self.presupuesto_ctrl.duplicar_partida_actual()
        else:
            QMessageBox.warning(self, "Duplicar Partida", "El controlador de presupuestos no está disponible.")
        self._post_accion_recálculo_global()

    def _on_eliminar_partida(self):
        if hasattr(self, 'presupuesto_ctrl') and self.presupuesto_ctrl:
            self.presupuesto_ctrl.eliminar_partida_actual()
        else:
            QMessageBox.warning(self, "Eliminar Partida", "El controlador de presupuestos no está disponible.")
        self._post_accion_recálculo_global()

    def _on_navegar_partidas(self):
        if not self.presupuesto_ctrl.presupuesto_id:
            QMessageBox.warning(self, "Navegar Partidas", "No hay un presupuesto cargado.")
            return
        from presupuestos.ui.dialogs.navegar_partidas_dialog import NavegarPartidasDialog
        dlg = NavegarPartidasDialog(self, self.presupuesto_ctrl)
        if dlg.exec():
            indice = dlg.get_indice_seleccionado()
            if indice >= 0:
                self.presupuesto_ctrl.cargar_partida_por_indice(indice)

    def _on_recalcular_todo(self):
        if getattr(self, '_prog', False):
            return
        viejo = getattr(self, "_dim_prev_partida", (float(self.sp_ancho.value()), float(self.sp_alto.value())))
        try:
            self._prog = True
            self._propagar_dimensiones_con_regla_paquetes(viejo)
            self._dim_prev_partida = (float(self.sp_ancho.value()), float(self.sp_alto.value()))
            for r in range(self.tbl.rowCount()):
                self._calc_std_row(r)
            for r in range(self.tbl_he.rowCount()):
                self._calc_he_row(r)
            if hasattr(self, 'tbl_anidada') and self._tabla_anidada_activa:
                for r in range(self.tbl_anidada.rowCount()):
                    self._calc_anidada_row(r)
            self._recalc_summary()
        finally:
            self._prog = False
        if hasattr(self, 'recalculo_global_ctrl') and self.recalculo_global_ctrl:
            self.recalculo_global_ctrl.cancelar_auto()
            self.recalculo_global_ctrl.ejecutar(mostrar_mensaje=True)


def main():
    app = QApplication(sys.argv)
    w = PresupuestosWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()