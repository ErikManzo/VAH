# -*- coding: utf-8 -*-
r"""
=========================================================
Archivo: D:\vah\proveedores\art\pantalla_proveedores.py
Módulo : VAH - Proveedores (GUI PyQt6)
=========================================================

VERSIÓN SIMPLIFICADA:
- Solo "Pantalla" como opción de salida (sin PDF, impresora, CSV, XLSX)
- Mantiene: CRUD completo, búsqueda, edición, eliminación, agrupar
- CORREGIDO: Error de filtros de teclado eliminado
"""

from __future__ import annotations

import sys
import os
import re
import traceback
import logging

from common.estilos import aplicar_estilo
from common.focus_simple import NavLineEdit, NavComboBox
from common.logger_config import get_logger
from common.manuales import abrir_manual_pdf
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGroupBox, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSpacerItem, QSizePolicy, QHBoxLayout, QStatusBar, QInputDialog, QDialog, QMenuBar
)
from PyQt6.QtGui import (
    QIntValidator, QIcon, QColor, QPalette, QFont, QAction, QKeySequence
)
from PyQt6.QtCore import Qt, QRect, QTimer, QObject, QEvent

# Repositorio (SQL Server)
from proveedores.repositories.proveedor_repository import ProveedorRepository


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
def _build_logger() -> logging.Logger:
    return get_logger("proveedores.art.pantalla")


LOGGER = _build_logger()


def log_exception(context: str, ex: Exception):
    tb = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
    LOGGER.error("%s | %s\n%s", context, str(ex), tb)


