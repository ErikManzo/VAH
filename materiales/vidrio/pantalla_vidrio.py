# D:\vah\materiales\vidrio\pantalla_vidrio.py
# -*- coding: utf-8 -*-
r"""
Pantalla Vidrio (PyQt6)

Ajustes:
- Foco marcado; Enter/Tab avanzan, Shift+Tab retrocede.
- Botones solo mouse (excepto Guardar).
- Tabla en blanco al iniciar/limpiar; Buscar solo en Editar.
- Refresh NO llena tabla (solo ping BD).
- **Eliminar** elimina por la clave que esté en los **inputs** (no requiere tabla).
- **Compatibilidad DB**: se agrega _db_get_por_clave() que intenta varios nombres de
  método en DBManager (obtener_por_clave / get_por_clave / buscar_por_clave / select_por_clave)
  y si ninguno existe, hace un fallback con listar_todos().
"""

import os, sys
from decimal import Decimal
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QGroupBox, QFileDialog,
    QAbstractItemView, QGridLayout, QSizePolicy, QStatusBar, QComboBox
)
from PyQt6.QtCore import Qt, QRect, QObject, QEvent
from PyQt6.QtGui import QIcon, QDoubleValidator, QAction, QKeySequence

PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from common.app_paths import get_resource_path
from common.estilos import QSS_BASE
from common.focus_utils import setup_form_navigation
from common.pdf_utils import get_pdf_path
from common.manuales import abrir_manual_pdf
from materiales.vidrio.db_manager import DBManager
from materiales.vidrio.imprimir import imprimir_pdf_guardar
from materiales.vidrio.utils import dec2


class UpperLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        pos = self.cursorPosition()
        self.setText((self.text() or "").upper())
        self.setCursorPosition(pos)


class NavLineEdit(UpperLineEdit):
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextPrevChild(True)
            return
        super().keyPressEvent(event)


