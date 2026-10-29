# -*- coding: utf-8 -*-
r"""
VAH — Módulo Clientes (GUI)
Ubicación: D:\vah\clientes\art\pantalla_clientes.py
VERSIÓN FINAL CONSOLIDADA:
- Menús organizados (Archivo, Herramientas, Ayuda)
- Botones CRUD con colores profesionales
- Navegación simple con focus_simple.py
- Editar/Eliminar optimizados
"""
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGroupBox, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QSpacerItem, QSizePolicy, QHBoxLayout, QInputDialog, QDialog, QMenuBar
)
from PyQt6.QtGui import (
    QIntValidator, QIcon, QPageSize, QPainter, QColor, QPalette, QFont, QAction, QKeySequence, QPageLayout, QPen, QTextDocument
)
from PyQt6.QtCore import Qt, QRect, QRectF, QEvent, QObject, QSizeF
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
import sys, re, os, traceback, logging
from common.estilos import aplicar_estilo
from common.app_paths import get_cache_dir, get_resource_path
from common.focus_simple import NavLineEdit, NavComboBox
from common.manuales import abrir_manual_pdf
from common.logger_config import get_logger
from clientes.services.cliente_service import ClienteService
from clientes.models.cliente import Cliente

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
def _build_logger() -> logging.Logger:
    return get_logger("clientes.art.pantalla")

LOGGER = _build_logger()

def log_exception(context: str, ex: Exception):
    tb = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
    LOGGER.error("%s | %s\n%s", context, str(ex), tb)

import json