# =========================================================
# Ventana principal
# =========================================================
class PantallaProveedores(QWidget):
    # Índices de columnas
    COL_ID = 0
    COL_CHECK = 1
    COL_EMPRESA = 2
    COL_TIPO_PROVEEDOR = 3
    COL_NOMBRE_AGENTE = 4

    def __init__(self):
        super().__init__()
        try:
            # ======== Ventana ========
            aplicar_estilo(self)
            self.setWindowTitle("VAH — Módulo Proveedores")
            try:
                self.setWindowIcon(QIcon(r"D:\vah\logo_00001.ico"))
            except Exception as e:
                log_exception("Icono de ventana", e)

            # Geometría
            self._geom_applied = False
            self._workspace_rect = self._read_workspace_env()

            # Fondo
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(200, 210, 220))
            self.setPalette(palette)

            # Status bar
            self.status = QStatusBar(self)

            # Estado / Repositorio
            self.modo = "inicio"
            self.proveedor_id_edicion = None
            self._guardando = False
            self._pantalla_cache = None
            self.service = ProveedorRepository()

            # ======== Layout principal ========
            self.layout_principal = QVBoxLayout(self)
            self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.layout_principal.setContentsMargins(8, 8, 8, 8)
            self.layout_principal.setSpacing(8)

            # ======== Menús ========
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
            act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("Proveedores", "operativo", self))
            menu_ayuda.addAction(act_manual_operativo)

            act_manual_tecnico = QAction("Manual Tecnico", self)
            act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("Proveedores", "tecnico", self))
            menu_ayuda.addAction(act_manual_tecnico)

            # ======== Grupo formulario ========
            self.group_box = QGroupBox("Registro de Proveedores")
            self.group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.group_box.setMinimumHeight(320)
            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(10)

            # === Campos ===
            self.txtEmpresa = NavLineEdit()

            self.cmbTipoProveedor = NavComboBox()
            self.cmbTipoProveedor.addItems(["ALUMINIO", "HERRERÍA", "VIDRIO", "HERRAJES", "OTROS"])
            self.txtNombreAgente = NavLineEdit()

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

            self.txtRFC = QLineEdit()
            self.txtRFC.setPlaceholderText("ABC-010203-1A2 ó ABCD-010203-XYZ")
            self.txtTelefono = QLineEdit()
            self.txtTelefono.setInputMask("00-0000-0000;_")
            self.txtCorreo = QLineEdit()

            # === Normalizaciones ===
            for campo in [
                self.txtEmpresa, self.txtNombreAgente, self.txtDireccion,
                self.txtNumInterior, self.txtColonia, self.txtMunicipio
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

            self.btnPantalla = QPushButton("Pantalla")
            self.btnPantalla.setVisible(False)

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

            # Campo Buscar
            self.txtBuscar = QLineEdit()
            self.txtBuscar.setPlaceholderText("Escriba para buscar por EMPRESA...")
            self.txtBuscar.textChanged.connect(lambda t: self._on_buscar_cambia(self._to_upper(t)))

            # === Layout del formulario ===
            # Renglón 1: EMPRESA
            grid.addWidget(QLabel("Empresa:"), 0, 0)
            grid.addWidget(self.txtEmpresa, 0, 1, 1, 9)
            # Renglón 2: TIPO + NOMBRE AGENTE
            grid.addWidget(QLabel("Tipo de proveedor:"), 1, 0)
            grid.addWidget(self.cmbTipoProveedor, 1, 1)
            grid.addWidget(QLabel("Nombre agente:"), 1, 2)
            grid.addWidget(self.txtNombreAgente, 1, 3, 1, 7)
            # Renglón 3: DIRECCIÓN + EXTERIOR + INTERIOR + CP
            grid.addWidget(QLabel("Dirección:"), 2, 0)
            grid.addWidget(self.txtDireccion, 2, 1, 1, 3)
            grid.addWidget(QLabel("# Exterior:"), 2, 4)
            grid.addWidget(self.txtNumExterior, 2, 5)
            grid.addWidget(QLabel("# Interior:"), 2, 6)
            grid.addWidget(self.txtNumInterior, 2, 7)
            grid.addWidget(QLabel("C.P.:"), 2, 8)
            grid.addWidget(self.txtCP, 2, 9)
            # Renglón 4: COLONIA + MUNICIPIO + ESTADO
            grid.addWidget(QLabel("Colonia:"), 3, 0)
            grid.addWidget(self.txtColonia, 3, 1, 1, 3)
            grid.addWidget(QLabel("Municipio:"), 3, 4)
            grid.addWidget(self.txtMunicipio, 3, 5, 1, 3)
            grid.addWidget(QLabel("Estado:"), 3, 8)
            grid.addWidget(self.cmbEstado, 3, 9)
            # Renglón 5: RFC + TELÉFONO + CORREO
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
            grid.addWidget(QLabel("Buscar por empresa:"), 7, 0)
            grid.addWidget(self.txtBuscar, 7, 1, 1, 10)

            self.group_box.setLayout(grid)

            # ======== Tabla ========
            self.tabla = QTableWidget()
            self._configurar_tabla_columnas()
            self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.tabla.horizontalHeader().setMinimumSectionSize(60)
            self.tabla.setColumnWidth(self.COL_CHECK, 36)
            self.tabla.setSelectionBehavior(self.tabla.SelectionBehavior.SelectRows)
            self.tabla.setEditTriggers(self.tabla.EditTrigger.NoEditTriggers)
            self.tabla.setMinimumHeight(420)
            self.tabla.setSortingEnabled(True)
            self.tabla.cellDoubleClicked.connect(self._fila_doble_click)

            # ======== Layout final ========
            self.layout_principal.addWidget(self.group_box)
            self.layout_principal.addWidget(self.tabla)
            self.layout_principal.addWidget(self.status)

            # ======== Conexiones ========
            self.btnGuardar.clicked.connect(self._guardar_click)
            self.btnEditar.clicked.connect(self._modo_editar)
            self.btnEliminar.clicked.connect(self._modo_eliminar)
            self.btnLimpiar.clicked.connect(self._modo_inicio)
            self.btnRefresh.clicked.connect(self._refrescar)
            self.btnPantalla.clicked.connect(self._modo_pantalla)
            self.btnSalir.clicked.connect(self._salir)
            self.btnAgrupar.clicked.connect(self._agrupar_click)
            self.btnRegresar.clicked.connect(self._modo_inicio)

            # ======== Atajos ========
            self._setup_shortcuts()
            self._setup_simple_navigation()
            self._modo_inicio()

        except Exception as e:
            log_exception("Error inicializando pantalla", e)
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{e}")

    # ------------------------------
    # Geometría
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
            QTimer.singleShot(0, self._raise_and_focus)

    def _raise_and_focus(self):
        try:
            self.raise_()
            self.activateWindow()
        except Exception as e:
            log_exception("raise/activate", e)

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
        _act("Delete", self._delete_shortcut_action)
        _act("F5", self._refrescar)
        _act("Esc", self._salir)

    def _delete_shortcut_action(self):
        try:
            if self.modo == "eliminar" and self.tabla.isVisible() and self.tabla.currentRow() >= 0:
                self._fila_doble_click(self.tabla.currentRow(), self.COL_EMPRESA)
            else:
                self._modo_eliminar()
        except Exception as e:
            log_exception("Delete shortcut", e)

    def _setup_simple_navigation(self) -> None:
        """Configura el orden de tabulación simple (Enter = Tab)."""
        widgets_en_orden = [
            self.txtEmpresa,
            self.cmbTipoProveedor,
            self.txtNombreAgente,
            self.txtDireccion,
            self.txtNumExterior,
            self.txtNumInterior,
            self.txtCP,
            self.txtColonia,
            self.txtMunicipio,
            self.cmbEstado,
            self.txtRFC,
            self.txtTelefono,
            self.txtCorreo,
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
                            outer.tabla.setCurrentCell(curr, outer.COL_EMPRESA)
                            outer.tabla.setFocus()
                            return True
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        if rc > 0:
                            row = outer.tabla.currentRow()
                            if row < 0:
                                row = 0
                                outer.tabla.setCurrentCell(row, outer.COL_EMPRESA)
                            outer._fila_doble_click(row, outer.COL_EMPRESA)
                            return True
                return False
        
        class _TableEnterFilter(QObject):
            def eventFilter(self, obj, ev):
                if obj is outer.tabla and ev.type() == QEvent.Type.KeyPress and outer.modo in ("editar","eliminar"):
                    if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        row = outer.tabla.currentRow()
                        if row >= 0:
                            outer._fila_doble_click(row, outer.COL_EMPRESA)
                            return True
                return False
        
        self._search_filter = _SearchBoxFilter(self)
        self._table_filter = _TableEnterFilter(self)
        self.txtBuscar.installEventFilter(self._search_filter)
        self.tabla.installEventFilter(self._table_filter)

    # -----------------------------------------------------
    # Configuración de tabla
    # -----------------------------------------------------
    def _configurar_tabla_columnas(self):
        self.tabla.setColumnCount(15)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "✔", "Empresa", "Tipo proveedor", "Nombre agente", "Dirección",
            "# Exterior", "# Interior", "C.P.", "Colonia", "Municipio", "Estado",
            "R.F.C.", "Teléfono", "Correo"
        ])
        self.tabla.hideColumn(self.COL_ID)
        self.tabla.setColumnHidden(self.COL_CHECK, True)

    def _llenar_tabla(self, registros, para_agrupar=False):
        try:
            self.tabla.setRowCount(0)
            self.tabla.setColumnHidden(self.COL_CHECK, not para_agrupar)

            for row in registros:
                fila = self.tabla.rowCount()
                self.tabla.insertRow(fila)

                if hasattr(row, "to_dict") and callable(getattr(row, "to_dict")):
                    dic = row.to_dict()
                elif isinstance(row, dict):
                    dic = dict(row)
                else:
                    dic = {
                        "id": getattr(row, "id", None),
                        "empresa": getattr(row, "empresa", None),
                        "tipo_proveedor": getattr(row, "tipo_proveedor", None),
                        "nombre_agente": getattr(row, "nombre_agente", None),
                        "direccion": getattr(row, "direccion", None),
                        "num_exterior": getattr(row, "num_exterior", None),
                        "num_interior": getattr(row, "num_interior", None),
                        "cp": getattr(row, "cp", None),
                        "colonia": getattr(row, "colonia", None),
                        "municipio": getattr(row, "municipio", None),
                        "estado": getattr(row, "estado", None),
                        "rfc": getattr(row, "rfc", None),
                        "telefono": getattr(row, "telefono", None),
                        "correo": getattr(row, "correo", None),
                    }

                self.tabla.setItem(fila, self.COL_ID, QTableWidgetItem("" if dic.get("id") is None else str(dic.get("id"))))

                chk_item = QTableWidgetItem("")
                chk_item.setFlags(chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                chk_item.setCheckState(Qt.CheckState.Unchecked)
                self.tabla.setItem(fila, self.COL_CHECK, chk_item)

                self.tabla.setItem(fila, self.COL_EMPRESA, QTableWidgetItem(self._s(dic.get("empresa"))))
                self.tabla.setItem(fila, self.COL_TIPO_PROVEEDOR, QTableWidgetItem(self._s(dic.get("tipo_proveedor"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE, QTableWidgetItem(self._s(dic.get("nombre_agente"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 1, QTableWidgetItem(self._s(dic.get("direccion"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 2, QTableWidgetItem(self._s(dic.get("num_exterior"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 3, QTableWidgetItem(self._s(dic.get("num_interior"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 4, QTableWidgetItem(self._s(dic.get("cp"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 5, QTableWidgetItem(self._s(dic.get("colonia"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 6, QTableWidgetItem(self._s(dic.get("municipio"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 7, QTableWidgetItem(self._s(dic.get("estado"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 8, QTableWidgetItem(self._s(dic.get("rfc"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 9, QTableWidgetItem(self._s(dic.get("telefono"))))
                self.tabla.setItem(fila, self.COL_NOMBRE_AGENTE + 10, QTableWidgetItem(self._s(dic.get("correo"))))
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
        rfc = (rfc or "").replace(" ", "").replace("-", "").upper()
        if not rfc:
            return ""
        if len(rfc) == 12:
            return f"{rfc[:3]}-{rfc[3:9]}-{rfc[9:]}"
        if len(rfc) == 13:
            return f"{rfc[:4]}-{rfc[4:10]}-{rfc[10:]}"
        return rfc

    # -----------------------------------------------------
    # Modos
    # -----------------------------------------------------
    def _modo_inicio(self):
        try:
            self.modo = "inicio"
            self.proveedor_id_edicion = None
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
            self.status.showMessage("Pantalla en estado inicial.", 3000)
        except Exception as e:
            log_exception("Modo inicio", e)

    def _modo_editar(self):
        try:
            self.modo = "editar"
            self.proveedor_id_edicion = None
            self._limpiar_campos_form()
            self._set_form_habilitado(False)

            self.txtBuscar.setEnabled(True)
            self.txtBuscar.setFocus()
            self.tabla.setEnabled(True)
            self.tabla.show()
            self._llenar_tabla([])

        except Exception as e:
            log_exception("Modo editar", e)

    def _modo_eliminar(self):
        try:
            self.modo = "eliminar"
            self.proveedor_id_edicion = None
            self._limpiar_campos_form()
            self._set_form_habilitado(False)

            self.txtBuscar.setEnabled(True)
            self.txtBuscar.setFocus()
            self.tabla.setEnabled(True)
            self.tabla.show()
            self._llenar_tabla([])

        except Exception as e:
            log_exception("Modo eliminar", e)

    def _modo_pantalla(self):
        """Muestra todos los registros en pantalla (sin opciones de impresión/exportación)"""
        try:
            self.modo = "pantalla"
            self.proveedor_id_edicion = None

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

            self.status.showMessage(f"{len(registros)} registros encontrados.", 3000)

        except Exception as e:
            log_exception("Modo pantalla", e)
            QMessageBox.critical(self, "Error", f"Ocurrió un error al mostrar los datos:\n{e}")

    # -----------------------------------------------------
    # Guardar
    # -----------------------------------------------------
    def _guardar_click(self):
        try:
            if self._guardando:
                return

            self._guardando = True

            if not self.txtEmpresa.text().strip():
                QMessageBox.warning(self, "Validación", "El campo 'Empresa' es obligatorio.")
                return

            proveedor = {
                "empresa": self.txtEmpresa.text().strip().upper(),
                "tipo_proveedor": self.cmbTipoProveedor.currentText(),
                "nombre_agente": self.txtNombreAgente.text().strip().upper() or None,
                "direccion": self.txtDireccion.text().strip().upper() or None,
                "num_exterior": self.txtNumExterior.text().strip() or None,
                "num_interior": self.txtNumInterior.text().strip().upper() or None,
                "cp": self.txtCP.text().strip() or None,
                "colonia": self.txtColonia.text().strip().upper() or None,
                "municipio": self.txtMunicipio.text().strip().upper() or None,
                "estado": self.cmbEstado.currentText(),
                "rfc": self.txtRFC.text().strip().upper() or None,
                "telefono": self.txtTelefono.text().strip() or None,
                "correo": self.txtCorreo.text().strip().lower() or None,
                "tipo": self.cmbTipoProveedor.currentText(),
            }

            if self.proveedor_id_edicion is None:
                resultado = self.service.insertar(proveedor)
                msg = "guardado"
            else:
                proveedor["id"] = self.proveedor_id_edicion
                resultado = self.service.actualizar(proveedor)
                msg = "actualizado"

            if resultado:
                QMessageBox.information(self, "Éxito", f"Proveedor {msg} correctamente.")
                self._modo_inicio()
                self._refrescar()
            else:
                busqueda = self.service.buscar_por_empresa(proveedor["empresa"])
                if busqueda:
                    QMessageBox.information(self, "Éxito", f"Proveedor {msg} correctamente (verificado).")
                    self._modo_inicio()
                    self._refrescar()
                else:
                    QMessageBox.warning(self, "Error", f"No se pudo {msg} el proveedor.")

        except Exception as e:
            log_exception("Guardar", e)
            QMessageBox.critical(self, "Error", f"Error al guardar:\n{e}")
        finally:
            self._guardando = False

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
            _ = self.service.listar_todos()
        except Exception as e:
            log_exception("Salir -> listar_todos()", e)
        self.close()

    # -----------------------------------------------------
    # Agrupar
    # -----------------------------------------------------
    def _agrupar_click(self):
        try:
            todos = self.service.listar_todos()

            if len(todos) < 2:
                QMessageBox.information(
                    self, "Agrupar",
                    "No hay suficientes registros para buscar duplicados.\n"
                    "Se necesitan al menos 2 proveedores."
                )
                return

            duplicados_por_empresa = {}
            for p in todos:
                empresa = (p.get("empresa") or "").upper()
                if empresa:
                    if empresa not in duplicados_por_empresa:
                        duplicados_por_empresa[empresa] = []
                    duplicados_por_empresa[empresa].append(p)

            grupos_duplicados = []
            for empresa, grupo in duplicados_por_empresa.items():
                if len(grupo) > 1:
                    grupos_duplicados.append({
                        "criterio": f"Misma empresa: {empresa}",
                        "registros": grupo
                    })

            if not grupos_duplicados:
                QMessageBox.information(
                    self, "Agrupar",
                    "No se encontraron duplicados.\n"
                    "No hay dos proveedores con la misma empresa."
                )
                return

            from proveedores.ui.dialogs.unificar_proveedores_dialog import UnificarProveedoresDialog

            items = [f"{g['criterio']} ({len(g['registros'])} registros)" for g in grupos_duplicados]
            item, ok = QInputDialog.getItem(
                self, "Seleccionar grupo",
                "Se encontraron múltiples grupos de duplicados.\n"
                "Seleccione cuál grupo desea revisar:",
                items, 0, False
            )

            if not ok or not item:
                return

            indice = items.index(item)
            grupo_seleccionado = grupos_duplicados[indice]

            dialog = UnificarProveedoresDialog(grupo_seleccionado["registros"], self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                id_conservar = dialog.get_seleccionado_id()
                ids_eliminar = dialog.get_ids_a_eliminar()

                if not id_conservar:
                    QMessageBox.warning(self, "Agrupar", "No se seleccionó un registro para conservar.")
                    return

                if not ids_eliminar:
                    QMessageBox.warning(self, "Agrupar", "No hay registros para eliminar.")
                    return

                ganador = None
                for p in grupo_seleccionado["registros"]:
                    if p.get("id") == id_conservar:
                        ganador = p
                        break

                if not ganador:
                    QMessageBox.warning(self, "Agrupar", "No se encontró el registro seleccionado.")
                    return

                for pid in ids_eliminar:
                    eliminado = None
                    for p in grupo_seleccionado["registros"]:
                        if p.get("id") == pid:
                            eliminado = p
                            break
                    if eliminado:
                        for campo in ["direccion", "colonia", "municipio", "estado",
                                      "telefono", "correo", "nombre_agente", "num_exterior",
                                      "num_interior", "cp"]:
                            if not ganador.get(campo) and eliminado.get(campo):
                                ganador[campo] = eliminado[campo]

                ganador["id"] = id_conservar
                self.service.actualizar(ganador)

                for pid in ids_eliminar:
                    self.service.eliminar(pid)

                QMessageBox.information(
                    self, "Unificación completada",
                    f"Se conservó el registro ID: {id_conservar}\n"
                    f"Se eliminaron {len(ids_eliminar)} registro(s) duplicado(s)."
                )

                self._refrescar()
                self._modo_inicio()

        except Exception as e:
            log_exception("Agrupar click", e)
            QMessageBox.critical(self, "Error", f"Error al agrupar:\n{e}")

    # -----------------------------------------------------
    # Búsqueda
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
                resultados = [r for r in self._pantalla_cache if (r.get("empresa") or "").upper().startswith(txt)]
            else:
                try:
                    resultados = self.service.buscar_por_empresa(txt)
                except Exception as e:
                    log_exception("Buscar por empresa (repo)", e)
                    resultados = []

            self._llenar_tabla(resultados, para_agrupar=(self.modo == "agrupar"))
            self.tabla.show()
            if resultados and self.modo in ("editar", "eliminar"):
                self.tabla.setCurrentCell(0, self.COL_EMPRESA)
        except Exception as e:
            log_exception("Buscar incremental (UI)", e)

    # -----------------------------------------------------
    # Doble clic
    # -----------------------------------------------------
    def _fila_doble_click(self, fila, col):
        try:
            it_id = self.tabla.item(fila, self.COL_ID)
            if not it_id or not it_id.text().isdigit():
                return
            pid = int(it_id.text())

            if self.modo == "editar":
                proveedor = self.service.obtener_por_id(pid)
                if not proveedor:
                    QMessageBox.warning(self, "Editar", "No se encontró el registro.")
                    return

                self._set_form_habilitado(True)
                self.group_box.show()
                self.tabla.hide()
                self._cargar_proveedor_en_form(proveedor)
                self.proveedor_id_edicion = pid
                # Llevar el foco al campo Empresa para comenzar la edición
                self.txtEmpresa.setFocus()
                self.txtEmpresa.selectAll()

            elif self.modo == "eliminar":
                # Preguntar directamente sin cargar el formulario
                resp = QMessageBox.question(
                    self, "Eliminar",
                    f"¿Estás seguro de eliminar el proveedor: {pid}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resp == QMessageBox.StandardButton.Yes:
                    if self.service.eliminar(pid):
                        QMessageBox.information(self, "Eliminar", "Información eliminada.")
                        self._on_buscar_cambia(self.txtBuscar.text())
                    else:
                        QMessageBox.warning(self, "Eliminar", "No se pudo eliminar.")
        except Exception as e:
            log_exception("Doble click", e)

    # -----------------------------------------------------
    # Utilidades formulario
    # -----------------------------------------------------
    def _cargar_proveedor_en_form(self, p):
        try:
            if hasattr(p, "to_dict"):
                d = p.to_dict()
            elif isinstance(p, dict):
                d = p
            else:
                d = {"empresa": str(p)} if p else {}

            self.txtEmpresa.setText(d.get("empresa") or "")

            tipo_val = d.get("tipo_proveedor") or d.get("tipo") or "OTROS"
            idx = self.cmbTipoProveedor.findText(tipo_val)
            if idx >= 0:
                self.cmbTipoProveedor.setCurrentIndex(idx)

            self.txtNombreAgente.setText(d.get("nombre_agente") or "")
            self.txtDireccion.setText(d.get("direccion") or "")
            self.txtNumExterior.setText(d.get("num_exterior") or "")
            self.txtNumInterior.setText(d.get("num_interior") or "")
            self.txtCP.setText(d.get("cp") or "")
            self.txtColonia.setText(d.get("colonia") or "")
            self.txtMunicipio.setText(d.get("municipio") or "")

            estado_val = d.get("estado") or "JALISCO"
            idx_estado = self.cmbEstado.findText(estado_val)
            if idx_estado >= 0:
                self.cmbEstado.setCurrentIndex(idx_estado)

            self.txtRFC.setText(d.get("rfc") or "")
            self.txtTelefono.setText(d.get("telefono") or "")
            self.txtCorreo.setText((d.get("correo") or "").lower())
        except Exception as e:
            log_exception("Cargar proveedor", e)

    def _limpiar_campos_form(self):
        try:
            self.txtEmpresa.clear()
            self.cmbTipoProveedor.setCurrentIndex(4)
            self.txtNombreAgente.clear()
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
                self.txtEmpresa, self.cmbTipoProveedor, self.txtNombreAgente, self.txtDireccion,
                self.txtNumExterior, self.txtNumInterior, self.txtCP, self.txtColonia,
                self.txtMunicipio, self.cmbEstado, self.txtRFC, self.txtTelefono, self.txtCorreo
            ]:
                w.setEnabled(habilitar)
        except Exception as e:
            log_exception("Habilitar formulario", e)


# ---------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------
if __name__ == "__main__":
    vah_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.isdir(vah_root) and vah_root not in sys.path:
        sys.path.insert(0, vah_root)

    app = QApplication(sys.argv)
    ventana = PantallaProveedores()
    ventana.show()
    ventana.raise_()
    ventana.activateWindow()
    sys.exit(app.exec())
