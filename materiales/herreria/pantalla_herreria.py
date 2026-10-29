# D:\vah\materiales\herreria\pantalla_herreria.py
# -*- coding: utf-8 -*-
r"""
Pantalla Herrería (PyQt6)

Ajustes solicitados:
- Resaltar visualmente el campo con foco (borde azul).
- Avance con TAB **y Enter**; retroceso con **Shift+Tab**.
- Los botones se operan exclusivamente con mouse (sin foco por teclado),
  excepto "Guardar" al final del orden de tabulación.
- Se mantiene el resto del comportamiento (Inicio limpio, Editar/Eliminar,
  Refresh que limpia, impresión, etc.).
"""

import os, sys
from decimal import Decimal
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QGroupBox, QFileDialog,
    QAbstractItemView, QGridLayout, QSizePolicy, QStatusBar
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QIcon, QDoubleValidator, QAction, QKeySequence

# Para `python -m materiales.herreria.pantalla_herreria`
PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from common.app_paths import get_resource_path
from common.estilos import QSS_BASE
from common.focus_simple import NavLineEdit as NavLineEditSimple, NavComboBox as NavComboBoxSimple
from common.pdf_utils import get_pdf_path
from common.manuales import abrir_manual_pdf
from materiales.herreria.db_manager import DBManager
from materiales.herreria.imprimir import imprimir_pdf_guardar
from materiales.herreria.utils import dec2


