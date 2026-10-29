# -*- coding: utf-8 -*-
"""
Pantalla de Materiales de Aluminio
Ubicación sugerida: D:\vah\materiales\aluminio\pantalla_materiales_aluminio.py

Cambios en esta versión:
- Importación alineada al formato oficial del Excel:
  * Usa parse_excel_oficial() y captura FormatoExcelError (muestra plantilla generada).
  * Reporte detallado: insertados / actualizados / sin cambios / errores.
- Orden de columnas de precios alineado al formato oficial (NP al final).
- Se agrega el largo 5.60 MTS. al combo.
- Botón Refresh: ya NO llena la tabla. Su única función es "refrescar la base"
  (ping/consulta para calentar cache/validar conexión) y mostrar un mensaje.
- Se mantiene todo lo demás (tabla en blanco al iniciar/limpiar, Buscar apagado por defecto,
  validación de clave duplicada, navegación, impresiones, importación, etc.).
- Sin `box-shadow` en QSS (evita warnings de Qt). Opción de sombra por código (flag).
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional

from PyQt6.QtCore import Qt, QRect, QObject, QEvent
from PyQt6.QtGui import QFont, QIcon, QDoubleValidator, QKeySequence, QAction, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QGroupBox, QComboBox, QGridLayout,
    QFileDialog, QAbstractItemView, QStatusBar, QGraphicsDropShadowEffect
)

# --- Config opcional de sombra de enfoque ---
USE_FOCUS_SHADOW = False  # Pon True si deseas ver sombra suave al enfocar inputs

# --- Módulos propios ---
from materiales.aluminio.db_manager import DBManager
from materiales.aluminio.imprimir import imprimir_pdf_guardar
from materiales.aluminio.utils import dec2, ordenar_registros_asc, CAMPOS_PRECIO_BD
from materiales.aluminio.parsers.parse_excel import parse_excel_oficial, FormatoExcelError
from materiales.aluminio.parsers.parse_pdf import importar_pdf_mateco
from materiales.aluminio.parsers.parse_csv import parse_csv_generico
from common.app_paths import get_resource_path
from common.estilos import QSS_BASE
from common.focus_simple import NavLineEdit, NavComboBox
from common.pdf_utils import get_pdf_path
from common.logger_config import get_logger
from common.manuales import abrir_manual_pdf

logger = get_logger("materiales.aluminio.pantalla")


class PantallaMaterialesAluminio(QMainWindow):
    def __init__(self, db_name: str = "aluminio") -> None:
        super().__init__()
        self.setWindowTitle("VAH — Materiales · Aluminio")

        # === Menú Archivo ===
        menu_archivo = self.menuBar().addMenu("&Archivo")
        act_refresh = QAction("Refresh (F5)", self)
        act_refresh.triggered.connect(self._on_refresh)
        menu_archivo.addAction(act_refresh)
        act_imprimir = QAction("Imprimir (Ctrl+P)", self)
        act_imprimir.triggered.connect(self._on_imprimir)
        menu_archivo.addAction(act_imprimir)
        menu_archivo.addSeparator()
        act_salir = QAction("Salir (Esc)", self)
        act_salir.triggered.connect(self._on_salir)
        menu_archivo.addAction(act_salir)

        # === Menú Herramientas ===
        menu_herramientas = self.menuBar().addMenu("&Herramientas")
        act_importar = QAction("Importar", self)
        act_importar.triggered.connect(self._on_importar)
        menu_herramientas.addAction(act_importar)

        # === Menú Ayuda ===
        menu_ayuda = self.menuBar().addMenu("&Ayuda")
        act_manual_operativo = QAction("Manual Operativo", self)
        act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("Materiales_Aluminio", "operativo", self))
        menu_ayuda.addAction(act_manual_operativo)
        act_manual_tecnico = QAction("Manual Técnico", self)
        act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("Materiales_Aluminio", "tecnico", self))
        menu_ayuda.addAction(act_manual_tecnico)

        for icon_name in ("logo.jpg", "logo.png", "logo_00001.ico"):
            logo_path = get_resource_path(icon_name)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break

        # Geometría diferida
        self._geom_applied = False
        self._workspace_rect = self._read_workspace_env()

        # Estado / DB
        self.db = DBManager(db_name=db_name)
        self.modo = "nuevo"  # "nuevo" | "editar"
        self.clave_en_edicion: Optional[str] = None

        # Colecciones para habilitar/deshabilitar
        self._inputs_precios: List[QLineEdit] = []
        self._inputs_all: List[QLineEdit | QComboBox] = []

        # UI
        self._estilos()
        self._ui()
        self._conectar_eventos()
        self.Inicio()  # apartado de "limpio"

        # Instalar event filter para la validación de Duplicado en CLAVE (Enter/Tab)
        self.clave_input.installEventFilter(self)

        # Adjuntar sombra opcional de enfoque
        if USE_FOCUS_SHADOW:
            self._attach_focus_shadows()

        # Traer la ventana al frente
        self.raise_()
        self.activateWindow()

    # ======= Geometría =======
    def _read_workspace_env(self) -> Optional[QRect]:
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

    def showEvent(self, e) -> None:
        super().showEvent(e)
        if not self._geom_applied:
            if self._workspace_rect is not None:
                self.setGeometry(self._workspace_rect)
            else:
                self.showMaximized()
            self._geom_applied = True

    # ======= Estilos =======
    def _estilos(self) -> None:
        # QSS sin box-shadow (Qt no lo soporta).
        self.setStyleSheet(QSS_BASE + """
            QWidget { background-color: #EEF2F6; font-family: Segoe UI; font-size: 10pt; }
            QGroupBox { border: 1px solid #cfd8e3; border-radius: 6px; margin-top: 10px; font-size: 9pt; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;
                               padding: 0 6px; margin-left: 8px; color: #374151; }
            QLineEdit, QComboBox {
                background: #ffffff; border: 1px solid #cfd8e3; padding: 4px 6px; border-radius: 5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #2563EB;
                outline: none;
            }
            QPushButton { background-color: #ffffff; border: 1px solid #cfd8e3; padding: 6px 12px; border-radius: 6px; }
            QPushButton:hover { background-color: #e6eefc; }
            QHeaderView::section { background-color: #1f6feb; color: white; font-weight: bold; border: none; }
            QTableWidget { background: #ffffff; border: 1px solid #cfd8e3; }
        """)

    # ======= (Opcional) Sombra por código en foco =======
    def _attach_focus_shadow(self, w: QWidget) -> None:
        eff = QGraphicsDropShadowEffect(self)
        eff.setBlurRadius(14)
        eff.setOffset(0, 0)
        eff.setColor(QColor(0, 0, 0, 70))
        eff.setEnabled(False)
        w.setGraphicsEffect(eff)

        # Wrap focus in/out para activar/deshabilitar la sombra
        old_in, old_out = w.focusInEvent, w.focusOutEvent

        def fin(e):
            eff.setEnabled(True)
            old_in(e)

        def fout(e):
            eff.setEnabled(False)
            old_out(e)

        w.focusInEvent, w.focusOutEvent = fin, fout

    def _attach_focus_shadows(self) -> None:
        widgets = [self.clave_input, self.descripcion_input, self.largo_input, *self.campos_precios.values()]
        for w in widgets:
            self._attach_focus_shadow(w)

    # ======= UI =======
    def _ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        if not self.statusBar():
            self.setStatusBar(QStatusBar())

        # Datos del Material
        datos_group = QGroupBox("Datos del Material")
        grid_datos = QGridLayout()

        self.clave_input = NavLineEdit()
        self.clave_input.setMaxLength(20)
        self.descripcion_input = NavLineEdit()
        self.descripcion_input.setMaxLength(120)
        self.largo_input = NavComboBox()
        # ACTUALIZADO: se agrega 5.60 MTS. (existe en el Excel oficial)
        self.largo_input.addItems(["6.10 MTS.", "5.60 MTS.", "5.50 MTS.", "5.00 MTS.", "4.60 MTS.", "3.66 MTS."])
        self.largo_input.setCurrentIndex(0)

        grid_datos.addWidget(QLabel("Clave:"), 0, 0)
        grid_datos.addWidget(self.clave_input, 0, 1)
        grid_datos.addWidget(QLabel("Descripción:"), 0, 2)
        grid_datos.addWidget(self.descripcion_input, 0, 3, 1, 4)
        grid_datos.addWidget(QLabel("Largo:"), 0, 7)
        grid_datos.addWidget(self.largo_input, 0, 8)
        grid_datos.setColumnStretch(1, 1)
        grid_datos.setColumnStretch(3, 5)
        grid_datos.setColumnStretch(8, 1)
        datos_group.setLayout(grid_datos)
        layout.addWidget(datos_group)

        # Título precios
        lbl_precios = QLabel("PRECIOS POR TRAMO")
        lbl_precios.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_precios.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_precios)

        # Precios
        # ACTUALIZADO: orden alineado al formato oficial del Excel (NP al final)
        precios_group = QGroupBox("Precios")
        grid_precios = QGridLayout()
        self.campos_precios: Dict[str, QLineEdit] = {}
        etiquetas = ["S/A", "NAT", "BMO", "E-100", "E-200", "E-400", "BCO", "HUESO",
                     "GRIS", "CHO", "ACE", "MAD L", "MAD T", "NP"]
        mapa_db = {"S/A": "sa", "NAT": "nat", "BMO": "bmo", "E-100": "e100", "E-200": "e200", "E-400": "e400",
                   "BCO": "bco", "HUESO": "hue", "GRIS": "gris", "CHO": "cho", "ACE": "ace",
                   "MAD L": "madl", "MAD T": "madt", "NP": "np"}
        self.etiquetas_mapa = mapa_db

        col = row = 0
        for i, et in enumerate(etiquetas):
            le = NavLineEdit()
            le.setPlaceholderText("0.00")
            le.setMaxLength(12)
            v = QDoubleValidator(0.00, 9999999.99, 2)
            v.setNotation(QDoubleValidator.Notation.StandardNotation)
            le.setValidator(v)
            self.campos_precios[et] = le
            grid_precios.addWidget(QLabel(et + ":"), row, col)
            grid_precios.addWidget(le, row, col + 1)
            col += 2
            if (i + 1) % 5 == 0:
                row += 1
                col = 0
        precios_group.setLayout(grid_precios)
        layout.addWidget(precios_group)

        # === Botones CRUD principales (visibles con colores) ===
        self.botones: Dict[str, QPushButton] = {}
        self.botones["Guardar"] = QPushButton("Guardar")
        self.botones["Guardar"].setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.botones["Guardar"].setToolTip("Guardar registro (Ctrl+S)")
        self.botones["Editar"] = QPushButton("Editar")
        self.botones["Editar"].setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold;")
        self.botones["Editar"].setToolTip("Modo edición")
        self.botones["Eliminar"] = QPushButton("Eliminar")
        self.botones["Eliminar"].setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
        self.botones["Eliminar"].setToolTip("Eliminar registro (Delete)")
        self.botones["Limpiar"] = QPushButton("Limpiar")
        self.botones["Limpiar"].setStyleSheet("background-color: #6B7280; color: white; font-weight: bold;")
        self.botones["Limpiar"].setToolTip("Limpiar formulario")

        # Botones secundarios (ocultos, accesibles desde menú)
        self.botones["Refresh"] = QPushButton("Refresh")
        self.botones["Refresh"].setVisible(False)
        self.botones["Imprimir"] = QPushButton("Imprimir")
        self.botones["Imprimir"].setVisible(False)
        self.botones["Salir"] = QPushButton("Salir")
        self.botones["Salir"].setVisible(False)
        self.botones["Importar"] = QPushButton("Importar")
        self.botones["Importar"].setVisible(False)

        botones_layout = QHBoxLayout()
        for b in ["Guardar", "Editar", "Eliminar", "Limpiar"]:
            self.botones[b].setFixedHeight(35)
            botones_layout.addWidget(self.botones[b])
        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        # Reglas de foco para botones
        self.botones["Guardar"].setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # recibe foco tras NP
        for b in ("Editar", "Eliminar", "Limpiar", "Refresh", "Imprimir", "Salir", "Importar"):
            self.botones[b].setFocusPolicy(Qt.FocusPolicy.NoFocus)  # solo mouse

        # Buscar (apagado por defecto)
        buscar_layout = QHBoxLayout()
        buscar_layout.addWidget(QLabel("Buscar por clave o descripción:"))
        self.buscar_input = NavLineEdit()
        self.buscar_input.setEnabled(False)  # se enciende solo con "Editar"
        buscar_layout.addWidget(self.buscar_input)
        layout.addLayout(buscar_layout)

        # Tabla
        # ACTUALIZADO: encabezados alineados al formato oficial (NP al final)
        self.table = QTableWidget()
        self.table.setColumnCount(17)
        self.table.setHorizontalHeaderLabels([
            "CLAVE", "DESCRIPCIÓN", "LARGO",
            "S/A", "NAT", "BMO", "E-100", "E-200", "E-400",
            "BCO", "HUESO", "GRIS", "CHO", "ACE", "MAD L", "MAD T", "NP"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        self._setup_shortcuts()
        self._setup_simple_navigation()

        # Colecciones para habilitar/deshabilitar
        self._inputs_precios = [self.campos_precios[e] for e in etiquetas]
        self._inputs_all = [self.clave_input, self.descripcion_input, self.largo_input] + self._inputs_precios

    def _setup_shortcuts(self) -> None:
        def _act(seq: QKeySequence, slot):
            a = QAction(self)
            a.setShortcut(seq)
            a.triggered.connect(slot)
            self.addAction(a)

        _act(QKeySequence("Ctrl+S"), self._on_guardar)
        _act(QKeySequence("Ctrl+F"), lambda: (self.buscar_input.setFocus(), self.buscar_input.selectAll()) if self.buscar_input.isEnabled() else None)
        _act(QKeySequence("Delete"), self._modo_eliminar)
        _act(QKeySequence("Ctrl+P"), self._on_imprimir)
        _act(QKeySequence("F5"), self._on_refresh)
        _act(QKeySequence("Esc"), self._on_salir)

    def _setup_simple_navigation(self) -> None:
        """Configura el orden de tabulación simple (Enter = Tab)."""
        # ACTUALIZADO: orden alineado al formato oficial (NP al final)
        orden_precios = ["S/A", "NAT", "BMO", "E-100", "E-200", "E-400", "BCO", "HUESO",
                         "GRIS", "CHO", "ACE", "MAD L", "MAD T", "NP"]
        widgets_en_orden = [
            self.clave_input,
            self.descripcion_input,
            self.largo_input,
            *[self.campos_precios[et] for et in orden_precios],
            self.botones["Guardar"],
            self.botones["Editar"],
            self.botones["Eliminar"],
            self.botones["Limpiar"],
            self.buscar_input,
            self.table,
        ]
        for anterior, siguiente in zip(widgets_en_orden, widgets_en_orden[1:]):
            self.setTabOrder(anterior, siguiente)

    # ======= EVENT FILTER: valida duplicado en CLAVE =======
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # Solo nos interesa el campo Clave, en modo "nuevo"
        if obj is self.clave_input and self.modo == "nuevo":
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                    # Validar antes de permitir avanzar
                    clave = self.clave_input.text().strip().upper()
                    if clave:
                        try:
                            if self.db.existe_clave(clave):
                                # Ya existe → pedir acción
                                resp = QMessageBox.question(
                                    self,
                                    "Clave existente",
                                    "Clave existente. ¿Deseas editarla?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                )
                                if resp == QMessageBox.StandardButton.Yes:
                                    # Cargar y entrar a modo edición
                                    reg = self.db.obtener_por_clave(clave)
                                    if reg:
                                        self._cargar_registro_para_editar(reg)
                                    return True  # consumimos la tecla
                                else:
                                    # No → limpiar y foco en Clave
                                    self.Inicio()
                                    self.clave_input.setText("")
                                    self.clave_input.setFocus()
                                    return True  # consumimos
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"No fue posible validar la clave:\n{e}")
                            return True  # evita que avance si hubo error
        return super().eventFilter(obj, event)

    def _cargar_registro_para_editar(self, reg: Dict) -> None:
        """
        Carga los datos en pantalla y habilita modo 'editar' con Clave/Descripción apagadas,
        precios y largo editables.
        """
        self.modo = "editar"
        self.clave_en_edicion = reg.get("clave", "")

        self.buscar_input.setEnabled(True)
        self.buscar_input.clear()

        self.clave_input.setText(reg.get("clave", ""))
        self.descripcion_input.setText(reg.get("descripcion", ""))
        largo = reg.get("largo", "")
        idx = self.largo_input.findText(f"{largo} MTS.")
        self.largo_input.setCurrentIndex(max(idx, 0))

        for etiqueta, campo in self.etiquetas_mapa.items():
            val = reg.get(campo, "0.00")
            self.campos_precios[etiqueta].setText(str(val))

        # Habilitaciones: Clave/Desc apagados, Largo y Precios encendidos
        self.clave_input.setEnabled(False)
        self.descripcion_input.setEnabled(False)
        self.largo_input.setEnabled(True)
        for w in self._inputs_precios:
            w.setEnabled(True)

        # Tabla: mantenemos criterio de pantalla limpia
        self.table.clearContents()
        self.table.setRowCount(0)
        if self.statusBar():
            self.statusBar().showMessage(f"Editando {self.clave_en_edicion}", 3000)

    # ======= Conexiones =======
    def _conectar_eventos(self) -> None:
        self.botones["Guardar"].clicked.connect(self._on_guardar)
        self.botones["Editar"].clicked.connect(self._modo_editar)
        self.botones["Eliminar"].clicked.connect(self._modo_eliminar)
        self.botones["Limpiar"].clicked.connect(self.Inicio)
        self.botones["Refresh"].clicked.connect(self._on_refresh)
        self.botones["Imprimir"].clicked.connect(self._on_imprimir)
        self.botones["Salir"].clicked.connect(self._on_salir)
        self.botones["Importar"].clicked.connect(self._on_importar)
        self.buscar_input.textChanged.connect(self._buscar_dinamico)
        self.table.itemSelectionChanged.connect(self._seleccion_tabla)

    # ======= Helpers habilitación =======
    def _set_enabled_inputs(self, *, datos: bool, precios: bool) -> None:
        self.clave_input.setEnabled(datos)
        self.descripcion_input.setEnabled(datos)
        self.largo_input.setEnabled(datos)
        for w in self._inputs_precios:
            w.setEnabled(precios)

    # ======= APARTADO DE LIMPIO =======
    def Inicio(self) -> None:
        """Deja todo en blanco/limpio. Tabla vacía. Buscar apagado y limpio."""
        self.modo = "nuevo"
        self.clave_en_edicion = None

        self.buscar_input.setEnabled(False)
        self.buscar_input.clear()

        self._set_enabled_inputs(datos=True, precios=True)

        self.clave_input.clear()
        self.descripcion_input.clear()
        self.largo_input.setCurrentIndex(0)
        # ACTUALIZADO: orden alineado al formato oficial (NP al final)
        for et in ["S/A", "NAT", "BMO", "E-100", "E-200", "E-400", "BCO", "HUESO",
                   "GRIS", "CHO", "ACE", "MAD L", "MAD T", "NP"]:
            self.campos_precios[et].setText("0.00")

        self.table.clearContents()
        self.table.setRowCount(0)
        if self.statusBar():
            self.statusBar().showMessage("Pantalla limpia.", 2000)
        self.clave_input.setFocus()

    # ======= Modo editar =======
    def _modo_editar(self) -> None:
        self.modo = "editar"
        self.clave_en_edicion = None
        self.buscar_input.setEnabled(True)
        self.buscar_input.clear()
        self.buscar_input.setFocus()
        self._set_enabled_inputs(datos=False, precios=False)
        self.table.clearContents()
        self.table.setRowCount(0)
        if self.statusBar():
            self.statusBar().showMessage("Modo edición: use Buscar y seleccione un registro.", 3000)

    def _seleccion_tabla(self) -> None:
        if self.modo != "editar":
            return
        row = self.table.currentRow()
        if row < 0:
            return
        self._copiar_fila_a_campos(row)
        self._set_enabled_inputs(datos=False, precios=True)
        self.largo_input.setEnabled(True)
        self.clave_input.setEnabled(False)
        self.descripcion_input.setEnabled(False)

    def _copiar_fila_a_campos(self, row: int) -> None:
        self.clave_en_edicion = self.table.item(row, 0).text()
        self.clave_input.setText(self.clave_en_edicion)
        self.descripcion_input.setText(self.table.item(row, 1).text())
        largo_txt = self.table.item(row, 2).text()
        idx = self.largo_input.findText(f"{largo_txt} MTS.")
        self.largo_input.setCurrentIndex(max(idx, 0))
        # ACTUALIZADO: orden alineado al formato oficial (NP al final)
        columnas = ["S/A", "NAT", "BMO", "E-100", "E-200", "E-400", "BCO", "HUESO",
                    "GRIS", "CHO", "ACE", "MAD L", "MAD T", "NP"]
        for i, et in enumerate(columnas, start=3):
            item = self.table.item(row, i)
            self.campos_precios[et].setText(item.text() if item else "0.00")
        if self.statusBar():
            self.statusBar().showMessage(f"Editando {self.clave_en_edicion}", 2000)

    # ======= Guardar / Eliminar / Importar / Imprimir =======
    def _on_guardar(self) -> None:
        clave = self.clave_input.text().strip().upper()
        if not clave:
            QMessageBox.warning(self, "Validación", "Debes capturar la CLAVE.")
            return
        descripcion = self.descripcion_input.text().strip()
        if not descripcion:
            QMessageBox.warning(self, "Validación", "Debes capturar la DESCRIPCIÓN.")
            return
        try:
            largo_val = Decimal(self.largo_input.currentText().split()[0])
        except (InvalidOperation, IndexError):
            QMessageBox.warning(self, "Validación", "LARGO inválido.")
            return

        reg: Dict[str, Decimal | str] = {"clave": clave, "descripcion": descripcion, "largo": largo_val}
        for et, campo in self.etiquetas_mapa.items():
            reg[campo] = dec2(self.campos_precios[et].text())
        try:
            self.db.insertar_o_actualizar(reg, use_merge=False)  # respeta 0.00
            self.Inicio()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No fue posible guardar:\n{e}")

    def _modo_eliminar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Eliminar", "Debes seleccionar un registro.")
            return
        clave = self.table.item(row, 0).text()
        resp = QMessageBox.question(
            self, "Eliminar",
            f"¿Seguro que deseas eliminar la clave {clave}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.db.eliminar_por_clave(clave)
                self.Inicio()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    # ======= Refresh =======
    def _on_refresh(self) -> None:
        """
        Refresh no llena la tabla.
        - Solo 'refresca la base' (ping de consulta) y muestra un mensaje.
        """
        try:
            _ = self.db.listar_todos()  # ping/consulta (se descarta)
            if self.statusBar():
                self.statusBar().showMessage("Base refrescada.", 2000)
        except Exception as e:
            QMessageBox.critical(self, "Refresh", f"No fue posible refrescar la base:\n{e}")

    # ======= Importar (ACTUALIZADO) =======
    def _on_importar(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo", "", "Excel (*.xlsx);;PDF (*.pdf);;CSV (*.csv)"
        )
        if not path:
            return

        reporte = {"insertado": 0, "actualizado": 0, "sin_cambios": 0, "error": 0}
        sin_precio: List[str] = []

        try:
            if path.lower().endswith(".xlsx"):
                # Formato oficial: valida encabezados, duplicados y genera plantilla si falla.
                resultado = parse_excel_oficial(path)
                registros = resultado["registros"]
                sin_precio = resultado.get("sin_precio", [])
            elif path.lower().endswith(".pdf"):
                registros = importar_pdf_mateco(path)
            elif path.lower().endswith(".csv"):
                registros = parse_csv_generico(path)
            else:
                QMessageBox.warning(self, "Importar", "Formato no soportado.")
                return
        except FormatoExcelError as e:
            mensaje = str(e)
            ruta_plantilla = getattr(e, "ruta_plantilla", None)
            if ruta_plantilla:
                mensaje += f"\n\nPlantilla oficial generada en:\n{ruta_plantilla}"
            QMessageBox.warning(self, "Formato no válido", mensaje)
            return
        except Exception as e:
            QMessageBox.critical(self, "Importar", f"No fue posible leer el archivo:\n{e}")
            return

        for r in registros:
            try:
                self.db.insertar_o_actualizar(r, use_merge=True, reporte=reporte)
            except Exception as e:
                reporte["error"] += 1
                print("Error importando:", r.get("clave"), e)
                logger.exception("Error importando registro de aluminio con clave=%s", r.get("clave"))

        mensaje = (
            "✅ Importación completada.\n\n"
            f"Nuevos insertados: {reporte['insertado']}\n"
            f"Actualizados (precio mayor): {reporte['actualizado']}\n"
            f"Sin cambios: {reporte['sin_cambios']}\n"
            f"Errores: {reporte['error']}"
        )
        if sin_precio:
            mensaje += f"\n\nClaves con todos los precios en $0 (informativo): {len(sin_precio)}"

        QMessageBox.information(self, "Importación", mensaje)
        self.Inicio()

    def _on_imprimir(self) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("Imprimir")
        msg.setText("¿Dónde deseas imprimir?")
        btn_pantalla = msg.addButton("Pantalla", QMessageBox.ButtonRole.AcceptRole)
        btn_pdf = msg.addButton("PDF", QMessageBox.ButtonRole.AcceptRole)
        btn_impresora = msg.addButton("Impresora", QMessageBox.ButtonRole.AcceptRole)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.exec()

        if msg.clickedButton() == btn_pantalla:
            try:
                registros = ordenar_registros_asc(self.db.listar_todos())
            except Exception as e:
                QMessageBox.critical(self, "Imprimir", f"No fue posible consultar:\n{e}")
                return
            if not registros:
                QMessageBox.warning(self, "Imprimir", "No hay registros para mostrar.")
            else:
                self._llenar_tabla(registros)
            return
        elif msg.clickedButton() == btn_pdf:
            try:
                registros = ordenar_registros_asc(self.db.listar_todos())
            except Exception as e:
                QMessageBox.critical(self, "Imprimir", f"No fue posible consultar:\n{e}")
                return
            if not registros:
                QMessageBox.warning(self, "Imprimir", "No hay registros para imprimir.")
                return
            try:
                path = get_pdf_path("Aluminio", "Materiales_aluminio.pdf")
                imprimir_pdf_guardar(registros, parent=self, filename=path)
                QMessageBox.information(self, "Imprimir", f"PDF generado con éxito:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Imprimir", f"No fue posible generar PDF:\n{e}")
        elif msg.clickedButton() == btn_impresora:
            try:
                registros = ordenar_registros_asc(self.db.listar_todos())
            except Exception as e:
                QMessageBox.critical(self, "Imprimir", f"No fue posible consultar:\n{e}")
                return
            if not registros:
                QMessageBox.warning(self, "Imprimir", "No hay registros para imprimir.")
                return
            try:
                import win32print, win32api
                printer_name = win32print.GetDefaultPrinter()
                if not printer_name or "PDF" in printer_name.upper():
                    QMessageBox.warning(self, "Impresora", "⚠️ No hay impresora conectada.")
                    self.Inicio()
                    return
                temp_pdf = os.path.join(os.getenv("TEMP") or ".", "materiales_aluminio_tmp.pdf")
                imprimir_pdf_guardar(registros, parent=None, filename=temp_pdf)
                win32api.ShellExecute(0, "print", temp_pdf, None, ".", 0)
                QMessageBox.information(self, "Imprimir", "✅ PDF enviado a la impresora.")
            except ImportError:
                QMessageBox.warning(self, "Impresora", "⚠️ No hay soporte de impresión en este sistema.")
                self.Inicio()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No fue posible imprimir en impresora:\n{e}")
                self.Inicio()

    def _on_salir(self) -> None:
        self.close()

    # ======= Buscar y tabla =======
    def _buscar_dinamico(self) -> None:
        if not self.buscar_input.isEnabled():
            return
        texto = self.buscar_input.text().strip().upper()
        try:
            regs = self.db.listar_todos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No fue posible consultar la base:\n{e}")
            return
        if texto:
            regs = [r for r in regs if texto in r.get("clave", "").upper() or texto in r.get("descripcion", "").upper()]
        self._llenar_tabla(regs)

    def _llenar_tabla(self, registros: List[Dict]) -> None:
        self.table.setRowCount(0)
        for r in ordenar_registros_asc(registros):
            row = self.table.rowCount()
            self.table.insertRow(row)
            valores = [r.get("clave", ""), r.get("descripcion", ""), str(r.get("largo", ""))] \
                      + [str(r.get(c, "0.00")) for c in CAMPOS_PRECIO_BD]
            for col, val in enumerate(valores):
                item = QTableWidgetItem(val)
                if col >= 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)


if __name__ == "__main__":
    vah_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.isdir(vah_root) and vah_root not in sys.path:
        sys.path.insert(0, vah_root)
    app = QApplication(sys.argv)
    win = PantallaMaterialesAluminio()
    win.show()
    sys.exit(app.exec())