class PantallaVidrio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VAH — Módulo Vidrio")

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
        act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf(self.windowTitle().split("—")[-1].strip(), "operativo", self))
        menu_ayuda.addAction(act_manual_operativo)

        act_manual_tecnico = QAction("Manual Tecnico", self)
        act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf(self.windowTitle().split("—")[-1].strip(), "tecnico", self))
        menu_ayuda.addAction(act_manual_tecnico)

        for icon_name in ("logo.jpg", "logo.png", "logo_00001.ico"):
            logo_path = get_resource_path(icon_name)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break

        self._geom_applied = False
        self._workspace_rect: Optional[QRect] = self._read_workspace_env()

        self.db = DBManager()
        self.modo = "nuevo"     # "nuevo" | "editar"
        self.clave_en_edicion: str | None = None

        self._estilos()
        self._ui()
        self._conectar()
        self._setup_shortcuts()
        self._build_tab_order()
        self.Inicio()

        # Duplicidad al salir de CLAVE
        self.clave_input.installEventFilter(self)

    # ---------- util DB ----------
    def _db_get_por_clave(self, clave: str) -> Optional[Dict]:
        """Obtiene un registro por clave, probando varios nombres de método.
        Si no existen, hace fallback con listar_todos().
        """
        clave = (clave or "").strip()
        if not clave:
            return None
        # 1) Intenta métodos directos si existen
        for nombre in ("obtener_por_clave", "get_por_clave", "buscar_por_clave", "select_por_clave"):
            fn = getattr(self.db, nombre, None)
            if callable(fn):
                try:
                    return fn(clave)
                except Exception:
                    pass
        # 2) Fallback: listar y filtrar
        try:
            for r in self.db.listar_todos():
                if (r.get("clave","") or "").strip().upper() == clave.upper():
                    return r
        except Exception:
            pass
        return None

    # ---------- geom ----------
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

    def showEvent(self, e):
        super().showEvent(e)
        if not self._geom_applied:
            if self._workspace_rect is not None:
                self.setGeometry(self._workspace_rect)
            else:
                self.showMaximized()
            self._geom_applied = True

    # ---------- estilos ----------
    def _estilos(self):
        self.setStyleSheet(QSS_BASE + """
            QWidget { background-color: #D9E0E7; font-family: Segoe UI; font-size: 10pt; }
            QGroupBox { border: 1px solid #cfd8e3; border-radius: 6px; margin-top: 10px; font-size: 9pt; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;
                               padding: 0 6px; margin-left: 8px; color: #374151; }
            QLineEdit, QComboBox {
                background: #ffffff; border: 1px solid #cfd8e3; padding: 4px 6px; border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #2563EB; outline: none; }
            QPushButton { background-color: #ffffff; border: 1px solid #cfd8e3; padding: 6px 12px; border-radius: 6px; }
            QPushButton:hover { background-color: #e6eefc; }
            QHeaderView::section { background-color: #1f6feb; color: white; font-weight: bold; border: none; }
            QTableWidget { background: #ffffff; border: 1px solid #cfd8e3; }
        """)

    # ---------- UI ----------
    def _ui(self):
        central = QWidget(); self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        if not self.statusBar():
            self.setStatusBar(QStatusBar())

        gb = QGroupBox("Datos del Vidrio"); grid = QGridLayout()

        self.clave_input = NavLineEdit(); self.clave_input.setMaxLength(20)
        self.descripcion_input = NavLineEdit(); self.descripcion_input.setMaxLength(100)
        self.precio_input = NavLineEdit(); self.precio_input.setPlaceholderText("0.00")
        val = QDoubleValidator(0.00, 9999999.99, 2); val.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.precio_input.setValidator(val); self.precio_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.clave_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed); self.clave_input.setFixedWidth(160)
        self.precio_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed); self.precio_input.setFixedWidth(110)
        self.descripcion_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        grid.addWidget(QLabel("Clave:"), 0, 0); grid.addWidget(self.clave_input, 0, 1)
        grid.addWidget(QLabel("Descripción:"), 0, 2); grid.addWidget(self.descripcion_input, 0, 3, 1, 5)
        grid.addWidget(QLabel("Precio:"), 0, 8); grid.addWidget(self.precio_input, 0, 9)

        for c in (3,4,5,6,7): grid.setColumnStretch(c, 1)
        grid.setColumnMinimumWidth(1, 160); grid.setColumnMinimumWidth(9, 110)

        gb.setLayout(grid); layout.addWidget(gb)

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

        # Layout con solo botones visibles
        botones_layout = QHBoxLayout()
        for b in ["Guardar", "Editar", "Eliminar", "Limpiar"]:
            self.botones[b].setFixedHeight(35)
            botones_layout.addWidget(self.botones[b])
        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        # Reglas de foco para botones
        self.botones["Guardar"].setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for b in ("Editar", "Eliminar", "Limpiar", "Refresh", "Imprimir", "Salir", "Importar"):
            self.botones[b].setFocusPolicy(Qt.FocusPolicy.NoFocus)

        hb = QHBoxLayout()
        hb.addWidget(QLabel("Buscar por clave:"))
        self.buscar_input = NavLineEdit(); self.buscar_input.setEnabled(False)
        hb.addWidget(self.buscar_input)
        layout.addLayout(hb)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["CLAVE","DESCRIPCIÓN","PRECIO"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

    def _conectar(self):
        self.botones["Guardar"].clicked.connect(self._on_guardar)
        self.botones["Editar"].clicked.connect(self._modo_editar)
        self.botones["Eliminar"].clicked.connect(self._on_eliminar_directo)
        self.botones["Limpiar"].clicked.connect(self.Inicio)
        self.botones["Refresh"].clicked.connect(self._on_refresh)
        self.botones["Imprimir"].clicked.connect(self._on_imprimir)
        self.botones["Salir"].clicked.connect(self.close)

        self.buscar_input.textChanged.connect(self._buscar_dinamico)
        self.table.itemDoubleClicked.connect(self._editar_desde_tabla)
        self.table.itemSelectionChanged.connect(self._cargar_desde_seleccion)

    # ---------- atajos ----------
    def _setup_shortcuts(self):
        def _act(seq: str, slot):
            a = QAction(self); a.setShortcut(QKeySequence(seq)); a.triggered.connect(slot); self.addAction(a)
        _act("Ctrl+S", self._on_guardar)
        _act("Ctrl+F", lambda: (self.buscar_input.setEnabled(True), self.buscar_input.setFocus(), self.buscar_input.selectAll()))
        _act("Delete", self._on_eliminar_directo)  # Delete borra el registro cargado
        _act("Ctrl+P", self._on_imprimir)
        _act("F5", self._on_refresh)
        _act("Esc", self.close)

    def _build_tab_order(self):
        self.botones["Guardar"].setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._focus_navigation = setup_form_navigation(
            self,
            tab_widgets=[
                self.clave_input,
                self.descripcion_input,
                self.precio_input,
                self.botones["Guardar"],
                self.buscar_input,
                self.table,
            ],
            enter_widgets=[
                self.descripcion_input,
                self.precio_input,
            ],
            submit_callback=self.botones["Guardar"].click,
        )
        self._setup_search_keys()

    # ---------- Duplicado CLAVE al salir con Enter/Tab ----------
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self.clave_input and self.modo == "nuevo":
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                    clave = self.clave_input.text().strip().upper()
                    if clave:
                        try:
                            if self.db.existe_clave(clave):
                                resp = QMessageBox.question(
                                    self, "Clave existente",
                                    "Clave existente. ¿Deseas editarla?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                )
                                if resp == QMessageBox.StandardButton.Yes:
                                    reg = self._db_get_por_clave(clave)
                                    if reg:
                                        self._cargar_para_editar(reg)
                                    return True
                                else:
                                    self.Inicio()
                                    self.clave_input.clear(); self.clave_input.setFocus()
                                    return True
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"No fue posible validar la clave:\n{e}")
                            return True
        return super().eventFilter(obj, event)

    # ---------- Flujo ----------
    def Inicio(self):
        self.modo = "nuevo"
        self.clave_en_edicion = None
        self.clave_input.setEnabled(True); self.descripcion_input.setEnabled(True)
        self.precio_input.setEnabled(True)

        self.clave_input.clear(); self.descripcion_input.clear(); self.precio_input.clear()
        self.buscar_input.clear(); self.buscar_input.setEnabled(False)
        self.table.clearContents(); self.table.setRowCount(0)
        self.clave_input.setFocus()
        self.statusBar().showMessage("Pantalla en estado inicial.", 3000)

    def _cargar_para_editar(self, reg: Dict):
        self.modo = "editar"
        self.clave_en_edicion = reg.get("clave", "")
        self.buscar_input.setEnabled(True); self.buscar_input.clear()

        self.clave_input.setText(reg.get("clave",""))
        self.descripcion_input.setText(reg.get("descripcion",""))
        self.precio_input.setText(f"{dec2(reg.get('precio','0.00')):.2f}")

        self.clave_input.setEnabled(False)
        self.descripcion_input.setEnabled(True)
        self.precio_input.setEnabled(True)

        self.table.clearContents(); self.table.setRowCount(0)
        self.statusBar().showMessage(f"Editando {self.clave_en_edicion}", 3000)

        # Llevar el foco al campo Clave para comenzar la edición
        self.clave_input.setFocus()
        self.clave_input.selectAll()

    # --- carga desde la tabla ---
    def _cargar_desde_seleccion(self):
        row = self.table.currentRow()
        if row < 0:
            return
        reg = {
            "clave": self.table.item(row,0).text(),
            "descripcion": self.table.item(row,1).text(),
            "precio": self.table.item(row,2).text(),
        }
        self._cargar_para_editar(reg)

    def _llenar_tabla(self, registros: List[Dict]):
        ordenados = sorted(registros, key=lambda r: (r.get("clave","") or "").upper())
        self.table.setRowCount(0)
        for r in ordenados:
            row = self.table.rowCount(); self.table.insertRow(row)
            clave = str(r.get("clave","") or "")
            desc  = str(r.get("descripcion","") or "")
            try:
                precio = f"{dec2(r.get('precio','0.00')):.2f}"
            except Exception:
                precio = "0.00"
            for col,val in enumerate([clave, desc, precio]):
                item = QTableWidgetItem(val)
                if col == 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

    # ---------- Acciones ----------
    def _on_guardar(self):
        clave = self.clave_input.text().strip().upper()
        if not clave:
            QMessageBox.warning(self,"Validación","Debe capturar la clave."); return
        descripcion = self.descripcion_input.text().strip()
        if not descripcion:
            QMessageBox.warning(self,"Validación","Debe capturar la descripción."); return
        try:
            precio = dec2(self.precio_input.text())
        except Exception:
            QMessageBox.warning(self,"Validación","Precio inválido."); return
        if precio <= Decimal("0.00"):
            QMessageBox.warning(self,"Validación","Debe capturar un precio mayor a 0."); return

        reg = {"clave": clave, "descripcion": descripcion, "precio": precio}

        try:
            if self.modo == "editar":
                if self.clave_en_edicion is None:
                    QMessageBox.warning(self,"Editar","No hay registro seleccionado para editar."); return
                if clave != self.clave_en_edicion and self.db.existe_clave(clave):
                    QMessageBox.warning(self,"Duplicidad",f"La clave '{clave}' ya existe."); return
                self.db.actualizar_por_clave(self.clave_en_edicion, reg)
                QMessageBox.information(self,"Editar","Registro actualizado con éxito")
                self.Inicio(); return

            if self.db.existe_clave(clave):
                QMessageBox.warning(self,"Duplicidad",f"La clave '{clave}' ya está registrada."); return

            self.db.insertar(reg)
            QMessageBox.information(self,"Guardar","Información guardada con éxito")
            self.Inicio()
        except Exception as e:
            QMessageBox.critical(self,"Error",f"No fue posible guardar:\n{e}")

    def _modo_editar(self):
        self.modo = "editar"
        self.clave_en_edicion = None
        self.buscar_input.setEnabled(True)
        self.buscar_input.clear()
        self.table.clearContents(); self.table.setRowCount(0)
        self.buscar_input.setFocus()
        self.statusBar().showMessage("Modo edición. Escribe prefijo de clave para ver coincidencias.", 4000)

    def _editar_desde_tabla(self):
        self._cargar_desde_seleccion()

    def _on_eliminar_directo(self):
        """Elimina el registro cargado en los inputs (no requiere tabla)."""
        clave_actual = (self.clave_input.text() or "").strip().upper()
        if not clave_actual:
            QMessageBox.warning(self, "Eliminar",
                                "Primero escribe/selecciona una clave y cárgala en los campos.")
            return
        try:
            if not self.db.existe_clave(clave_actual):
                QMessageBox.warning(self, "Eliminar", f"La clave '{clave_actual}' no existe en base de datos.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Eliminar", f"No fue posible validar la clave:\n{e}")
            return

        resp = QMessageBox.question(
            self, "Eliminar",
            f"¿Seguro que deseas eliminar la clave {clave_actual}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.db.eliminar_por_clave(clave_actual)
                QMessageBox.information(self, "Eliminar", "Registro eliminado.")
                self.Inicio()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    def _on_refresh(self):
        try:
            _ = self.db.listar_todos()
            self.statusBar().showMessage("Base refrescada.", 2000)
        except Exception as e:
            QMessageBox.critical(self, "Refresh", f"No fue posible refrescar la base:\n{e}")

    def _on_imprimir(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Imprimir")
        msg.setText("¿Dónde deseas imprimir?")
        btn_pantalla = msg.addButton("Pantalla", QMessageBox.ButtonRole.AcceptRole)
        btn_pdf = msg.addButton("PDF", QMessageBox.ButtonRole.AcceptRole)
        btn_impresora = msg.addButton("Impresora", QMessageBox.ButtonRole.AcceptRole)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.exec()

        try:
            registros = self.db.listar_todos()
        except Exception as e:
            QMessageBox.critical(self,"Error",f"No fue posible recuperar datos:\n{e}")
            return
        if not registros:
            QMessageBox.warning(self,"Imprimir","No hay registros para imprimir.")
            return

        registros = sorted(registros, key=lambda r: (r.get("clave","") or "").upper())

        if msg.clickedButton() == btn_pantalla:
            self._llenar_tabla(registros)
            return

        if msg.clickedButton() == btn_pdf:
            try:
                path = get_pdf_path("Vidrio", "Materiales vidrio.pdf")
                imprimir_pdf_guardar(
                    registros, parent=self, filename=path,
                    title="Materiales vidrio", page_size="LETTER",
                    orientation="portrait", repeat_header=True,
                    footer_pattern="Pagina {page}",
                )
                QMessageBox.information(self, "Imprimir", f"PDF generado con éxito:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No fue posible generar el PDF:\n{e}")
            return

        if msg.clickedButton() == btn_impresora:
            try:
                try:
                    import win32print, win32api
                except ImportError:
                    QMessageBox.warning(self,"Impresora","No hay Impresora conectada"); return
                printer = win32print.GetDefaultPrinter()
                if not printer or "PDF" in printer.upper():
                    QMessageBox.warning(self,"Impresora","No hay Impresora conectada"); return
                import tempfile
                tmp = os.path.join(tempfile.gettempdir(), "vidrio_tmp.pdf")
                imprimir_pdf_guardar(
                    registros, parent=None, filename=tmp,
                    title="Materiales vidrio", page_size="LETTER",
                    orientation="portrait", repeat_header=True,
                    footer_pattern="Pagina {page}",
                )
                win32api.ShellExecute(0, "print", tmp, None, ".", 0)
                QMessageBox.information(self,"Imprimir","Documento enviado a la impresora.")
            except Exception as e:
                QMessageBox.critical(self,"Error",f"No fue posible imprimir:\n{e}")

    def _buscar_dinamico(self):
        if not self.buscar_input.isEnabled():
            return
        pref = (self.buscar_input.text() or "").strip().upper()
        try:
            regs = self.db.listar_todos()
            if pref:
                regs = [r for r in regs if (r.get("clave","") or "").upper().startswith(pref)]
            self._llenar_tabla(regs)
        except Exception as e:
            QMessageBox.critical(self,"Error",f"No fue posible buscar:\n{e}")

    def _on_salir(self):
        """Cerrar la ventana."""
        self.close()

    def _on_importar(self):
        """Importar archivo (placeholder)."""
        QMessageBox.information(self, "Importar", "Función de importación no implementada aún.")

    def _setup_search_keys(self) -> None:
        """Configura filtros de teclado para la búsqueda."""
        outer = self
        
        class _SearchBoxFilter(QObject):
            def eventFilter(self, obj, ev):
                if obj is outer.buscar_input and ev.type() == QEvent.Type.KeyPress and outer.modo == "editar":
                    key = ev.key()
                    rc = outer.table.rowCount()
                    if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                        if rc > 0:
                            curr = outer.table.currentRow()
                            if curr < 0:
                                curr = 0
                            else:
                                curr = max(0, min(rc - 1, curr + (1 if key == Qt.Key.Key_Down else -1)))
                            outer.table.setCurrentCell(curr, 0)
                            outer.table.setFocus()
                            return True
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        if rc > 0:
                            row = outer.table.currentRow()
                            if row < 0:
                                row = 0
                                outer.table.setCurrentCell(row, 0)
                            outer._cargar_desde_tabla()
                            return True
                return False
        
        class _TableEnterFilter(QObject):
            def eventFilter(self, obj, ev):
                if obj is outer.table and ev.type() == QEvent.Type.KeyPress and outer.modo == "editar":
                    if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        row = outer.table.currentRow()
                        if row >= 0:
                            outer._cargar_desde_tabla()
                            return True
                return False
        
        self._search_filter = _SearchBoxFilter(self)
        self._table_filter = _TableEnterFilter(self)
        self.buscar_input.installEventFilter(self._search_filter)
        self.table.installEventFilter(self._table_filter)


if __name__ == "__main__":
    vah_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.isdir(vah_root) and vah_root not in sys.path:
        sys.path.insert(0, vah_root)

    app = QApplication(sys.argv)
    win = PantallaVidrio()
    win.show(); win.raise_(); win.activateWindow()
    sys.exit(app.exec())