class PantallaHerreria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VAH — Módulo Herrería")

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
        act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("Herrería", "operativo", self))
        menu_ayuda.addAction(act_manual_operativo)

        act_manual_tecnico = QAction("Manual Tecnico", self)
        act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("Herrería", "tecnico", self))
        menu_ayuda.addAction(act_manual_tecnico)

        for icon_name in ("logo.jpg", "logo.png", "logo_00001.ico"):
            logo_path = get_resource_path(icon_name)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break

        # Geometría controlada por el HUB (se aplica en showEvent)
        self._geom_applied = False
        self._workspace_rect: Optional[QRect] = self._read_workspace_env()

        # DB y estado
        self.db = DBManager()  # server y bd por defecto (herreria)
        self.modo = "nuevo"
        self.clave_en_edicion: str | None = None

        # UI
        self._estilos()
        self._ui()
        self._conectar()
        self._setup_shortcuts()
        self._setup_simple_navigation()
        self.Inicio()

    # ---------- geometría desde HUB ----------
    def _read_workspace_env(self) -> Optional[QRect]:
        """Lee VAH_CHILD_X/Y/W/H y devuelve un QRect válido o None si faltan."""
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
        """Aplica el área del HUB en el primer 'show'; si no hay, maximiza."""
        super().showEvent(e)
        if not self._geom_applied:
            if self._workspace_rect is not None:
                self.setGeometry(self._workspace_rect)
            else:
                self.showMaximized()
            self._geom_applied = True

    # ---------- estilos ----------
    def _estilos(self):
        # Sin box-shadow (Qt no lo soporta); usamos borde azul para foco.
        self.setStyleSheet(QSS_BASE + """
            QWidget { background-color: #D9E0E7; font-family: Segoe UI; font-size: 10pt; }
            QGroupBox { border: 1px solid #cfd8e3; border-radius: 6px; margin-top: 10px; font-size: 9pt; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;
                               padding: 0 6px; margin-left: 8px; color: #374151; }
            QLineEdit {
                background: #ffffff; border: 1px solid #cfd8e3; padding: 4px 6px; border-radius: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #2563EB; outline: none;
            }
            QPushButton { background-color: #ffffff; border: 1px solid #cfd8e3; padding: 6px 12px; border-radius: 6px; }
            QPushButton:hover { background-color: #e6eefc; }
            QHeaderView::section { background-color: #1f6feb; color: white; font-weight: bold; border: none; }
        """)

    # ---------- UI ----------
    def _ui(self):
        central = QWidget(); self.setCentralWidget(central)
        layout = QVBoxLayout(); central.setLayout(layout)

        # status bar explícita
        if not self.statusBar():
            self.setStatusBar(QStatusBar())

        gb = QGroupBox("Datos del material"); grid = QGridLayout()

        self.clave_input = NavLineEditSimple(); self.clave_input.setMaxLength(20)
        self.descripcion_input = NavLineEditSimple(); self.descripcion_input.setMaxLength(100)
        self.kg_input = NavLineEditSimple(); self.kg_input.setPlaceholderText("0.00")
        val = QDoubleValidator(0.00, 9999999.99, 2); val.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.kg_input.setValidator(val); self.kg_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        # tamaños
        self.clave_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed); self.clave_input.setFixedWidth(160)
        self.kg_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed); self.kg_input.setFixedWidth(110)
        self.descripcion_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        grid.addWidget(QLabel("Clave:"), 0, 0); grid.addWidget(self.clave_input, 0, 1)
        grid.addWidget(QLabel("Descripción:"), 0, 2); grid.addWidget(self.descripcion_input, 0, 3, 1, 5)
        grid.addWidget(QLabel("Kilogramos:"), 0, 8); grid.addWidget(self.kg_input, 0, 9)

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

        botones_layout = QHBoxLayout()
        for b in ["Guardar", "Editar", "Eliminar", "Limpiar"]:
            self.botones[b].setFixedHeight(35)
            botones_layout.addWidget(self.botones[b])
        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        # Reglas de foco para botones
        self.botones["Guardar"].setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for b in ("Editar","Eliminar","Limpiar","Refresh","Imprimir","Salir","Importar"):
            self.botones[b].setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # buscar (solo clave)
        hb = QHBoxLayout()
        hb.addWidget(QLabel("Buscar por clave:"))
        self.buscar_input = NavLineEditSimple()
        self.buscar_input.setEnabled(False)  # deshabilitado en Inicio
        hb.addWidget(self.buscar_input)
        layout.addLayout(hb)

        # tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["CLAVE","DESCRIPCIÓN","KILOGRAMOS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def _conectar(self):
        self.botones["Guardar"].clicked.connect(self._on_guardar)
        self.botones["Editar"].clicked.connect(self._modo_editar)
        self.botones["Eliminar"].clicked.connect(self._modo_eliminar)
        self.botones["Limpiar"].clicked.connect(self.Inicio)
        self.botones["Refresh"].clicked.connect(self._on_refresh)
        self.botones["Imprimir"].clicked.connect(self._on_imprimir)
        self.botones["Salir"].clicked.connect(self.close)

        self.buscar_input.textChanged.connect(self._buscar_dinamico)
        self.table.itemDoubleClicked.connect(self._editar_desde_tabla)

        # Ya no usamos returnPressed -> guardar; Enter ahora navega (NavLineEdit)

    # ---------- atajos ----------
    def _setup_shortcuts(self):
        def _act(seq: str, slot):
            a = QAction(self); a.setShortcut(QKeySequence(seq)); a.triggered.connect(slot); self.addAction(a)
        _act("Ctrl+S", self._on_guardar)
        _act("Ctrl+F", lambda: (self.buscar_input.setEnabled(True), self.buscar_input.setFocus(), self.buscar_input.selectAll()))
        _act("Delete", self._modo_eliminar)
        _act("Ctrl+P", self._on_imprimir)
        _act("F5", self._on_refresh)
        _act("Esc", self.close)

    def _setup_simple_navigation(self) -> None:
        """Configura el orden de tabulación simple (Enter = Tab)."""
        widgets_en_orden = [
            self.clave_input,
            self.descripcion_input,
            self.kg_input,
            self.botones["Guardar"],
            self.botones["Editar"],
            self.botones["Eliminar"],
            self.botones["Limpiar"],
            self.buscar_input,
            self.table,
        ]
        for anterior, siguiente in zip(widgets_en_orden, widgets_en_orden[1:]):
            self.setTabOrder(anterior, siguiente)

    # ---------- flujo ----------
    def Inicio(self):
        self.modo = "nuevo"
        self.clave_en_edicion = None
        self.clave_input.clear(); self.descripcion_input.clear(); self.kg_input.clear()
        self.buscar_input.clear(); self.buscar_input.setEnabled(False)
        self.table.clearContents(); self.table.setRowCount(0)
        self.clave_input.setFocus()
        self.statusBar().showMessage("Pantalla en estado inicial.", 3000)

    def _llenar_tabla(self, registros: List[Dict]):
        ordenados = sorted(registros, key=lambda r: (r.get("clave","") or "").upper())
        self.table.setRowCount(0)
        for r in ordenados:
            row = self.table.rowCount(); self.table.insertRow(row)
            clave = str(r.get("clave","") or "")
            desc  = str(r.get("descripcion","") or "")
            try:
                kg = f"{dec2(r.get('kilogramos','0.00')):.2f}"
            except Exception:
                kg = "0.00"
            for col,val in enumerate([clave, desc, kg]):
                it = QTableWidgetItem(val)
                if col == 2:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, it)

    # ---------- acciones ----------
    def _on_guardar(self):
        clave = self.clave_input.text().strip()
        if not clave:
            QMessageBox.warning(self,"Validación","Debe capturar la clave."); return
        descripcion = self.descripcion_input.text().strip()
        if not descripcion:
            QMessageBox.warning(self,"Validación","Debe capturar la descripción."); return
        try:
            kg = dec2(self.kg_input.text())
        except Exception:
            QMessageBox.warning(self,"Validación","Kilogramos inválido."); return
        if kg <= Decimal("0.00"):
            QMessageBox.warning(self,"Validación","Debe capturar un valor mayor a 0."); return

        reg = {"clave": clave, "descripcion": descripcion, "kilogramos": kg}

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
        # tabla vacía; coincidencias aparecerán al escribir
        self.table.clearContents(); self.table.setRowCount(0)
        self.buscar_input.setFocus()
        self.statusBar().showMessage("Modo edición. Escribe prefijo de clave para ver coincidencias.", 4000)

    def _editar_desde_tabla(self):
        row = self.table.currentRow()
        if row >= 0:
            self.clave_en_edicion = self.table.item(row,0).text()
            self.clave_input.setText(self.clave_en_edicion)
            self.descripcion_input.setText(self.table.item(row,1).text())
            self.kg_input.setText(self.table.item(row,2).text())
            self.statusBar().showMessage(f"Editando {self.clave_en_edicion}", 3000)

    def _modo_eliminar(self):
        if self.modo != "eliminar":
            self.modo = "eliminar"
            self.buscar_input.setEnabled(True)
            self.buscar_input.clear()
            self.table.clearContents(); self.table.setRowCount(0)
            self.buscar_input.setFocus()
            self.statusBar().showMessage(
                "Modo eliminar. Escribe prefijo de clave, selecciona una fila y vuelve a presionar Eliminar.",
                6000
            )
            return

        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self,"Eliminar","Selecciona un registro y vuelve a presionar Eliminar."); return
        clave = self.table.item(row,0).text()
        resp = QMessageBox.question(
            self,"Eliminar",f"¿Seguro que deseas eliminar {clave}?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.db.eliminar_por_clave(clave)
                QMessageBox.information(self,"Eliminar","Registro eliminado.")
                self.Inicio()
            except Exception as e:
                QMessageBox.critical(self,"Error",f"No se pudo eliminar:\n{e}")

    def _on_refresh(self):
        # Mantener criterio de este módulo: limpiar pantalla
        self.Inicio()
        self.statusBar().showMessage("Pantalla refrescada (limpia).", 3000)

    def _on_imprimir(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Imprimir")
        msg.setText("¿Dónde deseas imprimir?")
        btn_pantalla  = msg.addButton("Pantalla",  QMessageBox.ButtonRole.AcceptRole)
        btn_pdf       = msg.addButton("PDF",       QMessageBox.ButtonRole.AcceptRole)
        btn_impresora = msg.addButton("Impresora", QMessageBox.ButtonRole.AcceptRole)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.exec()

        try:
            registros = self.db.listar_todos()
        except Exception as e:
            QMessageBox.critical(self,"Error",f"No fue posible recuperar datos:\n{e}")
            self.Inicio(); return
        if not registros:
            QMessageBox.warning(self,"Imprimir","No hay registros para imprimir.")
            self.Inicio(); return

        registros = sorted(registros, key=lambda r: (r.get("clave","") or "").upper())

        if msg.clickedButton() == btn_pantalla:
            self._llenar_tabla(registros)
            return

        if msg.clickedButton() == btn_pdf:
            try:
                path = get_pdf_path("Herreria", "Materiales herreria.pdf")
                imprimir_pdf_guardar(
                    registros, parent=self, filename=path,
                    title="Materiales herrería (kg)", page_size="LETTER",
                    orientation="portrait", repeat_header=True,
                    footer_pattern="Pagina {page}",
                )
                QMessageBox.information(self, "Imprimir", f"PDF generado con éxito:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No fue posible generar el PDF:\n{e}")
            self.Inicio(); return

        if msg.clickedButton() == btn_impresora:
            try:
                try:
                    import win32print, win32api
                except ImportError:
                    QMessageBox.warning(self,"Impresora","No hay Impresora conectada")
                    self.Inicio(); return
                printer = win32print.GetDefaultPrinter()
                if not printer or "PDF" in printer.upper():
                    QMessageBox.warning(self,"Impresora","No hay Impresora conectada")
                    self.Inicio(); return
                import tempfile
                tmp = os.path.join(tempfile.gettempdir(), "herreria_tmp.pdf")
                imprimir_pdf_guardar(
                    registros, parent=None, filename=tmp,
                    title="Materiales herrería (kg)", page_size="LETTER",
                    orientation="portrait", repeat_header=True,
                    footer_pattern="Pagina {page}",
                )
                win32api.ShellExecute(0, "print", tmp, None, ".", 0)
                QMessageBox.information(self,"Imprimir","Documento enviado a la impresora.")
            except Exception as e:
                QMessageBox.critical(self,"Error",f"No fue posible imprimir:\n{e}")
            self.Inicio()

    def _on_salir(self):
        """Cerrar la ventana."""
        self.close()

    def _on_importar(self):
        """Importar archivo (placeholder)."""
        QMessageBox.information(self, "Importar", "Función de importación no implementada aún.")

    # ---------- búsqueda ----------
    def _buscar_dinamico(self):
        """Filtra SOLO por clave que **empieza con** el texto (prefijo)."""
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


# --- main ---
if __name__ == "__main__":
    # Si se ejecuta directo por ruta, añadimos la raiz real del proyecto al sys.path.
    vah_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.isdir(vah_root) and vah_root not in sys.path:
        sys.path.insert(0, vah_root)

    app = QApplication(sys.argv)
    win = PantallaHerreria()
    win.show(); win.raise_(); win.activateWindow()
    sys.exit(app.exec())
