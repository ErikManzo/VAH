# -*- coding: utf-8 -*-
from __future__ import annotations
import sys, os, traceback
import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Dict, Optional, Tuple

if TYPE_CHECKING:
    import pyodbc

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.estilos import QSS_BASE
from common.focus_simple import NavLineEdit as NavLineEditSimple
from common.focus_utils import apply_tab_order, install_select_all_on_focus
from common.search_utils import (
    configure_two_column_completer,
    create_key_description_model,
    get_key_description_from_index,
    populate_key_description_model,
)
from common.app_paths import get_resource_path
from common.logger_config import get_logger
from common.manuales import abrir_manual_pdf

logger = get_logger('paquetes.herrajes.pantalla')


# ===================== Función auxiliar local =====================
def _abrir_materiales_herrajes(parent=None) -> bool:
    """Abre el catálogo de materiales de herrajes sin depender de presupuestos."""
    import subprocess
    try:
        script_path = os.path.join(PROJECT_ROOT, "materiales", "herrajes", "pantalla_herrajes.py")
        if os.path.isfile(script_path):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            subprocess.Popen(
                [sys.executable, script_path],
                cwd=PROJECT_ROOT,
                shell=False,
                creationflags=0x08000000,
                startupinfo=startupinfo
            )
            return True
        return False
    except Exception:
        return False


# ===================== BD =====================
try:
    import pyodbc
except ImportError:
    pyodbc = None

# ===================== Qt =====================
from PyQt6.QtCore import Qt, QEvent, QModelIndex
from PyQt6.QtGui import QIcon, QIntValidator, QStandardItemModel, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QMessageBox, QHeaderView,
    QAbstractItemView, QFileDialog, QSizePolicy, QDialog, QDialogButtonBox,
    QComboBox, QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QTableView
)

try:
    from paquetes.herrajes.imprimir import imprimir as imprimir_paquetes
    _IMPRIMIR_IMPORT_ERROR = None
except ImportError as _e:
    imprimir_paquetes = None
    _IMPRIMIR_IMPORT_ERROR = traceback.format_exc()


# ===================== DB LAYER =====================
@dataclass
class ConnInfo:
    server: str = os.environ.get("VAH_DB_SERVER", r"DESKTOP-AE60PIU\SQLEXPRESS")
    database: str = os.environ.get("VAH_DB_DATABASE", "herrajes")