# =========================================================
# Ventana principal
# =========================================================
class RegistroClientes(QWidget):
    COL_ID = 0
    COL_CHECK = 1       # Columna de checkboxes (solo visible en modo agrupar)
    COL_TITULO = 2
    COL_NOMBRE = 3
    # ... las demás columnas se desplazan +1 por insertar COL_CHECK

    def __init__(self):
        super().__init__()
        self.cache_path = os.path.join(get_cache_dir(), "cliente_nuevo.json")
        self.cliente_creado_para_presupuestos = False
        try:
            # ======== Ventana ========
            aplicar_estilo(self)
            self.setWindowTitle("VAH — Módulo Clientes")
            for icon_name in ("logo.jpg", "logo.png", "logo_00001.ico"):
                logo_path = get_resource_path(icon_name)
                if os.path.exists(logo_path):
                    self.setWindowIcon(QIcon(logo_path))
                    break

            # Geometría: se aplicará definitivamente en showEvent
            self._geom_applied = False
            self._workspace_rect = self._read_workspace_env()

            # Fondo azul grisáceo pastel
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(200, 210, 220))
            self.setPalette(palette)

            # Estado
            self.modo = "inicio"               # inicio | editar | eliminar | pantalla | agrupar
            self.cliente_id_edicion = None
            self.service = ClienteService()

            # ======== Layout principal ========
            self.layout_principal = QVBoxLayout(self)
            self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.layout_principal.setContentsMargins(8, 8, 8, 8)
            self.layout_principal.setSpacing(8)

            self.menu_bar = QMenuBar(self)
            self.layout_principal.setMenuBar(self.menu_bar)

            # === Menú Archivo ===
            menu_archivo = self.menu_bar.addMenu("&Archivo")
            act_refresh = QAction("Refresh (F5)", self)
            act_refresh.triggered.connect(self._refrescar)
            menu_archivo.addAction(act_refresh)

            act_pantalla = QAction("Pantalla", self)
            act_pantalla.triggered.connect(self._modo_pantalla)
            menu_archivo.addAction(act_pantalla)

            menu_archivo.addSeparator()

            act_salir = QAction("Salir (Esc)", self)
            act_salir.triggered.connect(self._salir)
            menu_archivo.addAction(act_salir)

            # === Menú Herramientas ===
            menu_herramientas = self.menu_bar.addMenu("&Herramientas")
            act_agrupar = QAction("Agrupar coincidencias", self)
            act_agrupar.triggered.connect(self._agrupar_click)
            menu_herramientas.addAction(act_agrupar)

            # === Menú Ayuda ===
            menu_ayuda = self.menu_bar.addMenu("&Ayuda")
            act_manual_operativo = QAction("Manual Operativo", self)
            act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("Clientes", "operativo", self))
            menu_ayuda.addAction(act_manual_operativo)

            act_manual_tecnico = QAction("Manual Tecnico", self)
            act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("Clientes", "tecnico", self))
            menu_ayuda.addAction(act_manual_tecnico)

            # ======== Grupo formulario ========
            self.group_box = QGroupBox("Registro de Clientes")
            self.group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.group_box.setMinimumHeight(320)

            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(10)

            # === Campos ===
            self.cmbTitulo = NavComboBox()
            self.cmbTitulo.addItems(["SR.", "SRA.", "SRITA.", "ARQ.", "ING.", "LIC.", "DR."])

            self.txtNombre = NavLineEdit()
            self.txtAPaterno = NavLineEdit()
            self.txtAMaterno = NavLineEdit()
            self.txtEmpresa = NavLineEdit()
            self.txtDireccion = NavLineEdit()
            self.txtNumExterior = NavLineEdit()
            self.txtNumExterior.setValidator(QIntValidator())
            self.txtNumInterior = NavLineEdit()
            self.txtCP = NavLineEdit()
            self.txtCP.setValidator(QIntValidator())
            self.txtColonia = NavLineEdit()
            self.txtMunicipio = NavLineEdit()

            self.cmbEstado = NavComboBox()
            estados_mexico = [
                "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
                "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima", "Durango",
                "Estado de México", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco",
                "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla",
                "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora",
                "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas"
            ]
            self.cmbEstado.addItems([e.upper() for e in estados_mexico])
            self.cmbEstado.setCurrentText("JALISCO")

            self.txtRFC = NavLineEdit()
            self.txtRFC.setPlaceholderText("ABC-010203-1A2 ó ABCD-010203-XYZ")

            self.txtTelefono = NavLineEdit()
            self.txtTelefono.setInputMask("00-0000-0000;_")

            self.txtCorreo = NavLineEdit()

            # === Normalizaciones en tiempo real ===
            for campo in [
                self.txtNombre, self.txtAPaterno, self.txtAMaterno, self.txtEmpresa,
                self.txtDireccion, self.txtNumInterior, self.txtColonia, self.txtMunicipio
            ]:
                campo.textChanged.connect(lambda t, w=campo: self._forzar_mayusculas(w, t))

            self.txtRFC.textChanged.connect(lambda t: self._forzar_mayusculas(self.txtRFC, t, solo_alfanum=True))
            self.txtCorreo.textChanged.connect(lambda t: self._forzar_minusculas(self.txtCorreo, t))

            # === Botones CRUD principales (visibles con colores) ===
            self.btnGuardar  = QPushButton("Guardar")
            self.btnGuardar.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
            self.btnGuardar.setToolTip("Guardar registro (Ctrl+S)")

            self.btnEditar   = QPushButton("Editar")
            self.btnEditar.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold;")
            self.btnEditar.setToolTip("Modo edición")

            self.btnEliminar = QPushButton("Eliminar")
            self.btnEliminar.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
            self.btnEliminar.setToolTip("Eliminar registro (Delete)")

            self.btnLimpiar  = QPushButton("Limpiar")
            self.btnLimpiar.setStyleSheet("background-color: #6B7280; color: white; font-weight: bold;")
            self.btnLimpiar.setToolTip("Limpiar formulario")

            self.btnRegresar = QPushButton("Regresar")
            self.btnRegresar.setVisible(False)

            # Botones que irán al menú (ocultos)
            self.btnRefresh = QPushButton("Refresh")
            self.btnRefresh.setVisible(False)

            self.btnImprimir = QPushButton("Pantalla")
            self.btnImprimir.setVisible(False)

            self.btnSalir = QPushButton("Salir")
            self.btnSalir.setVisible(False)

            self.btnAgrupar = QPushButton("Agrupar coincidencias")
            self.btnAgrupar.setVisible(False)

            botones_visibles = [self.btnGuardar, self.btnEditar, self.btnEliminar, self.btnLimpiar, self.btnRegresar]
            layout_botones = QHBoxLayout()
            for b in botones_visibles:
                b.setFixedHeight(34)
                layout_botones.addWidget(b)
            layout_botones.addStretch()

            # Campo Buscar por nombre
            self.txtBuscar = QLineEdit()
            self.txtBuscar.setPlaceholderText("Escriba para buscar por NOMBRE...")
            self.txtBuscar.textChanged.connect(lambda t: self._on_buscar_cambia(self._to_upper(t)))

            # === Distribución por renglón ===
            # Renglón 1
            grid.addWidget(QLabel("Título:"), 0, 0)
            grid.addWidget(self.cmbTitulo, 0, 1)
            grid.addWidget(QLabel("Nombre:"), 0, 2)
            grid.addWidget(self.txtNombre, 0, 3, 1, 3)
            grid.addWidget(QLabel("A. Paterno:"), 0, 6)
            grid.addWidget(self.txtAPaterno, 0, 7)
            grid.addWidget(QLabel("A. Materno:"), 0, 8)
            grid.addWidget(self.txtAMaterno, 0, 9)

            # Renglón 2
            grid.addWidget(QLabel("Empresa:"), 1, 0)
            grid.addWidget(self.txtEmpresa, 1, 1, 1, 9)

            # Renglón 3
            grid.addWidget(QLabel("Dirección:"), 2, 0)
            grid.addWidget(self.txtDireccion, 2, 1, 1, 3)
            grid.addWidget(QLabel("# Exterior:"), 2, 4)
            grid.addWidget(self.txtNumExterior, 2, 5)
            grid.addWidget(QLabel("# Interior:"), 2, 6)
            grid.addWidget(self.txtNumInterior, 2, 7)
            grid.addWidget(QLabel("C.P.:"), 2, 8)
            grid.addWidget(self.txtCP, 2, 9)

            # Renglón 4
            grid.addWidget(QLabel("Colonia:"), 3, 0)
            grid.addWidget(self.txtColonia, 3, 1, 1, 3)
            grid.addWidget(QLabel("Municipio:"), 3, 4)
            grid.addWidget(self.txtMunicipio, 3, 5, 1, 3)
            grid.addWidget(QLabel("Estado:"), 3, 8)
            grid.addWidget(self.cmbEstado, 3, 9)

            # Renglón 5
            grid.addWidget(QLabel("R.F.C.:"), 4, 0)
            grid.addWidget(self.txtRFC, 4, 1)
            grid.addWidget(QLabel("Teléfono:"), 4, 2)
            grid.addWidget(self.txtTelefono, 4, 3)
            grid.addWidget(QLabel("Correo:"), 4, 4)
            grid.addWidget(self.txtCorreo, 4, 5, 1, 5)

            # Renglón 6: Botones
            grid.addLayout(layout_botones, 5, 0, 1, 10)

            # Renglón 7: espacio
            grid.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed), 6, 0)

            # Renglón 8: Buscar
            grid.addWidget(QLabel("Buscar por nombre:"), 7, 0)
            grid.addWidget(self.txtBuscar, 7, 1, 1, 10)

            self.group_box.setLayout(grid)

            # ======== Tabla ========
            self.tabla = QTableWidget()
            self._configurar_tabla_columnas()
            self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.tabla.setSortingEnabled(True)
            self.tabla.setSelectionBehavior(self.tabla.SelectionBehavior.SelectRows)
            self.tabla.setEditTriggers(self.tabla.EditTrigger.NoEditTriggers)
            self.tabla.setMinimumHeight(420)
            self.tabla.cellDoubleClicked.connect(self._fila_doble_click)

            # ======== Layout ========
            self.layout_principal.addWidget(self.group_box)
            self.layout_principal.addWidget(self.tabla)

            # ======== Conexiones ========
            self.btnGuardar.clicked.connect(self._guardar_click)
            self.btnEditar.clicked.connect(self._modo_editar)
            self.btnEliminar.clicked.connect(self._modo_eliminar)
            self.btnLimpiar.clicked.connect(self._modo_inicio)
            self.btnRegresar.clicked.connect(self._modo_inicio)
            self.btnRefresh.clicked.connect(self._refrescar)
            self.btnImprimir.clicked.connect(self._modo_pantalla)
            self.btnSalir.clicked.connect(self._salir)
            self.btnAgrupar.clicked.connect(self._agrupar_click)

            # ======== Atajos globales ========
            self._setup_shortcuts()

            # Arranque
            self._modo_inicio()

        except Exception as e:
            log_exception("Error inicializando ventana", e)
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{e}")

        self._setup_simple_navigation()

    # ------------------------------
    # Geometría del área disponible
    # ------------------------------
    def _read_workspace_env(self):
        try:
            x = int(os.getenv("VAH_CHILD_X", "").strip() or "-1")
            y = int(os.getenv("VAH_CHILD_Y", "").strip() or "-1")
            w = int(os.getenv("VAH_CHILD_W", "").strip() or "0")
            h = int(os.getenv("VAH_CHILD_H", "").strip() or "0")
            if x >= 0 and y >= 0 and w > 0 and h > 0:
                return QRect(x, y, w, h)
        except Exception:
            pass
        return None

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_geom_applied", False):
            if self._workspace_rect is not None:
                self.setGeometry(self._workspace_rect)
            else:
                self.showMaximized()
            self._geom_applied = True

    # -----------------------------------------------------
    # Atajos
    # -----------------------------------------------------
    def _setup_shortcuts(self) -> None:
        def _act(seq: str, slot):
            a = QAction(self)
            a.setShortcut(QKeySequence(seq))
            a.triggered.connect(slot)
            self.addAction(a)

        _act("Ctrl+S", self._guardar_click)
        _act("Ctrl+F", lambda: (self.txtBuscar.setEnabled(True), self.txtBuscar.setFocus(), self.txtBuscar.selectAll()))
        _act("Delete", self._eliminar_atajo)
        _act("F5", self._refrescar)
        _act("Esc", self._salir)

    def _eliminar_atajo(self):
        if self.modo == "eliminar" and self.tabla.isVisible():
            filas = self.tabla.selectionModel().selectedRows() if self.tabla.selectionModel() else []
            if filas:
                self._eliminar_por_fila(filas[0].row())
                return
        self._modo_eliminar()

    def _setup_simple_navigation(self) -> None:
        """Configura el orden de tabulación simple (Enter = Tab)."""
        widgets_en_orden = [
            self.cmbTitulo, self.txtNombre, self.txtAPaterno, self.txtAMaterno,
            self.txtEmpresa, self.txtDireccion, self.txtNumExterior, self.txtNumInterior,
            self.txtCP, self.txtColonia, self.txtMunicipio, self.cmbEstado,
            self.txtRFC, self.txtTelefono, self.txtCorreo,
            self.btnGuardar, self.btnEditar, self.btnEliminar, self.btnLimpiar,
            self.btnRegresar,
            self.txtBuscar, self.tabla
        ]
        for anterior, siguiente in zip(widgets_en_orden, widgets_en_orden[1:]):
            self.setTabOrder(anterior, siguiente)
        self._setup_search_keys()

    def _setup_search_keys(self) -> None:
        outer = self

        class _SearchBoxFilter(QObject):
            def eventFilter(self, obj, ev):
                if obj is outer.txtBuscar and ev.type() == QEvent.Type.KeyPress and outer.modo in ("editar","eliminar"):
                    key = ev.key()
                    rc = outer.tabla.rowCount()
                    if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                        if rc > 0:
                            curr = outer.tabla.currentRow()
                            if curr < 0:
                                curr = 0
                            else:
                                curr = max(0, min(rc - 1, curr + (1 if key == Qt.Key.Key_Down else -1)))
                            outer.tabla.setCurrentCell(curr, outer.COL_NOMBRE)
                            outer.tabla.setFocus()
                            return True
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        if rc > 0:
                            row = outer.tabla.currentRow()
                            if row < 0:
                                row = 0
                                outer.tabla.setCurrentCell(row, outer.COL_NOMBRE)
                            outer._fila_doble_click(row, outer.COL_NOMBRE)
                            return True
                return False

        class _TableEnterFilter(QObject):
            def eventFilter(self, obj, ev):
                if obj is outer.tabla and ev.type() == QEvent.Type.KeyPress and outer.modo in ("editar","eliminar"):
                    if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        row = outer.tabla.currentRow()
                        if row >= 0:
                            outer._fila_doble_click(row, outer.COL_NOMBRE)
                            return True
                return False

        self._search_filter = _SearchBoxFilter(self)
        self._table_filter = _TableEnterFilter(self)
        self.txtBuscar.installEventFilter(self._search_filter)
        self.tabla.installEventFilter(self._table_filter)

    # -----------------------------------------------------
    # Config tabla y helpers
    # -----------------------------------------------------
    def _configurar_tabla_columnas(self):
        self.tabla.setColumnCount(17)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "✔", "Título", "Nombre", "A. Paterno", "A. Materno", "Empresa", "Dirección",
            "# Exterior", "# Interior", "C.P.", "Colonia", "Municipio", "Estado",
            "R.F.C.", "Teléfono", "Correo"
        ])
        self.tabla.hideColumn(self.COL_ID)
        self.tabla.setColumnHidden(self.COL_CHECK, True)
        try:
            self.tabla.horizontalHeader().setMinimumSectionSize(60)
            self.tabla.setColumnWidth(self.COL_CHECK, 36)
        except Exception:
            pass

    def _llenar_tabla(self, registros, para_agrupar=False):
        try:
            self.tabla.setRowCount(0)
            self.tabla.setColumnHidden(self.COL_CHECK, not para_agrupar)
            for row in registros:
                fila = self.tabla.rowCount()
                self.tabla.insertRow(fila)
                if isinstance(row, Cliente):
                    data = row.to_list_with_id()
                    dic = {
                        "id": data[0],
                        "titulo": data[1],
                        "nombre": data[2],
                        "a_paterno": data[3],
                        "a_materno": data[4],
                        "empresa": data[5],
                        "direccion": data[6],
                        "num_exterior": data[7],
                        "num_interior": data[8],
                        "cp": data[9],
                        "colonia": data[10],
                        "municipio": data[11],
                        "estado": data[12],
                        "rfc": data[13],
                        "telefono": data[14],
                        "Email": data[15],
                    }
                else:
                    dic = row

                self.tabla.setItem(fila, self.COL_ID, QTableWidgetItem("" if dic.get("id") is None else str(dic.get("id"))))

                chk_item = QTableWidgetItem("")
                chk_item.setFlags(chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                chk_item.setCheckState(Qt.CheckState.Unchecked)
                self.tabla.setItem(fila, self.COL_CHECK, chk_item)

                self.tabla.setItem(fila, self.COL_TITULO, QTableWidgetItem(self._s(dic.get("titulo"))))
                self.tabla.setItem(fila, self.COL_NOMBRE, QTableWidgetItem(self._s(dic.get("nombre"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 1, QTableWidgetItem(self._s(dic.get("a_paterno"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 2, QTableWidgetItem(self._s(dic.get("a_materno"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 3, QTableWidgetItem(self._s(dic.get("empresa"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 4, QTableWidgetItem(self._s(dic.get("direccion"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 5, QTableWidgetItem(self._s(dic.get("num_exterior"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 6, QTableWidgetItem(self._s(dic.get("num_interior"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 7, QTableWidgetItem(self._s(dic.get("cp"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 8, QTableWidgetItem(self._s(dic.get("colonia"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 9, QTableWidgetItem(self._s(dic.get("municipio"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 10, QTableWidgetItem(self._s(dic.get("estado"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 11, QTableWidgetItem(self._s(dic.get("rfc"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 12, QTableWidgetItem(self._s(dic.get("telefono"))))
                self.tabla.setItem(fila, self.COL_NOMBRE + 13, QTableWidgetItem(self._s(dic.get("Email"))))
        except Exception as e:
            log_exception("Llenar tabla", e)

    def _s(self, v):
        return "" if v is None else str(v)

    # -----------------------------------------------------
    # Normalizaciones
    # -----------------------------------------------------
    def _to_upper(self, t: str) -> str:
        return (t or "").upper()

    def _forzar_mayusculas(self, widget: QLineEdit, texto: str, solo_alfanum: bool = False):
        try:
            nuevo = (texto or "").upper()
            if solo_alfanum:
                nuevo = re.sub(r"[^A-Z0-9-]", "", nuevo)
            if nuevo != texto:
                pos = widget.cursorPosition()
                widget.blockSignals(True)
                widget.setText(nuevo)
                widget.setCursorPosition(min(pos, len(nuevo)))
                widget.blockSignals(False)
        except Exception as e:
            log_exception("Forzar mayúsculas", e)

    def _forzar_minusculas(self, widget: QLineEdit, texto: str):
        try:
            nuevo = (texto or "").lower()
            if nuevo != texto:
                pos = widget.cursorPosition()
                widget.blockSignals(True)
                widget.setText(nuevo)
                widget.setCursorPosition(min(pos, len(nuevo)))
                widget.blockSignals(False)
        except Exception as e:
            log_exception("Forzar minúsculas", e)

    def _normalizar_rfc_para_guardar(self, rfc: str) -> str:
        rfc = (rfc or "").replace("-", "").upper()
        if not rfc:
            return ""
        if len(rfc) == 12:
            return f"{rfc[:3]}-{rfc[3:9]}-{rfc[9:]}"
        if len(rfc) == 13:
            return f"{rfc[:4]}-{rfc[4:10]}-{rfc[10:]}"
        return rfc

    # -----------------------------------------------------
    # Modos y botones
    # -----------------------------------------------------
    def _modo_inicio(self):
        try:
            self.modo = "inicio"
            self.cliente_id_edicion = None
            self._pantalla_cache = None
            self._limpiar_campos_form()
            self._set_form_habilitado(True)
            self.txtBuscar.clear()
            self.txtBuscar.setEnabled(False)
            self.btnRegresar.setVisible(False)
            self.tabla.clearSelection()
            self.tabla.setRowCount(0)
            self.tabla.setEnabled(False)
            self.tabla.hide()
            self.group_box.show()
            self.btnAgrupar.setText("Agrupar coincidencias")
        except Exception as e:
            log_exception("Modo inicio", e)

    def _modo_editar(self):
        try:
            self.modo = "editar"
            self.cliente_id_edicion = None
            self._limpiar_campos_form()
            self._set_form_habilitado(False)
            self.txtBuscar.setEnabled(True)
            self.txtBuscar.setFocus()
            self.tabla.setEnabled(True)
            self.tabla.show()
            self._llenar_tabla([])
            self.txtBuscar.setPlaceholderText("Escriba para buscar y haga doble clic para editar…")
        except Exception as e:
            log_exception("Modo editar", e)

    def _modo_eliminar(self):
        try:
            self.modo = "eliminar"
            self.cliente_id_edicion = None
            self._limpiar_campos_form()
            self._set_form_habilitado(False)
            self.txtBuscar.setEnabled(True)
            self.txtBuscar.setFocus()
            self.tabla.setEnabled(True)
            self.tabla.show()
            self._llenar_tabla([])
            self.txtBuscar.setPlaceholderText("Escriba para buscar y doble clic para eliminar…")
        except Exception as e:
            log_exception("Modo eliminar", e)

    def _modo_pantalla(self):
        """Solo muestra los registros en pantalla (sin opciones de impresión/exportación)"""
        try:
            self.modo = "pantalla"
            self.cliente_id_edicion = None
            # Cargar todos los registros
            try:
                registros = self.service.listar_todos()
            except Exception as e:
                log_exception("Pantalla: listar_todos()", e)
                registros = []

            # Mostrar la tabla con los datos
            self.tabla.setEnabled(True)
            self.tabla.show()
            self._llenar_tabla(registros, para_agrupar=False)

            # Configurar UI para modo pantalla
            self.group_box.show()
            self._set_form_habilitado(False)
            self.txtBuscar.setEnabled(True)
            self.txtBuscar.setPlaceholderText("Filtro local en pantalla…")
            self.btnRegresar.setVisible(True)

            # Guardar caché para filtrado
            self._pantalla_cache = list(registros)
        except Exception as e:
            log_exception("Modo pantalla", e)
            QMessageBox.critical(self, "Error", f"Ocurrió un error al mostrar los datos:\n{e}")

    def _modo_agrupar(self):
        try:
            self.modo = "agrupar"
            self.cliente_id_edicion = None
            self._limpiar_campos_form()
            self._set_form_habilitado(False)
            self.txtBuscar.setEnabled(True)
            self.txtBuscar.setFocus()
            self.tabla.setEnabled(True)
            self.tabla.show()
            self._llenar_tabla([], para_agrupar=True)
            self.btnAgrupar.setText("Unificar seleccionados")
            QMessageBox.information(self, "Agrupar coincidencias",
                                    "Escriba en 'Buscar por nombre', marque varios con ✔ y presione 'Unificar seleccionados'.")
        except Exception as e:
            log_exception("Modo agrupar", e)

    # -----------------------------------------------------
    # Acciones de botones
    # -----------------------------------------------------
    def _guardar_click(self):
        try:
            if not self.txtNombre.text().strip():
                QMessageBox.warning(self, "Validación", "El campo 'Nombre' es obligatorio.")
                return

            if self.txtTelefono.text().strip() and not self.txtTelefono.hasAcceptableInput():
                QMessageBox.warning(self, "Validación", "Teléfono incompleto o inválido.")
                return

            rfc_norm = self._normalizar_rfc_para_guardar(self.txtRFC.text()).replace(" ", "")
            if rfc_norm:
                if not re.match(r"^[A-Z0-9]{3,4}-\d{6}-[A-Z0-9]{3}$", rfc_norm):
                    QMessageBox.warning(self, "Validación", "El R.F.C. no tiene un formato válido.")
                    return

            c = Cliente(
                id=self.cliente_id_edicion,
                titulo=self.cmbTitulo.currentText(),
                nombre=self.txtNombre.text().strip().upper(),
                a_paterno=(self.txtAPaterno.text().strip().upper() or None),
                a_materno=(self.txtAMaterno.text().strip().upper() or None),
                empresa=(self.txtEmpresa.text().strip().upper() or None),
                direccion=(self.txtDireccion.text().strip().upper() or None),
                num_exterior=(self.txtNumExterior.text().strip() or None),
                num_interior=(self.txtNumInterior.text().strip().upper() or None),
                cp=(self.txtCP.text().strip() or None),
                colonia=(self.txtColonia.text().strip().upper() or None),
                municipio=(self.txtMunicipio.text().strip().upper() or None),
                estado=self.cmbEstado.currentText(),
                rfc=(rfc_norm or None),
                telefono=(self.txtTelefono.text().strip() or None),
                Email=(self.txtCorreo.text().strip().lower() or None)
            )

            if self.cliente_id_edicion is None:
                id_nuevo = None
                try:
                    id_nuevo = self.service.insertar(c)
                except Exception as e:
                    log_exception("Guardar -> insertar()", e)
                if id_nuevo is None:
                    try:
                        id_nuevo = self.service.guardar(c)
                    except Exception as e:
                        log_exception("Guardar -> guardar()", e)
                        id_nuevo = None
                if id_nuevo:
                    QMessageBox.information(self, "Guardar", "¡Cliente Almacenado con éxito!")
                    # LOGICA PARA PRESUPUESTOS
                    self._reportar_cliente_a_presupuestos(id_nuevo, c)
                    self._modo_inicio()
                else:
                    QMessageBox.warning(self, "Guardar", "No se pudo guardar el registro.")
            else:
                ok = False
                try:
                    ok = self.service.actualizar(c)
                except Exception as e:
                    log_exception("Guardar -> actualizar()", e)
                if ok:
                    QMessageBox.information(self, "Guardar", "¡Cliente Actualizado con éxito!")
                    self._modo_inicio()
                else:
                    QMessageBox.warning(self, "Guardar", "No se pudo actualizar el registro.")
        except Exception as e:
            log_exception("Guardar registro", e)
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar:\n{e}")

    def _reportar_cliente_a_presupuestos(self, id_cliente, cliente_obj):
        """Si existe el archivo de caché, reporta el nuevo cliente."""
        if not os.path.exists(self.cache_path):
            return
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get("presupuestos_activo"):
                partes = [str(x).strip() for x in [cliente_obj.titulo, cliente_obj.nombre, cliente_obj.a_paterno, cliente_obj.a_materno] if x]
                nombre_completo = " ".join(partes)
                data["cliente_creado"] = {
                    "id": id_cliente,
                    "nombre": nombre_completo
                }
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                self.cliente_creado_para_presupuestos = True
        except Exception as e:
            log_exception("Reportar cliente a presupuestos", e)

    def _refrescar(self):
        try:
            if self.tabla.isVisible():
                try:
                    registros = self.service.listar_todos()
                except Exception as e:
                    log_exception("Refrescar: listar_todos()", e)
                    registros = []
                self._llenar_tabla(registros, para_agrupar=(self.modo == "agrupar"))
            self._modo_inicio()
        except Exception as e:
            log_exception("Refrescar", e)

    def _salir(self):
        try:
            # Lógica de limpieza de caché para presupuestos
            if os.path.exists(self.cache_path):
                if not self.cliente_creado_para_presupuestos:
                    try:
                        os.remove(self.cache_path)
                    except:
                        pass
            _ = self.service.listar_todos()
        except Exception as e:
            log_exception("Salir -> listar_todos()", e)
        self.close()

    def _agrupar_click(self):
        try:
            if self.modo != "agrupar":
                self._modo_agrupar()
                return

            ids = self._recolectar_ids_marcados()
            if len(ids) < 2:
                QMessageBox.warning(self, "Agrupar", "Debe marcar al menos dos registros (✔).")
                return

            resp = QMessageBox.question(
                self, "Confirmar",
                "¿Desea continuar con la unificación de información?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp == QMessageBox.StandardButton.No:
                self._refrescar()
                return

            try:
                cliente = self.service.agrupar_coincidencias_por_id(ids)
            except Exception as e:
                log_exception("Agrupar -> service.agrupar_coincidencias_por_id", e)
                QMessageBox.critical(self, "Error", f"No fue posible unificar:\n{e}")
                return

            if cliente:
                d = cliente.to_dict() if hasattr(cliente, "to_dict") else {}
                lineas = []
                for k in [
                    "id","titulo","nombre","a_paterno","a_materno","empresa","direccion",
                    "num_exterior","num_interior","cp","colonia","municipio","estado",
                    "rfc","telefono","Email"
                ]:
                    lineas.append(f"{k.upper()}: {d.get(k,'')}")
                QMessageBox.information(self, "Cliente resultante", "\n".join(lineas))

            self._refrescar()
        except Exception as e:
            log_exception("Agrupar click", e)
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{e}")

    def _recolectar_ids_marcados(self):
        ids = []
        try:
            for fila in range(self.tabla.rowCount()):
                item_chk = self.tabla.item(fila, self.COL_CHECK)
                if item_chk and item_chk.checkState() == Qt.CheckState.Checked:
                    it_id = self.tabla.item(fila, self.COL_ID)
                    if it_id and it_id.text().isdigit():
                        ids.append(int(it_id.text()))
        except Exception as e:
            log_exception("Recolectar IDs marcados", e)
        return ids

    # -----------------------------------------------------
    # Búsqueda incremental
    # -----------------------------------------------------
    def _on_buscar_cambia(self, texto: str):
        try:
            if not self.txtBuscar.isEnabled():
                return

            txt = (texto or "").strip().upper()
            if not txt:
                if self.modo == "pantalla" and isinstance(self._pantalla_cache, list):
                    self._llenar_tabla(self._pantalla_cache, para_agrupar=False)
                else:
                    self._llenar_tabla([], para_agrupar=(self.modo == "agrupar"))
                return

            if self.modo == "pantalla" and isinstance(self._pantalla_cache, list):
                base = self._pantalla_cache
                resultados = [r for r in base if (r.get("nombre") or "").upper().startswith(txt)]
            else:
                resultados = []
                try:
                    if hasattr(self.service, "buscar_por_nombre"):
                        resultados = self.service.buscar_por_nombre(txt)
                    else:
                        todos = self.service.listar_todos()
                        resultados = [r for r in todos if (r.get("nombre") or "").upper().startswith(txt)]
                except Exception as e:
                    log_exception("Buscar incremental", e)
                    resultados = []

            resultados.sort(key=lambda r: (r.get("nombre") or "").upper(), reverse=True)
            self._llenar_tabla(resultados, para_agrupar=(self.modo == "agrupar"))
            self.tabla.show()

            if resultados and self.modo in ("editar","eliminar"):
                self.tabla.setCurrentCell(0, self.COL_NOMBRE)
        except Exception as e:
            log_exception("Buscar incremental (UI)", e)

    # -----------------------------------------------------
    # Doble clic en tabla
    # -----------------------------------------------------
    def _fila_doble_click(self, fila, col):
        try:
            it_id = self.tabla.item(fila, self.COL_ID)
            if not it_id or not it_id.text().isdigit():
                return
            cid = int(it_id.text())

            if self.modo == "editar":
                cliente = None
                try:
                    if hasattr(self.service, "obtener_por_id"):
                        cliente = self.service.obtener_por_id(cid)
                    else:
                        registros = self.service.listar_todos()
                        for r in registros:
                            if r.get("id") == cid:
                                cliente = Cliente(**r)
                                break
                except Exception as e:
                    log_exception("Doble click editar -> obtener_por_id", e)
                    cliente = None

                if not cliente:
                    QMessageBox.warning(self, "Editar", "No se encontró el registro.")
                    return

                self._set_form_habilitado(True)
                self.group_box.show()
                self.tabla.hide()
                self._cargar_cliente_en_form(cliente)
                self.cliente_id_edicion = cliente.id
                # Llevar el foco al campo Título para comenzar la edición
                self.cmbTitulo.setFocus()
                self.cmbTitulo.showPopup()

            elif self.modo == "eliminar":
                # Preguntar directamente sin cargar el formulario
                resp = QMessageBox.question(
                    self, "Eliminar",
                    f"¿Estás seguro de eliminar el cliente: {cid}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resp == QMessageBox.StandardButton.Yes:
                    self._eliminar_por_fila(fila)

        except Exception as e:
            log_exception("Doble click en fila", e)

    def _eliminar_por_fila(self, fila: int):
        try:
            it_id = self.tabla.item(fila, self.COL_ID)
            if not it_id or not it_id.text().isdigit():
                QMessageBox.warning(self, "Eliminar", "No se pudo determinar el ID del registro.")
                return
            cid = int(it_id.text())

            resp = QMessageBox.question(
                self, "Eliminar",
                "¿Estas seguro de eliminar este cliente?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

            ok = False
            try:
                ok = self.service.eliminar(cid)
            except Exception as e:
                log_exception("Eliminar registro", e)

            if ok:
                QMessageBox.information(self, "Eliminar", f"Registro ID {cid} eliminado.")
                self._on_buscar_cambia(self.txtBuscar.text())
            else:
                QMessageBox.warning(self, "Eliminar", f"No se pudo eliminar el registro ID {cid}.")
        except Exception as e:
            log_exception("Eliminar por fila", e)

    # -----------------------------------------------------
    # Utilidades formulario
    # -----------------------------------------------------
    def _cargar_cliente_en_form(self, c: Cliente):
        try:
            self.cmbTitulo.setCurrentText(c.titulo or "SR.")
            self.txtNombre.setText(c.nombre or "")
            self.txtAPaterno.setText(c.a_paterno or "")
            self.txtAMaterno.setText(c.a_materno or "")
            self.txtEmpresa.setText(c.empresa or "")
            self.txtDireccion.setText(c.direccion or "")
            self.txtNumExterior.setText(c.num_exterior or "")
            self.txtNumInterior.setText(c.num_interior or "")
            self.txtCP.setText(c.cp or "")
            self.txtColonia.setText(c.colonia or "")
            self.txtMunicipio.setText(c.municipio or "")
            self.cmbEstado.setCurrentText((c.estado or "JALISCO"))
            self.txtRFC.setText(c.rfc or "")
            self.txtTelefono.setText(c.telefono or "")
            self.txtCorreo.setText((c.Email or "").lower())
        except Exception as e:
            log_exception("Cargar cliente en formulario", e)

    def _limpiar_campos_form(self):
        try:
            self.cmbTitulo.setCurrentIndex(0)
            self.txtNombre.clear()
            self.txtAPaterno.clear()
            self.txtAMaterno.clear()
            self.txtEmpresa.clear()
            self.txtDireccion.clear()
            self.txtNumExterior.clear()
            self.txtNumInterior.clear()
            self.txtCP.clear()
            self.txtColonia.clear()
            self.txtMunicipio.clear()
            self.cmbEstado.setCurrentText("JALISCO")
            self.txtRFC.clear()
            self.txtTelefono.clear()
            self.txtCorreo.clear()
        except Exception as e:
            log_exception("Limpiar formulario", e)

    def _set_form_habilitado(self, habilitar: bool):
        try:
            for w in [
                self.cmbTitulo, self.txtNombre, self.txtAPaterno, self.txtAMaterno, self.txtEmpresa,
                self.txtDireccion, self.txtNumExterior, self.txtNumInterior, self.txtCP,
                self.txtColonia, self.txtMunicipio, self.cmbEstado, self.txtRFC,
                self.txtTelefono, self.txtCorreo
            ]:
                w.setEnabled(habilitar)
        except Exception as e:
            log_exception("Habilitar/Deshabilitar formulario", e)

# -----------------------------------------------------
# Qt app entry
# -----------------------------------------------------
if __name__ == "__main__":
    vah_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.isdir(vah_root) and vah_root not in sys.path:
        sys.path.insert(0, vah_root)

    app = QApplication(sys.argv)
    ventana = RegistroClientes()
    ventana.show()
    ventana.raise_()
    ventana.activateWindow()
    sys.exit(app.exec())