class DBManager:
    def __init__(self, server: Optional[str] = None, database: Optional[str] = None):
        ci = ConnInfo()
        self.server = server or ci.server
        self.database = database or ci.database
        self._cn: Optional["pyodbc.Connection"] = None

    def cn(self):
        if pyodbc is None:
            raise RuntimeError("pyodbc no está disponible.")
        if self._cn is not None:
            return self._cn
        raw_drivers = list(pyodbc.drivers())
        drivers: List[str] = []
        if "ODBC Driver 18 for SQL Server" in raw_drivers:
            drivers.append("ODBC Driver 18 for SQL Server")
        if "ODBC Driver 17 for SQL Server" in raw_drivers:
            drivers.append("ODBC Driver 17 for SQL Server")
        for d in raw_drivers:
            if ("SQL Server" in d) and (d not in drivers):
                drivers.append(d)
        if not drivers:
            raise RuntimeError("No se encontró un driver ODBC de SQL Server (17/18).")
        server_input = (self.server or "").strip()
        variants: List[str] = []
        if server_input:
            variants.append(server_input)
        if "\\" in server_input:
            host, inst = server_input.split("\\", 1)
            variants.extend([host + "\\" + inst, "localhost\\" + inst, "127.0.0.1\\" + inst])
        else:
            host = server_input or "localhost"
            variants.extend([host, "localhost", "127.0.0.1", host + ",1433", "localhost,1433", "127.0.0.1,1433"])
        seen = set()
        server_variants: List[str] = []
        for v in variants:
            if v and v not in seen:
                seen.add(v)
                server_variants.append(v)
        last_error: Optional[Exception] = None
        tried: List[str] = []
        for drv in drivers:
            for srv in server_variants:
                parts = ["DRIVER={" + drv + "}", "SERVER=" + srv, "DATABASE=" + (self.database or ""), "Trusted_Connection=yes"]
                if "ODBC Driver 18" in drv:
                    parts.append("Encrypt=yes")
                    # VAH_TRUST_SERVER_CERTIFICATE: "yes" para desarrollo, "no" para producción (default)
                    trust_cert = os.environ.get("VAH_TRUST_SERVER_CERTIFICATE", "no").strip().lower()
                    if trust_cert in ("1", "yes", "true"):
                        parts.append("TrustServerCertificate=yes")
                    else:
                        parts.append("TrustServerCertificate=no")
                conn_str = ";".join(parts) + ";"
                try:
                    # VAH_DB_TIMEOUT: timeout en segundos (default: 30)
                    db_timeout = int(os.environ.get("VAH_DB_TIMEOUT", "30"))
                    self._cn = pyodbc.connect(conn_str, autocommit=False, timeout=db_timeout)
                    return self._cn
                except Exception as e:
                    last_error = e
                    tried.append("[" + drv + "] SERVER=" + srv)
                    continue
        detail = "\n".join(tried[:30])
        raise RuntimeError("No fue posible abrir conexión a SQL Server.\n" + detail + "\nÚltimo error: " + str(last_error))

    def materiales_buscar(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_herraje ORDER BY Clave"
            params: List[str] = []
        else:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_herraje WHERE UPPER(Clave) LIKE ? OR UPPER(Descripcion) LIKE ? ORDER BY Clave"
            like = "%" + q + "%"
            params = [like, like]
        with self.cn().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": r[0] or "", "descripcion": r[1] or ""} for r in rows]

    def paquete_existe(self, clave_paquete: str) -> bool:
        with self.cn().cursor() as c:
            r = c.execute("SELECT 1 FROM paquetes_herrajes WHERE clave=?", clave_paquete).fetchone()
        return bool(r)

    def paquetes_listar(self) -> List[Dict]:
        with self.cn().cursor() as c:
            rows = c.execute("SELECT clave, descripcion FROM paquetes_herrajes ORDER BY clave").fetchall()
        return [{"clave": r[0] or "", "descripcion": r[1] or ""} for r in rows]

    def paquetes_y_items(self) -> List[Dict]:
        with self.cn().cursor() as cur:
            rows = cur.execute("SELECT p.clave, p.descripcion, i.clv_herraje, m.Descripcion, i.cantidad FROM paquetes_herrajes p LEFT JOIN paquete_herraje_items i ON i.clave_paquete = p.clave LEFT JOIN materiales_herraje m ON m.Clave = i.clv_herraje ORDER BY p.clave ASC, i.clv_herraje ASC").fetchall()
        paquetes: Dict[str, Dict] = {}
        for r in rows:
            pclave, pdesc, hclave, hdesc, cant = r
            if pclave not in paquetes:
                paquetes[pclave] = {"clave": pclave, "descripcion": pdesc, "items": []}
            if hclave is not None:
                paquetes[pclave]["items"].append({"clave": hclave or "", "descripcion": hdesc or "", "cantidad": int(cant or 0)})
        return [paquetes[k] for k in sorted(paquetes.keys())]

    def paquete_cargar(self, clave_paquete: str) -> Tuple[Optional[Dict], List[Dict]]:
        with self.cn().cursor() as c:
            h = c.execute("SELECT clave, descripcion FROM paquetes_herrajes WHERE clave=?", clave_paquete).fetchone()
            if not h:
                return None, []
            d = {"clave": h[0], "descripcion": h[1]}
            rows = c.execute("SELECT i.clv_herraje, m.Descripcion, i.cantidad FROM paquete_herraje_items i LEFT JOIN materiales_herraje m ON m.Clave = i.clv_herraje WHERE i.clave_paquete=? ORDER BY i.clv_herraje", clave_paquete).fetchall()
        items = [{"clave": r[0] or "", "descripcion": r[1] or "", "cantidad": int(r[2] or 0)} for r in rows]
        return d, items

    def paquete_guardar(self, header: Dict, items: List[Dict]):
        if not header.get("clave"):
            raise ValueError("Falta clave del paquete")
        if not header.get("descripcion"):
            raise ValueError("Falta descripción del paquete")
        if not items:
            raise ValueError("Debe agregar al menos un herraje al paquete")
        cn = self.cn()
        try:
            with cn.cursor() as c:
                if self.paquete_existe(header["clave"]):
                    c.execute("UPDATE paquetes_herrajes SET descripcion=? WHERE clave=?", header["descripcion"], header["clave"])
                    c.execute("DELETE FROM paquete_herraje_items WHERE clave_paquete=?", header["clave"])
                else:
                    c.execute("INSERT INTO paquetes_herrajes(clave, descripcion) VALUES (?,?)", header["clave"], header["descripcion"])
                for it in items:
                    c.execute("INSERT INTO paquete_herraje_items(clave_paquete, clv_herraje, cantidad) VALUES (?,?,?)", header["clave"], it["clave"], int(it["cantidad"]))
            cn.commit()
        except Exception:
            cn.rollback()
            raise

    def paquete_eliminar(self, clave_paquete: str):
        cn = self.cn()
        with cn.cursor() as c:
            c.execute("DELETE FROM paquete_herraje_items WHERE clave_paquete=?", clave_paquete)
            c.execute("DELETE FROM paquetes_herrajes WHERE clave=?", clave_paquete)
            cn.commit()


# ===================== UI =====================
class PaqueteHerrajesUI(QMainWindow):
    def __init__(self, server: Optional[str] = None, database: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("VAH – Paquete de herrajes")

        # === Menú Archivo ===
        menu_archivo = self.menuBar().addMenu("&Archivo")
        act_refresh = QAction("Refresh (F5)", self)
        act_refresh.triggered.connect(self.Inicio)
        menu_archivo.addAction(act_refresh)
        act_imprimir = QAction("Imprimir (Ctrl+P)", self)
        act_imprimir.triggered.connect(self.on_imprimir)
        menu_archivo.addAction(act_imprimir)
        menu_archivo.addSeparator()
        act_salir = QAction("Salir (Esc)", self)
        act_salir.triggered.connect(self._on_salir)
        menu_archivo.addAction(act_salir)

        # Catálogo de herrajes
        menu_archivo.addSeparator()
        act_herraje = QAction("Catálogo de Herrajes", self)
        act_herraje.triggered.connect(self.on_herraje)
        menu_archivo.addAction(act_herraje)

        # === Menú Ayuda ===
        menu_ayuda = self.menuBar().addMenu("&Ayuda")
        act_manual_operativo = QAction("Manual Operativo", self)
        act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("Paquete_Herrajes", "operativo", self))
        menu_ayuda.addAction(act_manual_operativo)
        act_manual_tecnico = QAction("Manual Técnico", self)
        act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("Paquete_Herrajes", "tecnico", self))
        menu_ayuda.addAction(act_manual_tecnico)

        # Buscar logo para el ícono de la ventana
        logo_candidates = [
            ("logo.jpg",),
            ("logo.png",),
            ("logo_00001.ico",),
            ("principal", "pantalla_principal.ico"),
        ]
        for relative_path in logo_candidates:
            logo_path = get_resource_path(*relative_path)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break

        self._first_show = True
        self.db = DBManager(server=server, database=database)
        self.items: List[Dict] = []
        self.modo = "nuevo"
        self.edit_row_idx: Optional[int] = None
        self._lookup_clave: Dict[str, str] = {}
        self._lookup_desc: Dict[str, str] = {}
        self._estilos()
        self._build()
        self._wire()
        self.Inicio()

    def showEvent(self, e):
        super().showEvent(e)
        if self._first_show:
            self._first_show = False
            self.showMaximized()

    def _estilos(self):
        self.setStyleSheet(QSS_BASE + """
            QWidget { background-color:#D9E0E7; font-family: Segoe UI; font-size:10pt; }
            QGroupBox { border:1px solid #888; margin-top:10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 6px; }
            QLineEdit { background:white; border:1px solid gray; padding:5px; border-radius:4px; }
            QLineEdit:focus { border:2px solid #2563EB; outline: none; }
            QPushButton { background:#f2f2f2; border:1px solid #bbb; padding:6px 12px; border-radius:6px; }
            QPushButton:hover { background:#cce0ff; }
            QHeaderView::section { background:#0078D7; color:white; font-weight:bold; }
        """)

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout()
        central.setLayout(root)

        gb_hdr = QGroupBox("Datos del Paquete")
        g = QGridLayout()
        gb_hdr.setLayout(g)
        self.paquete_clave = NavLineEditSimple()
        self.paquete_clave.setMaxLength(20)
        self.paquete_desc = NavLineEditSimple()
        self.paquete_desc.setMaxLength(100)
        self.paquete_clave.setFixedWidth(160)
        self.paquete_desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        g.addWidget(QLabel("Clave:"), 0, 0)
        g.addWidget(self.paquete_clave, 0, 1)
        g.addWidget(QLabel("Descripción:"), 0, 2)
        g.addWidget(self.paquete_desc, 0, 3, 1, 5)
        root.addWidget(gb_hdr)

        gb_it = QGroupBox("Agregar herrajes al paquete")
        gi = QGridLayout()
        gb_it.setLayout(gi)
        self.it_clave = NavLineEditSimple()
        self.it_clave.setMaxLength(20)
        self.it_desc = NavLineEditSimple()
        self.it_desc.setMaxLength(100)
        self.it_cant = NavLineEditSimple()
        self.it_cant.setValidator(QIntValidator(1, 1_000_000))
        self.it_cant.setPlaceholderText("1")
        self.it_clave.setFixedWidth(160)
        self.it_desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.it_cant.setFixedWidth(120)
        gi.addWidget(QLabel("Clave Herraje:"), 0, 0)
        gi.addWidget(self.it_clave, 0, 1)
        gi.addWidget(QLabel("Descripción Herraje:"), 0, 2)
        gi.addWidget(self.it_desc, 0, 3, 1, 4)
        gi.addWidget(QLabel("Cantidad:"), 0, 7)
        gi.addWidget(self.it_cant, 0, 8)
        root.addWidget(gb_it)

        self.model_clave = create_key_description_model(self)
        self.model_desc = create_key_description_model(self)
        self.comp_clave = configure_two_column_completer(self.model_clave, display_column=0, parent=self)
        self.it_clave.setCompleter(self.comp_clave)
        self.comp_desc = configure_two_column_completer(self.model_desc, display_column=1, parent=self)
        self.it_desc.setCompleter(self.comp_desc)

        # Configurar ancho del popup del autocompletado
        for comp in [self.comp_clave, self.comp_desc]:
            popup = comp.popup()
            if isinstance(popup, QTableView):
                popup.setMinimumWidth(500)
                popup.setColumnWidth(0, 150)
                popup.setColumnWidth(1, 320)
                popup.horizontalHeader().setStretchLastSection(True)

        # === Botones CRUD principales ===
        self.botones: Dict[str, QPushButton] = {}
        self.botones["Guardar"] = QPushButton("Guardar")
        self.botones["Guardar"].setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.botones["Guardar"].setToolTip("Guardar registro (Ctrl+S)")
        self.botones["Agregar"] = QPushButton("Agregar")
        self.botones["Agregar"].setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold;")
        self.botones["Agregar"].setToolTip("Agregar herraje al paquete")
        self.botones["Editar"] = QPushButton("Editar")
        self.botones["Editar"].setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold;")
        self.botones["Editar"].setToolTip("Modo edición")
        self.botones["Eliminar"] = QPushButton("Eliminar")
        self.botones["Eliminar"].setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
        self.botones["Eliminar"].setToolTip("Eliminar paquete")
        self.botones["Limpiar"] = QPushButton("Limpiar")
        self.botones["Limpiar"].setStyleSheet("background-color: #6B7280; color: white; font-weight: bold;")
        self.botones["Limpiar"].setToolTip("Limpiar formulario")

        # Botones secundarios (ocultos)
        self.botones["Refresh"] = QPushButton("Refresh")
        self.botones["Refresh"].setVisible(False)
        self.botones["Imprimir"] = QPushButton("Imprimir")
        self.botones["Imprimir"].setVisible(False)
        self.botones["Salir"] = QPushButton("Salir")
        self.botones["Salir"].setVisible(False)

        # Botones específicos
        self.botones["QuitarItem"] = QPushButton("Quitar item")
        self.botones["QuitarItem"].setStyleSheet("background-color: #8B5CF6; color: white; font-weight: bold;")
        self.botones["QuitarItem"].setToolTip("Quitar herraje seleccionado de la tabla")

        # Layout con botones visibles
        bar = QHBoxLayout()
        root.addLayout(bar)
        for b in ["Guardar", "Agregar", "Editar", "Eliminar", "Limpiar", "QuitarItem"]:
            self.botones[b].setFixedHeight(36)
            bar.addWidget(self.botones[b])
        bar.addStretch()

        # Reglas de foco para botones
        self.botones["Guardar"].setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.botones["Agregar"].setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for b in ("Editar", "Eliminar", "Limpiar", "Refresh", "Imprimir", "Salir", "QuitarItem"):
            self.botones[b].setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["CLAVE HERRAJE", "DESCRIPCIÓN", "CANTIDAD"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        root.addWidget(self.tbl)

        apply_tab_order(self, [self.paquete_clave, self.paquete_desc, self.it_clave, self.it_desc, self.it_cant, self.botones["Agregar"], self.botones["Guardar"]])
        self._focus_selection = install_select_all_on_focus(self, [self.paquete_clave, self.paquete_desc, self.it_clave, self.it_desc, self.it_cant])

    def _wire(self):
        self.botones["Guardar"].clicked.connect(self.on_guardar)
        self.botones["Agregar"].clicked.connect(self._agregar_item)
        self.botones["Editar"].clicked.connect(self.on_editar)
        self.botones["Eliminar"].clicked.connect(self.on_eliminar)
        self.botones["Limpiar"].clicked.connect(self.Inicio)
        self.botones["Refresh"].clicked.connect(self.Inicio)
        self.botones["Imprimir"].clicked.connect(self.on_imprimir)
        self.botones["QuitarItem"].clicked.connect(self.on_quitar_item)
        self.botones["Salir"].clicked.connect(self.close)
        self.it_clave.textEdited.connect(self._buscar_popup)
        self.it_desc.textEdited.connect(self._buscar_popup)
        self.comp_clave.activated[QModelIndex].connect(self._on_clave_activada)
        self.comp_desc.activated[QModelIndex].connect(self._on_desc_activada)
        self.it_cant.returnPressed.connect(self._agregar_item)
        self.tbl.itemSelectionChanged.connect(self._on_tbl_select)
        self.tbl.customContextMenuRequested.connect(self._menu_tbl)
        self.tbl.installEventFilter(self)
        self.paquete_clave.returnPressed.connect(self._check_clave_paquete_unique)
        self.botones["Agregar"].installEventFilter(self)
        self.botones["Guardar"].installEventFilter(self)

    def Inicio(self):
        self.modo = "nuevo"
        self.edit_row_idx = None
        self.items.clear()
        for w in (self.paquete_clave, self.paquete_desc, self.it_clave, self.it_desc, self.it_cant):
            w.clear()
        self._refrescar_tabla_items()
        self.tbl.clearSelection()
        self.statusBar().showMessage("Pantalla en estado inicial.", 7000)
        self.paquete_clave.setFocus()

    def eventFilter(self, obj, event):
        if obj is self.tbl and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.on_quitar_item()
                return True
        if obj in (self.botones["Agregar"], self.botones["Guardar"]) and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                obj.click()
                return True
        return super().eventFilter(obj, event)

    def _menu_tbl(self, pos):
        row = self.tbl.currentRow()
        m = QMenu(self)
        act_quitar = m.addAction("Quitar item")
        act = m.exec(self.tbl.viewport().mapToGlobal(pos))
        if act == act_quitar and row >= 0:
            self.on_quitar_item()

    def _buscar_popup(self):
        sender = self.sender()
        if not isinstance(sender, QLineEdit):
            return
        texto = sender.text()

        # OPCIÓN C: Si el usuario edita la clave, limpiar la descripción automáticamente
        if sender is self.it_clave and texto:
            self.it_desc.clear()

        try:
            if sender is self.it_desc:
                rows = self.db.materiales_buscar(texto, por="descripcion")
                self._fill_model(self.model_desc, rows, lookup="desc")
                self.comp_desc.complete()
            else:
                rows = self.db.materiales_buscar(texto, por="clave")
                self._fill_model(self.model_clave, rows, lookup="clave")
                self.comp_clave.complete()
        except Exception as e:
            self.statusBar().showMessage("No se pudo consultar materiales: " + str(e), 4000)

    def _fill_model(self, model: QStandardItemModel, rows: List[Dict], lookup: str):
        populate_key_description_model(model, rows)
        if lookup == "clave":
            self._lookup_clave = {}
        else:
            self._lookup_desc = {}
        for r in rows:
            clave = r.get("clave", "")
            desc = r.get("descripcion", "")
            if lookup == "clave":
                self._lookup_clave[clave] = desc
            else:
                self._lookup_desc[desc] = clave

    def _on_clave_activada(self, index):
        """Manejador cuando se selecciona un ítem del autocompletado por clave."""
        if not index.isValid():
            return
        proxy_model = self.comp_clave.completionModel()
        source_index = proxy_model.mapToSource(index)
        clave = str(source_index.siblingAtColumn(0).data() or "").strip()
        desc = str(source_index.siblingAtColumn(1).data() or "").strip()
        if not clave:
            return
        self.it_clave.setText(clave)
        if desc:
            self.it_desc.setText(desc)
        self.it_cant.setFocus()
        self.it_cant.selectAll()

    def _on_desc_activada(self, index):
        """Manejador cuando se selecciona un ítem del autocompletado por descripción."""
        if not index.isValid():
            return
        proxy_model = self.comp_desc.completionModel()
        source_index = proxy_model.mapToSource(index)
        clave = str(source_index.siblingAtColumn(0).data() or "").strip()
        desc = str(source_index.siblingAtColumn(1).data() or "").strip()
        if not desc:
            return
        self.it_desc.setText(desc)
        if clave:
            self.it_clave.setText(clave)
        self.it_cant.setFocus()
        self.it_cant.selectAll()

    def _on_tbl_select(self):
        """Manejador cuando se selecciona un ítem de la tabla para edición."""
        row = self.tbl.currentRow()
        if row < 0:
            self.edit_row_idx = None
            self.statusBar().showMessage("Modo edición desactivado.", 2000)
            return
        # Obtener la clave desde la celda de la tabla (no asumir que el índice coincide)
        clave_item = self.tbl.item(row, 0)
        if clave_item is None:
            self.edit_row_idx = None
            return
        clave_seleccionada = clave_item.text().strip().upper()
        # Buscar el item en self.items por clave (no por índice)
        for idx, it in enumerate(self.items):
            if it.get("clave", "").upper() == clave_seleccionada:
                self.it_clave.setText(it.get("clave", ""))
                self.it_desc.setText(it.get("descripcion", ""))
                self.it_cant.setText(str(it.get("cantidad", 1)))
                self.edit_row_idx = idx
                self.it_cant.setFocus()
                self.it_cant.selectAll()
                # Indicador visual claro de modo edición
                self.statusBar().showMessage(
                    f"EDITANDO: {clave_seleccionada} - Modifique y presione 'Agregar' para actualizar", 
                    5000
                )
                return
        self.edit_row_idx = None

    def _procesar_item(self, clave: str, desc: str, cant_txt: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Procesa un item para agregarlo al paquete.
        Retorna: (exito, clave_resuelta, cantidad_final_si_se_acumulo)
        cantidad_final es None si se agregó como nuevo item, o el valor acumulado si ya existía.
        """
        clave = (clave or "").strip().upper()
        desc = (desc or "").strip()
        # Resolver clave desde descripción si es necesario
        if not clave and desc and desc in self._lookup_desc:
            clave = (self._lookup_desc.get(desc, "") or "").strip().upper()
        # Resolver descripción desde clave si es necesario
        if not desc and clave and clave in self._lookup_clave:
            desc = self._lookup_clave.get(clave, "")
        # Validar clave
        if not clave:
            return False, None, None
        # Validar cantidad
        try:
            cant = int(cant_txt or "1")
        except Exception:
            return False, None, None
        if cant <= 0:
            return False, None, None
        # Acumular si ya existe o agregar nuevo
        for it in self.items:
            if it["clave"] == clave:
                it["cantidad"] += cant
                self._refrescar_tabla_items()
                self.statusBar().showMessage(
                    f"Cantidad actualizada: {clave} → Nueva cantidad: {it['cantidad']}",
                    4000
                )
                return True, clave, it["cantidad"]
        # No existía, agregar nuevo
        self.items.append({"clave": clave, "descripcion": desc, "cantidad": cant})
        self._refrescar_tabla_items()
        self.statusBar().showMessage(f"Herraje {clave} agregado al paquete.", 3000)
        return True, clave, None

    def _agregar_item(self):
        """Agrega o actualiza un herraje en el paquete."""
        clave = self.it_clave.text().strip().upper()
        desc = self.it_desc.text().strip()
        cant_txt = self.it_cant.text().strip() or "1"

        # Si estamos en modo edición, SUSTITUIR el ítem (no acumular)
        if self.edit_row_idx is not None and 0 <= self.edit_row_idx < len(self.items):
            # Validaciones básicas
            if not clave:
                QMessageBox.warning(self, "Validación", "Captura la Clave del herraje.")
                return
            try:
                cant = int(cant_txt)
            except Exception:
                QMessageBox.warning(self, "Validación", "Cantidad inválida.")
                return
            if cant <= 0:
                QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor a 0.")
                return
            
            # Resolver descripción desde clave si es necesario
            if not desc and clave and clave in self._lookup_clave:
                desc = self._lookup_clave.get(clave, "")
            
            # Verificar que la clave no haya cambiado a una que ya existe
            clave_original = self.items[self.edit_row_idx]["clave"]
            if clave != clave_original:
                for i, it in enumerate(self.items):
                    if i != self.edit_row_idx and it["clave"] == clave:
                        QMessageBox.warning(self, "Validación", 
                            f"Ya existe un ítem con la clave '{clave}'. "
                            f"Use 'Quitar item' para eliminar el duplicado.")
                        return
            
            # SUSTITUIR el ítem editado
            self.items[self.edit_row_idx] = {"clave": clave, "descripcion": desc, "cantidad": cant}
            edited_key = clave
            self.edit_row_idx = None
            self._refrescar_tabla_items()
            
            # Seleccionar la fila editada
            for r in range(self.tbl.rowCount()):
                if self.tbl.item(r, 0).text() == edited_key:
                    self.tbl.selectRow(r)
                    break
            
            self.statusBar().showMessage("✓ Ítem actualizado correctamente.", 3000)
            self.it_clave.clear()
            self.it_desc.clear()
            self.it_cant.clear()
            self.it_cant.setText("1")
            self.it_clave.setFocus()
            return

        # Si no estamos editando, verificar si la clave ya existe para acumular
        exito, clave_resuelta, cant_acumulada = self._procesar_item(clave, desc, cant_txt)
        if not exito:
            QMessageBox.warning(self, "Validación", "Captura la Clave del herraje.")
            return

        self.tbl.clearSelection()
        self.edit_row_idx = None

        # OPCIÓN C: Mantener clave y descripción visibles, limpiar solo cantidad
        # y poner foco en cantidad para permitir acumulación rápida
        self.it_cant.clear()
        self.it_cant.setText("1")
        self.it_cant.setFocus()
        self.it_cant.selectAll()

    def on_quitar_item(self):
        row = self.tbl.currentRow()
        if row < 0 or row >= len(self.items):
            QMessageBox.warning(self, "Quitar item", "Selecciona un renglón de la tabla.")
            return
        it = self.items[row]
        resp = QMessageBox.question(self, "Quitar item", f"¿Eliminar el herraje '{it.get('clave', '')}' del paquete?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        del self.items[row]
        self._refrescar_tabla_items()
        self.edit_row_idx = None
        self.it_clave.clear()
        self.it_desc.clear()
        self.it_cant.clear()
        self.it_cant.setText("1")
        self.statusBar().showMessage("Ítem eliminado.", 3000)

    def _refrescar_tabla_items(self):
        self.tbl.setRowCount(0)
        for it in sorted(self.items, key=lambda r: r["clave"]):
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            self.tbl.setItem(row, 0, QTableWidgetItem(it["clave"]))
            self.tbl.setItem(row, 1, QTableWidgetItem(it.get("descripcion", "")))
            self.tbl.setItem(row, 2, QTableWidgetItem(str(it["cantidad"])))
        self.tbl.clearSelection()
        self.edit_row_idx = None

    def _check_clave_paquete_unique(self):
        clave = self.paquete_clave.text().strip().upper()
        if not clave or self.modo != "nuevo":
            return
        try:
            if self.db.paquete_existe(clave):
                QMessageBox.warning(self, "¡Clave existente!", "Ya existe un paquete con la clave " + clave + ".")
                self.statusBar().showMessage("Clave duplicada: " + clave, 5000)
                self.paquete_clave.setFocus()
                self.paquete_clave.selectAll()
        except Exception as e:
            QMessageBox.critical(self, "Error de conexión", f"No se pudo validar la clave del paquete:\n{e}")

    def on_imprimir(self):
        if imprimir_paquetes is None:
            msg = "No se pudo cargar el motor interno de impresion/PDF del modulo.\n\nVerifica que el ejecutable se haya compilado con sus dependencias.\n"
            if _IMPRIMIR_IMPORT_ERROR:
                msg += "\nDetalle de importación:\n" + _IMPRIMIR_IMPORT_ERROR.splitlines()[-1]
            QMessageBox.critical(self, "Imprimir", msg)
            return
        try:
            imprimir_paquetes(self, self.db)
        except Exception as e:
            QMessageBox.critical(self, "Imprimir", f"Ocurrió un error al imprimir:\n{e}")

    def on_herraje(self):
        try:
            if _abrir_materiales_herrajes(self):
                self.statusBar().showMessage("Abriendo pantalla de herrajes...", 3000)
                return
            QMessageBox.warning(self, "Herraje", "No se pudo abrir el modulo de materiales de herrajes.")
        except Exception as e:
            QMessageBox.critical(self, "Herraje", f"No fue posible abrir la pantalla de herrajes:\n{e}")

    def on_editar(self):
        try:
            dlg = PaquetePicker(self.db, self)
        except Exception as e:
            QMessageBox.critical(self, "Editar", "No fue posible obtener el listado de paquetes:\n" + str(e))
            return
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        clave = dlg.selected_clave()
        if not clave:
            return
        try:
            hdr, items = self.db.paquete_cargar(clave)
        except Exception as e:
            QMessageBox.critical(self, "Error", "No fue posible cargar el paquete:\n" + str(e))
            return
        if not hdr:
            QMessageBox.warning(self, "Editar", "No existe el paquete " + clave + ".")
            return
        self.modo = "editar"
        self.paquete_clave.setText(hdr["clave"])
        self.paquete_desc.setText(hdr["descripcion"])
        self.items = list(items)
        self._refrescar_tabla_items()
        self.tbl.clearSelection()
        self.edit_row_idx = None
        self.statusBar().showMessage("Editando paquete " + clave, 4000)

    def _append_pending_if_any(self):
        clave = (self.it_clave.text() or "").strip().upper()
        desc = (self.it_desc.text() or "").strip()
        cant_txt = (self.it_cant.text() or "").strip() or "1"
        if not (clave or desc):
            return
        # Usar el método centralizado para procesar el item
        self._procesar_item(clave, desc, cant_txt)

    def on_guardar(self):
        self._append_pending_if_any()
        hdr_clave = self.paquete_clave.text().strip().upper()
        hdr_desc = self.paquete_desc.text().strip()
        if not hdr_clave:
            QMessageBox.warning(self, "Validación", "Debes capturar la CLAVE del paquete.")
            return
        if not hdr_desc:
            QMessageBox.warning(self, "Validación", "Debes capturar la DESCRIPCIÓN del paquete.")
            return
        if not self.items:
            QMessageBox.warning(self, "Validación", "Agrega al menos un herraje al paquete.")
            return
        if self.modo == "nuevo":
            try:
                if self.db.paquete_existe(hdr_clave):
                    resp = QMessageBox.question(self, "Duplicado", "Ya existe un paquete con la clave " + hdr_clave + ". ¿Deseas sobrescribirlo?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if resp != QMessageBox.StandardButton.Yes:
                        return
            except Exception as e:
                self.statusBar().showMessage("No se pudo verificar duplicidad: " + str(e), 4000)
        try:
            self.db.paquete_guardar({"clave": hdr_clave, "descripcion": hdr_desc}, self.items)
            QMessageBox.information(self, "Guardar", "Paquete guardado con éxito.")
            self.Inicio()
        except Exception as e:
            QMessageBox.critical(self, "Error", "No fue posible guardar el paquete:\n" + str(e))

    def on_eliminar(self):
        try:
            dlg = PaquetePicker(self.db, self)
        except Exception as e:
            QMessageBox.critical(self, "Eliminar", "No fue posible obtener el listado de paquetes:\n" + str(e))
            return
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        clave = dlg.selected_clave()
        if not clave:
            return
        resp = QMessageBox.question(self, "Eliminar", f"¿Seguro que deseas eliminar el paquete '{clave}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.paquete_eliminar(clave)
            QMessageBox.information(self, "Eliminar", "Paquete eliminado.")
            self.Inicio()
        except Exception as e:
            QMessageBox.critical(self, "Error", "No fue posible eliminar el paquete:\n" + str(e))

    def _on_salir(self):
        self.close()


class PaquetePicker(QDialog):
    def __init__(self, db: DBManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Seleccionar paquete")
        self.resize(720, 420)
        lay = QVBoxLayout(self)
        self.tbl = QTableWidget(0, 2, self)
        self.tbl.setHorizontalHeaderLabels(["CLAVE", "DESCRIPCIÓN"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay.addWidget(self.tbl)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Seleccionar")
        lay.addWidget(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self._btn_ok = btns.button(QDialogButtonBox.StandardButton.Ok)
        self._btn_ok.setEnabled(False)
        self.tbl.selectionModel().selectionChanged.connect(lambda *args: self._btn_ok.setEnabled(self.tbl.currentRow() >= 0))
        self._cargar()

    def _cargar(self):
        rows = self.db.paquetes_listar()
        self.tbl.setRowCount(0)
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(r.get("clave", "")))
            self.tbl.setItem(i, 1, QTableWidgetItem(r.get("descripcion", "")))

    def selected_clave(self) -> str:
        i = self.tbl.currentRow()
        if i < 0:
            return ""
        return self.tbl.item(i, 0).text().strip().upper()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--server", default=os.environ.get("VAH_DB_SERVER", r"DESKTOP-AE60PIU\SQLEXPRESS"))
    p.add_argument("--database", default=os.environ.get("VAH_DB_DATABASE", "herrajes"))
    return p.parse_args()


def main():
    args = parse_args()
    app = QApplication(sys.argv)
    win = PaqueteHerrajesUI(server=args.server, database=args.database)
    win.show()
    win.raise_()
    win.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()