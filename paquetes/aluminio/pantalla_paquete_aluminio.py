# -*- coding: utf-8 -*-
r"""
VAH – Paquete de aluminio
Ruta: D:\vah\paquetes\aluminio\paquete_aluminio.py
Notas:
Todos los botones ejecutan su acción con Enter (además de mouse).
Enter en campos sigue navegando; no dispara acciones.
Ajustes HUB: lee VAH_CHILD_X/Y/W/H y usa esa geometría; si faltan -> maximiza.
Atajos: Ctrl+S (Guardar), Ctrl+E (Editar), Delete (Quitar), Ctrl+P (Imprimir), F5 (Refresh), Esc (Salir).
Cambios realizados:
Eliminado "Herrería" y "Vidrio" del ComboBox de tipos
Eliminado todo el código relacionado con estos tipos (búsquedas, validaciones, navegación)
Actualizados los mapeos de tipos y las condiciones que los involucraban
Mantenido todo lo demás intacto
"""
from __future__ import annotations
import sys, os, argparse, traceback
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------- BD -----------------
try:
    import pyodbc
except Exception:
    pyodbc = None

# ----------------- Qt -----------------
from PyQt6.QtCore import Qt, QEvent, QRect, QModelIndex
from PyQt6.QtGui import (
    QIcon, QIntValidator, QStandardItemModel,
    QAction, QKeySequence
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSizePolicy, QDialog,
    QDialogButtonBox, QComboBox, QMenu, QStatusBar, QTableView
)
from common.estilos import QSS_BASE
from common.focus_utils import apply_tab_order, install_auto_popup_on_focus, install_select_all_on_focus
from common.search_utils import (
    configure_two_column_completer,
    create_key_description_model,
    get_key_description_from_index,
    populate_key_description_model,
)
from common.app_paths import get_resource_path
from common.logger_config import get_logger
from common.manuales import abrir_manual_pdf
from presupuestos.integrations.external_launchers import (
    abrir_materiales_aluminio,
    abrir_materiales_herrajes,
    abrir_materiales_otros,
    abrir_materiales_plasticos,
    abrir_paquetes_herrajes_con_args,
)
try:
    from paquetes.aluminio.imprimir import imprimir as imprimir_paquetes
    _IMPRIMIR_IMPORT_ERROR = None
except Exception:
    imprimir_paquetes = None
    _IMPRIMIR_IMPORT_ERROR = traceback.format_exc()
logger = get_logger("paquetes.aluminio.pantalla")

# =========================================
# CAPA DE DATOS
# =========================================
@dataclass
class ConnInfo:
    server: str = r"DESKTOP-AE60PUN\SQLEXPRESS"
    db_al: str = "aluminio"
    db_hr: str = "herrajes"
    db_he: str = "herreria"
    db_vi: str = "vidrio"
    db_pl: str = "plasticos"
    db_ot: str = "otros"

class DB:
    """Conexiones y operaciones para todos los almacenes."""
    def __init__(self, server: Optional[str] = None,
                 db_al: Optional[str] = None, db_hr: Optional[str] = None,
                 db_he: Optional[str] = None, db_vi: Optional[str] = None,
                 db_pl: Optional[str] = None, db_ot: Optional[str] = None):
        ci = ConnInfo()
        self.server = server or ci.server
        self.db_al = db_al or ci.db_al
        self.db_hr = db_hr or ci.db_hr
        self.db_he = db_he or ci.db_he
        self.db_vi = db_vi or ci.db_vi
        self.db_pl = db_pl or ci.db_pl
        self.db_ot = db_ot or ci.db_ot
        self._cn_al: Optional["pyodbc.Connection"] = None
        self._cn_hr: Optional["pyodbc.Connection"] = None
        self._cn_he: Optional["pyodbc.Connection"] = None
        self._cn_vi: Optional["pyodbc.Connection"] = None
        self._cn_pl: Optional["pyodbc.Connection"] = None
        self._cn_ot: Optional["pyodbc.Connection"] = None

    def _connect(self, database: str):
        if pyodbc is None:
            raise RuntimeError("pyodbc no está disponible.")
        raw = list(pyodbc.drivers())
        drvs: List[str] = []
        if "ODBC Driver 18 for SQL Server" in raw:
            drvs.append("ODBC Driver 18 for SQL Server")
        if "ODBC Driver 17 for SQL Server" in raw:
            drvs.append("ODBC Driver 17 for SQL Server")
        for d in raw:
            if "SQL Server" in d and d not in drvs:
                drvs.append(d)
        if not drvs:
            raise RuntimeError("No se encontró driver ODBC de SQL Server.")
        s = (self.server or "").strip()
        variants = [s] if s else []
        if "\\" in s:
            host, inst = s.split("\\", 1)
            variants += [f"{host}\\{inst}", f"localhost\\{inst}", f"127.0.0.1\\{inst}"]
        else:
            variants += [s, "localhost", "127.0.0.1", s + ",1433", "localhost,1433", "127.0.0.1,1433"]
        last = None
        for drv in drvs:
            for srv in [v for v in variants if v]:
                parts = [f"DRIVER={{{drv}}}", f"SERVER={srv}", f"DATABASE={database}", "Trusted_Connection=yes"]
                if "ODBC Driver 18" in drv:
                    parts += ["Encrypt=yes", "TrustServerCertificate=yes"]
                cs = ";".join(parts) + ";"
                try:
                    return pyodbc.connect(cs, autocommit=False, timeout=5)
                except Exception as e:
                    last = e
        raise RuntimeError("No fue posible abrir conexión. Último error: " + str(last))

    def cn_al(self):
        if self._cn_al is None:
            self._cn_al = self._connect(self.db_al)
        return self._cn_al

    def cn_hr(self):
        if self._cn_hr is None:
            self._cn_hr = self._connect(self.db_hr)
        return self._cn_hr

    def cn_he(self):
        if self._cn_he is None:
            self._cn_he = self._connect(self.db_he)
        return self._cn_he

    def cn_vi(self):
        if self._cn_vi is None:
            self._cn_vi = self._connect(self.db_vi)
        return self._cn_vi

    def cn_pl(self):
        if self._cn_pl is None:
            self._cn_pl = self._connect(self.db_pl)
        return self._cn_pl

    def cn_ot(self):
        if self._cn_ot is None:
            self._cn_ot = self._connect(self.db_ot)
        return self._cn_ot

    def obtener_descripcion(self, tipo: str, clave: str) -> str:
        tipo = (tipo or "").upper()
        clave = (clave or "").strip()
        if not clave:
            return ""
        try:
            if tipo == "AL":
                with self.cn_al().cursor() as c:
                    r = c.execute("SELECT Descripcion FROM materiales_aluminio WHERE Clave=?", clave).fetchone()
                return (r[0] if r else "") or ""
            elif tipo == "HR":
                with self.cn_hr().cursor() as c:
                    r = c.execute("SELECT Descripcion FROM materiales_herraje WHERE Clave=?", clave).fetchone()
                return (r[0] if r else "") or ""
            elif tipo == "PH":
                with self.cn_hr().cursor() as c:
                    r = c.execute("SELECT descripcion FROM paquetes_herrajes WHERE clave=?", clave).fetchone()
                return (r[0] if r else "") or ""
            elif tipo == "HE":
                with self.cn_he().cursor() as c:
                    r = c.execute("SELECT Descripcion FROM materiales_herreria WHERE Clave=?", clave).fetchone()
                return (r[0] if r else "") or ""
            elif tipo == "VI":
                with self.cn_vi().cursor() as c:
                    r = c.execute("SELECT Descripcion FROM materiales_vidrio WHERE Clave=?", clave).fetchone()
                return (r[0] if r else "") or ""
            elif tipo == "PL":
                with self.cn_pl().cursor() as c:
                    r = c.execute("SELECT Descripcion FROM materiales_plasticos WHERE Clave=?", clave).fetchone()
                return (r[0] if r else "") or ""
            elif tipo == "OT":
                with self.cn_ot().cursor() as c:
                    r = c.execute("SELECT Descripcion FROM materiales_otros WHERE Clave=?", clave).fetchone()
                return (r[0] if r else "") or ""
        except Exception as e:
            print(f"Error obteniendo descripción para tipo={tipo}, clave={clave}: {e}")
            logger.exception("Error obteniendo descripcion para tipo=%s clave=%s", tipo, clave)
        return ""

    def buscar_aluminio(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_aluminio ORDER BY Clave"
            params = []
        else:
            like = "%" + q + "%"
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_aluminio WHERE UPPER(Clave) LIKE ? OR UPPER(Descripcion) LIKE ? ORDER BY Clave"
            params = [like, like]
        with self.cn_al().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def buscar_herraje(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_herraje ORDER BY Clave"
            params = []
        else:
            like = "%" + q + "%"
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_herraje WHERE UPPER(Clave) LIKE ? OR UPPER(Descripcion) LIKE ? ORDER BY Clave"
            params = [like, like]
        with self.cn_hr().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def buscar_paquete_herraje(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 clave, descripcion FROM paquetes_herrajes ORDER BY clave"
            params = []
        else:
            like = "%" + q + "%"
            sql = "SELECT TOP 100 clave, descripcion FROM paquetes_herrajes WHERE UPPER(clave) LIKE ? OR UPPER(descripcion) LIKE ? ORDER BY clave"
            params = [like, like]
        with self.cn_hr().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def buscar_herreria(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_herreria ORDER BY Clave"
            params = []
        else:
            like = "%" + q + "%"
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_herreria WHERE UPPER(Clave) LIKE ? OR UPPER(Descripcion) LIKE ? ORDER BY Clave"
            params = [like, like]
        with self.cn_he().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def buscar_vidrio(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_vidrio ORDER BY Clave"
            params = []
        else:
            like = "%" + q + "%"
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_vidrio WHERE UPPER(Clave) LIKE ? OR UPPER(Descripcion) LIKE ? ORDER BY Clave"
            params = [like, like]
        with self.cn_vi().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def buscar_plasticos(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_plasticos ORDER BY Clave"
            params = []
        else:
            like = "%" + q + "%"
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_plasticos WHERE UPPER(Clave) LIKE ? OR UPPER(Descripcion) LIKE ? ORDER BY Clave"
            params = [like, like]
        with self.cn_pl().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def buscar_otros(self, texto: str, por: str = "clave") -> List[Dict]:
        q = (texto or "").strip().upper()
        if not q:
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_otros ORDER BY Clave"
            params = []
        else:
            like = "%" + q + "%"
            sql = "SELECT TOP 100 Clave, Descripcion FROM materiales_otros WHERE UPPER(Clave) LIKE ? OR UPPER(Descripcion) LIKE ? ORDER BY Clave"
            params = [like, like]
        with self.cn_ot().cursor() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def paquete_al_existe(self, clave: str) -> bool:
        with self.cn_al().cursor() as c:
            r = c.execute("SELECT 1 FROM paquetes_aluminio WHERE clave=?", clave).fetchone()
        return bool(r)

    def paquetes_al_listar(self) -> List[Dict]:
        with self.cn_al().cursor() as c:
            rows = c.execute("SELECT clave, descripcion FROM paquetes_aluminio ORDER BY clave").fetchall()
        return [{"clave": str(r[0]).strip(), "descripcion": (r[1] or "").strip()} for r in rows]

    def paquetes_al_y_items(self) -> List[Dict]:
        try:
            with self.cn_al().cursor() as c:
                paquetes_rows = c.execute("SELECT clave, descripcion FROM paquetes_aluminio ORDER BY clave").fetchall()
                paquetes = []
                for p_row in paquetes_rows:
                    clave = str(p_row[0]).strip()
                    descripcion = (p_row[1] or "").strip()
                    items_rows = c.execute("SELECT tipo, clv_item, horizontal, vertical, cantidad FROM paquete_aluminio_items WHERE clave_paquete=? ORDER BY tipo, clv_item", clave).fetchall()
                    items = []
                    for it_row in items_rows:
                        tipo = (it_row[0] or "").strip().upper()
                        clv_item = str(it_row[1]).strip()
                        desc_item = self.obtener_descripcion(tipo, clv_item)
                        items.append({
                            "tipo": tipo,
                            "clave": clv_item,
                            "descripcion": desc_item,
                            "horizontal": int(it_row[2] or 0),
                            "vertical": int(it_row[3] or 0),
                            "cantidad": int(it_row[4] or 0)
                        })
                    paquetes.append({
                        "clave": clave,
                        "descripcion": descripcion,
                        "items": items
                    })
                return paquetes
        except Exception as e:
            print(f"Error en paquetes_al_y_items: {e}")
            logger.exception("Error en paquetes_al_y_items")
            raise

    def paquete_al_cargar(self, clave: str) -> Tuple[Optional[Dict], List[Dict]]:
        with self.cn_al().cursor() as c:
            h = c.execute("SELECT clave, descripcion FROM paquetes_aluminio WHERE clave=?", clave).fetchone()
            if not h:
                return None, []
            hdr = {"clave": str(h[0]).strip(), "descripcion": (h[1] or "").strip()}
            rows = c.execute("SELECT tipo, clv_item, horizontal, vertical, cantidad FROM paquete_aluminio_items WHERE clave_paquete=? ORDER BY tipo, clv_item", clave).fetchall()
        items: List[Dict] = []
        for tipo, clv, h, v, cant in rows:
            clv = str(clv).strip()
            desc = self.obtener_descripcion(tipo, clv)
            items.append({
                "tipo": (tipo or "").strip(),
                "clave": clv,
                "descripcion": desc,
                "horizontal": int(h or 0),
                "vertical": int(v or 0),
                "cantidad": int(cant or 0)
            })
        return hdr, items

    def paquete_al_guardar(self, header: Dict, items: List[Dict]):
        if not header.get("clave"):
            raise ValueError("Falta clave del paquete")
        if not header.get("descripcion"):
            raise ValueError("Falta descripción del paquete")
        if not items:
            raise ValueError("Debe agregar al menos un ítem")
        cn = self.cn_al()
        with cn.cursor() as c:
            if self.paquete_al_existe(header["clave"]):
                c.execute("UPDATE paquetes_aluminio SET descripcion=? WHERE clave=?", header["descripcion"], header["clave"])
                c.execute("DELETE FROM paquete_aluminio_items WHERE clave_paquete=?", header["clave"])
            else:
                c.execute("INSERT INTO paquetes_aluminio(clave, descripcion) VALUES (?,?)", header["clave"], header["descripcion"])
            for it in items:
                tipo = (it.get("tipo") or "").upper()
                clv = str(it.get("clave") or "").strip()
                h = int(it.get("horizontal") or 0)
                v = int(it.get("vertical") or 0)
                cta = int(it.get("cantidad") or 0)
                if tipo == "AL":
                    pass
                else:
                    h = 0
                    v = 0
                    if cta < 1:
                        cta = 1
                c.execute("INSERT INTO paquete_aluminio_items(clave_paquete, tipo, clv_item, horizontal, vertical, cantidad) VALUES (?,?,?,?,?,?)", header["clave"], tipo, clv, h, v, cta)
            cn.commit()

    def paquete_al_eliminar(self, clave: str):
        cn = self.cn_al()
        with cn.cursor() as c:
            c.execute("DELETE FROM paquete_aluminio_items WHERE clave_paquete=?", clave)
            c.execute("DELETE FROM paquetes_aluminio WHERE clave=?", clave)
            cn.commit()

# =========================================
# UI
# =========================================
class UpperLineEdit(QLineEdit):
    """LineEdit que convierte automáticamente a mayúsculas."""
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        pos = self.cursorPosition()
        self.setText(self.text().upper())
        self.setCursorPosition(pos)

class PaquetesAluminioUI(QMainWindow):
    """Ventana principal para gestión de paquetes de aluminio."""
    def __init__(self, server: Optional[str] = None, db_al: Optional[str] = None,
                 db_hr: Optional[str] = None, db_he: Optional[str] = None,
                 db_vi: Optional[str] = None, db_pl: Optional[str] = None,
                 db_ot: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("VAH – Paquete de aluminio")
        for relative_path in (
            ("logo.jpg",),
            ("logo.png",),
            ("logo_00001.ico",),
            ("principal", "pantalla_principal.ico"),
        ):
            logo_path = get_resource_path(*relative_path)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break
        self._geom_applied = False
        self._workspace_rect: Optional[QRect] = self._read_workspace_env()
        self.db = DB(server=server, db_al=db_al, db_hr=db_hr,
                     db_he=db_he, db_vi=db_vi, db_pl=db_pl, db_ot=db_ot)
        self.items: List[Dict] = []
        self.edit_row_idx: Optional[int] = None
        self._estilos()
        self._build()
        self._wire()
        self._setup_shortcuts()
        self.Inicio()

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

    def _estilos(self):
        self.setStyleSheet(QSS_BASE + """
            QWidget { background-color:#D9E0E7; font-family: Segoe UI; font-size:10pt; }
            QGroupBox { border:1px solid #888; margin-top:10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 6px; }
            QLineEdit, QComboBox { background:white; border:1px solid gray; padding:5px; }
            QPushButton { background:#f2f2f2; border:1px solid #bbb; padding:6px 12px; }
            QPushButton:hover { background:#cce0ff; }
            QHeaderView::section { background:#0078D7; color:white; font-weight:bold; }
        """)

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout()
        central.setLayout(root)
        if not self.statusBar():
            self.setStatusBar(QStatusBar())
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
        act_salir.triggered.connect(self.close)
        menu_archivo.addAction(act_salir)
        # === Menú Catálogos ===
        menu_catalogos = self.menuBar().addMenu("&Catálogos")
        act_aluminio = QAction("Materiales Aluminio", self)
        act_aluminio.triggered.connect(self.on_open_perfil_aluminio)
        menu_catalogos.addAction(act_aluminio)
        act_herraje = QAction("Materiales Herraje", self)
        act_herraje.triggered.connect(self.on_open_material_herraje)
        menu_catalogos.addAction(act_herraje)
        act_paq_herrajes = QAction("Paquete Herrajes", self)
        act_paq_herrajes.triggered.connect(self.on_open_paq_herrajes)
        menu_catalogos.addAction(act_paq_herrajes)
        menu_catalogos.addSeparator()
        act_plasticos = QAction("Materiales Plásticos", self)
        act_plasticos.triggered.connect(self.on_open_material_plasticos)
        menu_catalogos.addAction(act_plasticos)
        act_otros = QAction("Materiales Otros", self)
        act_otros.triggered.connect(self.on_open_material_otros)
        menu_catalogos.addAction(act_otros)
        # === Menú Ayuda ===
        menu_ayuda = self.menuBar().addMenu("&Ayuda")
        act_manual_operativo = QAction("Manual Operativo", self)
        act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("Paquete_Aluminio", "operativo", self))
        menu_ayuda.addAction(act_manual_operativo)
        act_manual_tecnico = QAction("Manual Técnico", self)
        act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("Paquete_Aluminio", "tecnico", self))
        menu_ayuda.addAction(act_manual_tecnico)
        # Encabezado
        gb_hdr = QGroupBox("Datos del Paquete")
        g = QGridLayout()
        gb_hdr.setLayout(g)
        self.paquete_clave = UpperLineEdit()
        self.paquete_clave.setMaxLength(20)
        self.paquete_clave.setFixedWidth(160)
        self.paquete_desc = UpperLineEdit()
        self.paquete_desc.setMaxLength(200)
        self.paquete_desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        g.addWidget(QLabel("Clave:"), 0, 0)
        g.addWidget(self.paquete_clave, 0, 1)
        g.addWidget(QLabel("Descripción:"), 0, 2)
        g.addWidget(self.paquete_desc, 0, 3, 1, 5)
        root.addWidget(gb_hdr)
        # Captura de ítems
        gb_it = QGroupBox("Agregar ítems al paquete")
        gi = QGridLayout()
        gb_it.setLayout(gi)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["Aluminio", "Herraje", "Paquete herrajes", "Plásticos", "Otros"])
        self.it_clave = UpperLineEdit()
        self.it_clave.setMaxLength(20)
        self.it_clave.setFixedWidth(180)
        self.it_desc = UpperLineEdit()
        self.it_desc.setMaxLength(200)
        self.it_h = QLineEdit()
        self.it_h.setValidator(QIntValidator(0, 1_000_000))
        self.it_h.setFixedWidth(120)
        self.it_h.setPlaceholderText("Horizontal")
        self.it_v = QLineEdit()
        self.it_v.setValidator(QIntValidator(0, 1_000_000))
        self.it_v.setFixedWidth(120)
        self.it_v.setPlaceholderText("Vertical")
        self.it_cant = QLineEdit()
        self.it_cant.setValidator(QIntValidator(1, 1_000_000))
        self.it_cant.setFixedWidth(120)
        self.it_cant.setPlaceholderText("Cantidad (ej: 2)")
        self.btn_add = QPushButton("Agregar")
        gi.addWidget(QLabel("Tipo:"), 0, 0)
        gi.addWidget(self.cmb_tipo, 0, 1)
        gi.addWidget(QLabel("Clave:"), 1, 0)
        gi.addWidget(self.it_clave, 1, 1)
        gi.addWidget(QLabel("Descripción:"), 1, 2)
        gi.addWidget(self.it_desc, 1, 3, 1, 4)
        gi.addWidget(QLabel("Horizontal:"), 2, 0)
        gi.addWidget(self.it_h, 2, 1)
        gi.addWidget(QLabel("Vertical:"), 2, 2)
        gi.addWidget(self.it_v, 2, 3)
        gi.addWidget(QLabel("Cantidad:"), 2, 4)
        gi.addWidget(self.it_cant, 2, 5)
        gi.addWidget(self.btn_add, 2, 6)
        root.addWidget(gb_it)
        # Completers
        self.model_clave = create_key_description_model(self)
        self.model_desc = create_key_description_model(self)
        self.model_clave.setHorizontalHeaderLabels(["CLAVE", "DESCRIPCIÓN"])
        self.model_desc.setHorizontalHeaderLabels(["CLAVE", "DESCRIPCIÓN"])
        self.comp_clave = configure_two_column_completer(self.model_clave, display_column=0, parent=self)
        self.it_clave.setCompleter(self.comp_clave)
        self.comp_desc = configure_two_column_completer(self.model_desc, display_column=1, parent=self)
        self.it_desc.setCompleter(self.comp_desc)
        # Configurar altura fija del popup (siempre 15 filas visibles)
        for comp in [self.comp_clave, self.comp_desc]:
            popup = comp.popup()
            if popup:
                row_height = max(popup.sizeHintForRow(0), 24)
                frame = popup.frameWidth() * 2
                fixed_height = (row_height * 15) + frame + 4
                popup.setMinimumHeight(fixed_height)
                popup.setMaximumHeight(fixed_height)
                popup.setMinimumWidth(500)
                popup.setColumnWidth(0, 120)
                popup.setColumnWidth(1, 350)
                popup.horizontalHeader().setStretchLastSection(True)
        # Botonera
        self.botones = {}
        self.botones["Guardar"] = QPushButton("Guardar")
        self.botones["Guardar"].setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.botones["Guardar"].setToolTip("Guardar paquete (Ctrl+S)")
        self.botones["Editar"] = QPushButton("Editar")
        self.botones["Editar"].setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold;")
        self.botones["Editar"].setToolTip("Editar paquete existente")
        self.botones["Eliminar"] = QPushButton("Eliminar")
        self.botones["Eliminar"].setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
        self.botones["Eliminar"].setToolTip("Eliminar paquete")
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
        # Botones específicos (siempre visibles)
        self.botones["Quitar item"] = QPushButton("Quitar item")
        self.botones["Quitar item"].setStyleSheet("background-color: #8B5CF6; color: white; font-weight: bold;")
        self.botones["Quitar item"].setToolTip("Quitar ítem seleccionado")
        # Configurar botones
        for b in [self.botones["Guardar"], self.botones["Editar"], self.botones["Eliminar"],
                  self.botones["Limpiar"], self.botones["Refresh"], self.botones["Imprimir"],
                  self.botones["Quitar item"], self.botones["Salir"]]:
            try:
                b.setAutoDefault(False)
                b.setDefault(False)
            except Exception:
                pass
            b.setFixedHeight(36)
        self.botones["Guardar"].setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Añadir botones a la barra (solo los visibles)
        bar = QHBoxLayout()
        root.addLayout(bar)
        for b in ["Guardar", "Editar", "Eliminar", "Limpiar", "Quitar item"]:
            self.botones[b].setFixedHeight(36)
            bar.addWidget(self.botones[b])
        bar.addStretch()
        # Reglas de foco para botones
        for b in ("Editar", "Eliminar", "Limpiar", "Refresh", "Imprimir", "Salir", "Importar", "Quitar item"):
            self.botones[b].setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Tabla de ítems
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["TIPO", "CLAVE", "DESCRIPCIÓN", "H", "V", "CANT"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        root.addWidget(self.tbl)
        apply_tab_order(self, [self.paquete_clave, self.paquete_desc, self.cmb_tipo, self.it_clave, self.it_desc, self.it_h, self.it_v, self.it_cant, self.btn_add, self.botones["Guardar"], self.tbl])
        self._focus_selection = install_select_all_on_focus(self, [self.paquete_clave, self.paquete_desc, self.cmb_tipo, self.it_clave, self.it_desc, self.it_h, self.it_v, self.it_cant])
        self._combo_popup = install_auto_popup_on_focus(self, [self.cmb_tipo])
        self._update_item_fields_visibility()

    def _wire(self):
        self.botones["Guardar"].clicked.connect(self.on_guardar)
        self.botones["Editar"].clicked.connect(self.on_editar_paquete)
        self.botones["Eliminar"].clicked.connect(self.on_eliminar)
        self.botones["Limpiar"].clicked.connect(self.Inicio)
        self.botones["Refresh"].clicked.connect(self.Inicio)
        self.botones["Imprimir"].clicked.connect(self.on_imprimir)
        self.botones["Quitar item"].clicked.connect(self.on_quitar_item)
        self.botones["Salir"].clicked.connect(self.close)
        self.cmb_tipo.currentIndexChanged.connect(self._update_item_fields_visibility)
        self.paquete_clave.returnPressed.connect(self._validar_clave_paquete_y_avanzar)
        # NO conectar a editingFinished para evitar lentitud
        self.paquete_desc.returnPressed.connect(lambda: self.cmb_tipo.setFocus())
        # NO conectar _on_tipo_changed para evitar ciclo
        self.it_clave.textEdited.connect(self._buscar_popup)
        self.it_desc.textEdited.connect(self._buscar_popup)
        self.comp_clave.activated[QModelIndex].connect(self._on_clave_activada)
        self.comp_desc.activated[QModelIndex].connect(self._on_desc_activada)
        self.it_clave.editingFinished.connect(self._sync_from_clave_with_validation)
        self.it_desc.editingFinished.connect(self._sync_from_desc_with_validation)
        self.it_clave.returnPressed.connect(lambda: self._auto_complete_and_focus(origin='clave'))
        self.it_desc.returnPressed.connect(lambda: self._auto_complete_and_focus(origin='desc'))
        self.it_h.returnPressed.connect(lambda: self._navigate_after_h())
        self.it_v.returnPressed.connect(lambda: self._navigate_after_v())
        self.it_cant.returnPressed.connect(lambda: self.btn_add.setFocus())
        self.btn_add.clicked.connect(self._agregar_item)
        self.tbl.customContextMenuRequested.connect(self._menu_tbl)
        self.tbl.itemSelectionChanged.connect(self._cargar_fila_a_campos)
        self.tbl.cellDoubleClicked.connect(lambda *_: self._cargar_fila_a_campos())
        self.tbl.installEventFilter(self)
        self.installEventFilter(self)
        self.it_clave.installEventFilter(self)
        self.it_desc.installEventFilter(self)
        self.btn_add.installEventFilter(self)
        self.botones["Guardar"].installEventFilter(self)

    def _on_tipo_changed(self):
        if self.sender() is self.cmb_tipo and self.it_clave.isVisible():
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, lambda: self.it_clave.setFocus())

    def _navigate_after_h(self):
        t = self._tipo_codigo()
        if t == "AL":
            self.it_v.setFocus()
        else:
            self.it_cant.setFocus()

    def _navigate_after_v(self):
        self.it_cant.setFocus()

    def _setup_shortcuts(self):
        def _act(seq: str, slot):
            a = QAction(self)
            a.setShortcut(QKeySequence(seq))
            a.triggered.connect(slot)
            self.addAction(a)
        _act("Ctrl+S", self.on_guardar)
        _act("Ctrl+E", self.on_editar_paquete)
        _act("Delete", self.on_quitar_item)
        _act("Ctrl+P", self.on_imprimir)
        _act("F5", self.Inicio)
        _act("Esc", self.close)

    def Inicio(self):
        self.items.clear()
        self.edit_row_idx = None
        for w in (self.paquete_clave, self.paquete_desc, self.it_clave, self.it_desc, self.it_h, self.it_v, self.it_cant):
            w.clear()
        self.it_cant.setText("1")
        self._refrescar_tabla_items()
        self._update_item_fields_visibility()
        self.paquete_clave.setFocus()
        self.btn_add.setText("Agregar")
        if not self.statusBar():
            self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Pantalla en estado inicial.", 3000)

    def eventFilter(self, obj, event):
        if obj is self.tbl and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                self.on_quitar_item()
                return True
        if event.type() == QEvent.Type.KeyPress and obj in (self.it_clave, self.it_desc):
            if event.key() == Qt.Key.Key_Down:
                if obj is self.it_clave and self.model_clave.rowCount() > 0:
                    self.comp_clave.complete()
                    return True
                if obj is self.it_desc and self.model_desc.rowCount() > 0:
                    self.comp_desc.complete()
                    return True
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            fw = self.focusWidget()
            if isinstance(fw, QPushButton):
                fw.click()
                return True
        return super().eventFilter(obj, event)

    def _menu_tbl(self, pos):
        if self.tbl.currentRow() < 0:
            return
        m = QMenu(self)
        act_edit = m.addAction("Editar fila")
        act_del = m.addAction("Quitar item")
        a = m.exec(self.tbl.viewport().mapToGlobal(pos))
        if a == act_del:
            self.on_quitar_item()
        elif a == act_edit:
            self._cargar_fila_a_campos()

    def _tipo_codigo(self) -> str:
        index = self.cmb_tipo.currentIndex()
        tipos = ["AL", "HR", "PH", "PL", "OT"]
        return tipos[index] if 0 <= index < len(tipos) else "AL"

    def _update_item_fields_visibility(self):
        t = self._tipo_codigo()
        usa_h_v = t == "AL"
        self.it_h.setEnabled(usa_h_v)
        self.it_v.setEnabled(usa_h_v)
        self.it_cant.setEnabled(True)
        if usa_h_v:
            self.it_h.setPlaceholderText("Horizontal")
            self.it_v.setPlaceholderText("Vertical")
            self.it_cant.setPlaceholderText("Cantidad (ej: 2)")
        else:
            self.it_h.setPlaceholderText("N/A")
            self.it_v.setPlaceholderText("N/A")
            self.it_cant.setPlaceholderText("Cantidad (ej: 1)")
        if self.sender() is self.cmb_tipo:
            if not usa_h_v:
                self.it_h.clear()
                self.it_v.clear()
        self.model_clave.setRowCount(0)
        self.model_desc.setRowCount(0)

    def _validar_clave_paquete_y_avanzar(self):
        clave = (self.paquete_clave.text() or "").strip().upper()
        if not clave:
            QMessageBox.warning(self, "Validación", "Captura la CLAVE del paquete.")
            self.paquete_clave.setFocus()
            return
        try:
            if self.db.paquete_al_existe(clave):
                r = QMessageBox.question(self, "Clave existente", f"La clave de paquete '{clave}' ya existe.\n\n¿Deseas editarlo?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if r == QMessageBox.StandardButton.Yes:
                    hdr, items = self.db.paquete_al_cargar(clave)
                    if hdr:
                        self.paquete_clave.setText(hdr["clave"])
                        self.paquete_desc.setText(hdr["descripcion"])
                        self.items = list(items)
                        self._refrescar_tabla_items()
                        self.cmb_tipo.setFocus()
                        self.statusBar().showMessage(f"Editando paquete {clave}", 4000)
                        return
                else:
                    # Usuario canceló - solo limpiar el campo y mantener foco
                    self.paquete_clave.clear()
                    self.paquete_clave.setFocus()
                    return
            # Clave válida, avanzar a Descripción
            self.paquete_desc.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Validación", f"No fue posible validar la clave del paquete:\n{e}")

    def _buscar_popup(self):
        sender = self.sender()
        if not isinstance(sender, QLineEdit):
            return
        texto = sender.text()
        t = self._tipo_codigo()
        try:
            if sender is self.it_desc:
                rows = self._buscar_por_tipo(t, texto, "descripcion")
                self._fill_model(self.model_desc, rows)
                if rows:
                    self.comp_desc.complete()
                else:
                    self.comp_desc.popup().hide()
            else:
                rows = self._buscar_por_tipo(t, texto, "clave")
                self._fill_model(self.model_clave, rows)
                if rows:
                    self.comp_clave.complete()
                else:
                    self.comp_clave.popup().hide()
        except Exception as e:
            self.statusBar().showMessage("No se pudo consultar catálogo: " + str(e), 4000)

    def _buscar_por_tipo(self, tipo: str, texto: str, por: str) -> List[Dict]:
        if tipo == "AL":
            return self.db.buscar_aluminio(texto, por)
        elif tipo == "HR":
            return self.db.buscar_herraje(texto, por)
        elif tipo == "PH":
            return self.db.buscar_paquete_herraje(texto, por)
        elif tipo == "PL":
            return self.db.buscar_plasticos(texto, por)
        elif tipo == "OT":
            return self.db.buscar_otros(texto, por)
        else:
            return []

    def _fill_model(self, model: QStandardItemModel, rows: List[Dict]):
        populate_key_description_model(model, rows)

    def _set_selected_item(self, clave: str, desc: str):
        if clave:
            self.it_clave.setText(clave)
        if desc:
            self.it_desc.setText(desc)

    def _on_clave_activada(self, index):
        if not index.isValid():
            return
        clave, desc = get_key_description_from_index(index)
        self._set_selected_item(clave, desc)
        self._focus_next_after_selection()

    def _on_desc_activada(self, index):
        if not index.isValid():
            return
        clave, desc = get_key_description_from_index(index)
        self._set_selected_item(clave, desc)
        self._focus_next_after_selection()

    def _focus_next_after_selection(self):
        t = self._tipo_codigo()
        if t == "AL":
            self.it_h.setFocus()
        else:
            self.it_cant.setFocus()

    def _sync_from_clave_with_validation(self):
        clv = (self.it_clave.text() or "").strip()
        if not clv:
            self.it_desc.clear()
            return
        d = self.db.obtener_descripcion(self._tipo_codigo(), clv)
        if d:
            self.it_desc.setText(d)
        else:
            self._handle_inexistent("clave")

    def _sync_from_desc_with_validation(self):
        desc = (self.it_desc.text() or "").strip()
        if not desc:
            return
        t = self._tipo_codigo()
        rows = self._buscar_por_tipo(t, desc, "descripcion")
        if len(rows) == 1:
            self.it_clave.setText(rows[0]["clave"])
        elif len(rows) == 0:
            self._handle_inexistent("descripcion")

    def _auto_complete_and_focus(self, origin: str):
        try:
            if origin == 'clave':
                self._auto_complete_from('clave')
                self._focus_next_after_selection()
            else:
                self._auto_complete_from('desc')
                self._focus_next_after_selection()
        except Exception as e:
            self.statusBar().showMessage("No se pudo completar: " + str(e), 4000)

    def _auto_complete_from(self, origin: str):
        t = self._tipo_codigo()
        if origin == 'clave':
            val = (self.it_clave.text() or "").strip().upper()
            if not val:
                return
            rows = self._buscar_por_tipo(t, val, "clave")
            best = next((r for r in rows if str(r.get("clave", "")).strip().upper() == val), None)
            if not best and len(rows) == 1:
                best = rows[0]
            if best:
                self._set_selected_item(str(best["clave"]), best.get("descripcion", ""))
        else:
            val = (self.it_desc.text() or "").strip().upper()
            if not val:
                return
            rows = self._buscar_por_tipo(t, val, "descripcion")
            best = next((r for r in rows if (r.get("descripcion", "") or "").strip().upper() == val), None)
            if not best and len(rows) == 1:
                best = rows[0]
            if best:
                self._set_selected_item(str(best["clave"]), best.get("descripcion", ""))

    def _handle_inexistent(self, campo: str):
        is_clave = (campo == "clave")
        pregunta = "Clave inexistente, ¿Deseas agregarlo?" if is_clave else "Descripción inexistente, ¿Deseas agregarlo?"
        ret = QMessageBox.question(self, "Validación", pregunta, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            t = self._tipo_codigo()
            if t == "AL":
                self.on_open_perfil_aluminio()
            elif t == "HR":
                self.on_open_material_herraje()
            elif t == "PL":
                self.on_open_material_plasticos()
            elif t == "OT":
                self.on_open_material_otros()
            elif t == "PH":
                self.on_open_paq_herrajes()
        else:
            ret2 = QMessageBox.question(self, "Continuar", "¿Deseas dar de alta otro item?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret2 == QMessageBox.StandardButton.Yes:
                self._limpiar_campos_item()
                self.it_cant.setText("1")
                self.it_clave.setFocus()
            else:
                self.botones["Guardar"].setFocus()

    def _limpiar_campos_item(self):
        self.it_clave.clear()
        self.it_desc.clear()
        self.it_h.clear()
        self.it_v.clear()
        self.it_cant.clear()
        self.it_cant.setText("1")

    def _refrescar_tabla_items(self):
        self.items.sort(key=lambda r: (r["tipo"], r["clave"]))
        self.tbl.setRowCount(0)
        for it in self.items:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(it["tipo"]))
            self.tbl.setItem(r, 1, QTableWidgetItem(it["clave"]))
            self.tbl.setItem(r, 2, QTableWidgetItem(it.get("descripcion", "")))
            self.tbl.setItem(r, 3, QTableWidgetItem(str(it.get("horizontal", 0))))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(it.get("vertical", 0))))
            self.tbl.setItem(r, 5, QTableWidgetItem(str(it.get("cantidad", 0))))
        self.tbl.clearSelection()

    def _cargar_fila_a_campos(self):
        row = self.tbl.currentRow()
        if row < 0 or row >= len(self.items):
            return
        it = self.items[row]
        tipo_map = {"AL": 0, "HR": 1, "PH": 2, "PL": 3, "OT": 4}
        idx = tipo_map.get(it["tipo"], 0)
        self.cmb_tipo.setCurrentIndex(idx)
        self.it_clave.setText(it["clave"])
        self.it_desc.setText(it.get("descripcion", ""))
        self.it_cant.setText(str(it.get("cantidad", 0) or 0))
        self.it_h.setText("" if it.get("horizontal", 0) == 0 else str(it.get("horizontal", 0)))
        self.it_v.setText("" if it.get("vertical", 0) == 0 else str(it.get("vertical", 0)))
        self.edit_row_idx = row
        self.btn_add.setText("Actualizar")
        self.it_clave.setFocus()

    def on_quitar_item(self):
        row = self.tbl.currentRow()
        if row < 0 or row >= len(self.items):
            QMessageBox.warning(self, "Quitar item", "Selecciona un renglón.")
            return
        it = self.items[row]
        if QMessageBox.question(self, "Quitar item", f"¿Eliminar el ítem {it.get('tipo', '')} '{it.get('clave', '')}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        del self.items[row]
        self.edit_row_idx = None
        self.btn_add.setText("Agregar")
        self._refrescar_tabla_items()
        self.statusBar().showMessage("Ítem eliminado.", 3000)

    def _agregar_item(self):
        t = self._tipo_codigo()
        clave = (self.it_clave.text() or "").strip().upper()
        desc = (self.it_desc.text() or "").strip()
        if not clave:
            QMessageBox.warning(self, "Validación", "Captura la CLAVE.")
            self.it_clave.setFocus()
            return
        db_desc = self.db.obtener_descripcion(t, clave)
        if not db_desc:
            self._handle_inexistent("clave")
            return
        if not desc or desc != db_desc:
            desc = db_desc
            self.it_desc.setText(desc)
        cant_text = self.it_cant.text().strip()
        cantidad = int(cant_text) if cant_text else 1
        if cantidad <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser >= 1.")
            self.it_cant.setFocus()
            return
        if t == "AL":
            h = int((self.it_h.text().strip() or "0"))
            v = int((self.it_v.text().strip() or "0"))
            if h < 0 or v < 0:
                QMessageBox.warning(self, "Validación", "Horizontal/Vertical no pueden ser negativos.")
                self.it_h.setFocus()
                return
            new_item = {"tipo": t, "clave": clave, "descripcion": desc, "horizontal": h, "vertical": v, "cantidad": cantidad}
        else:
            new_item = {"tipo": t, "clave": clave, "descripcion": desc, "horizontal": 0, "vertical": 0, "cantidad": cantidad}
        self._procesar_nuevo_item(new_item)

    def _procesar_nuevo_item(self, new_item: Dict):
        t = new_item["tipo"]
        if self.edit_row_idx is not None:
            self.items[self.edit_row_idx] = new_item
            self.edit_row_idx = None
            self.btn_add.setText("Agregar")
        else:
            encontrado = False
            for it in self.items:
                if it["tipo"] == new_item["tipo"] and it["clave"] == new_item["clave"]:
                    it["cantidad"] += new_item["cantidad"]
                    if t == "AL":
                        it["horizontal"] += new_item["horizontal"]
                        it["vertical"] += new_item["vertical"]
                    if new_item["descripcion"] and new_item["descripcion"] != it.get("descripcion", ""):
                        it["descripcion"] = new_item["descripcion"]
                    encontrado = True
                    break
            if not encontrado:
                self.items.append(new_item)
        self._refrescar_tabla_items()
        self._limpiar_campos_item()
        self._update_item_fields_visibility()
        self.it_clave.setFocus()

    def on_guardar(self):
        hdr_clave = (self.paquete_clave.text() or "").strip().upper()
        hdr_desc = (self.paquete_desc.text() or "").strip()
        if not hdr_clave:
            QMessageBox.warning(self, "Validación", "Debes capturar la CLAVE del paquete.")
            self.paquete_clave.setFocus()
            return
        if not hdr_desc:
            QMessageBox.warning(self, "Validación", "Debes capturar la DESCRIPCIÓN del paquete.")
            self.paquete_desc.setFocus()
            return
        if not self.items:
            QMessageBox.warning(self, "Validación", "Agrega al menos un ítem.")
            return
        try:
            if self.db.paquete_al_existe(hdr_clave):
                if QMessageBox.question(self, "Duplicado", f"Ya existe un paquete con la clave {hdr_clave}. ¿Sobrescribir?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                    return
            self.db.paquete_al_guardar({"clave": hdr_clave, "descripcion": hdr_desc}, self.items)
            QMessageBox.information(self, "Guardar", "Paquete guardado con éxito.")
            self.Inicio()
        except Exception as e:
            QMessageBox.critical(self, "Error", "No fue posible guardar:\n" + str(e))

    def on_editar_paquete(self):
        try:
            dlg = PaquetePicker(self.db, self)
        except Exception as e:
            QMessageBox.critical(self, "Editar", "No fue posible obtener listado:\n" + str(e))
            return
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        clave = dlg.selected_clave()
        if not clave:
            return
        try:
            hdr, items = self.db.paquete_al_cargar(clave)
        except Exception as e:
            QMessageBox.critical(self, "Editar", "No fue posible cargar el paquete:\n" + str(e))
            return
        if not hdr:
            QMessageBox.warning(self, "Editar", f"No existe el paquete {clave}.")
            return
        self.paquete_clave.setText(hdr["clave"])
        self.paquete_desc.setText(hdr["descripcion"])
        self.items = list(items)
        self._refrescar_tabla_items()
        self.cmb_tipo.setFocus()
        self.statusBar().showMessage("Editando paquete " + clave, 4000)

    def on_eliminar(self):
        from PyQt6.QtWidgets import QInputDialog
        clave, ok = QInputDialog.getText(self, "Eliminar paquete", "Clave del paquete:")
        if not ok or not (clave or "").strip():
            return
        clave = clave.strip().upper()
        if QMessageBox.question(self, "Eliminar", f"¿Seguro que deseas eliminar {clave}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.paquete_al_eliminar(clave)
            QMessageBox.information(self, "Eliminar", "Paquete eliminado.")
            self.Inicio()
        except Exception as e:
            QMessageBox.critical(self, "Error", "No fue posible eliminar:\n" + str(e))

    def on_imprimir(self):
        if imprimir_paquetes is None:
            msg = "No se pudo cargar el motor interno de impresion/PDF del modulo.\nVerifica que el ejecutable se haya compilado con sus dependencias."
            if _IMPRIMIR_IMPORT_ERROR:
                msg += "\nDetalle: " + _IMPRIMIR_IMPORT_ERROR.splitlines()[-1]
            QMessageBox.critical(self, "Imprimir", msg)
            return
        try:
            imprimir_paquetes(self, self.db)
        except Exception as e:
            QMessageBox.critical(self, "Imprimir", f"Ocurrió un error al imprimir:\n{e}")

    def on_open_paq_herrajes(self):
        if abrir_paquetes_herrajes_con_args(self, server=self.db.server, database=self.db.db_hr):
            self.statusBar().showMessage("Abriendo Paquetes de Herrajes...", 3000)

    def on_open_perfil_aluminio(self):
        abrir_materiales_aluminio(self)

    def on_open_material_herraje(self):
        abrir_materiales_herrajes(self)

    def on_open_material_plasticos(self):
        abrir_materiales_plasticos(self)

    def on_open_material_otros(self):
        abrir_materiales_otros(self)


class PaquetePicker(QDialog):
    """Diálogo para seleccionar un paquete de aluminio existente."""
    def __init__(self, db: DB, parent=None):
        super().__init__(parent)
        self._db = db
        self.setWindowTitle("Seleccionar paquete (aluminio)")
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
        self.tbl.itemDoubleClicked.connect(lambda *_: self.accept())
        self._cargar()
        self._btn_ok = btns.button(QDialogButtonBox.StandardButton.Ok)
        self._btn_ok.setEnabled(False)
        self.tbl.selectionModel().selectionChanged.connect(lambda *_: self._btn_ok.setEnabled(self.tbl.currentRow() >= 0))

    def _cargar(self):
        rows = self._db.paquetes_al_listar()
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
    """Parseo de argumentos de línea de comandos."""
    p = argparse.ArgumentParser()
    p.add_argument("--server", default=r"DESKTOP-AE60PUN\SQLEXPRESS")
    p.add_argument("--db_al", default="aluminio")
    p.add_argument("--db_hr", default="herrajes")
    p.add_argument("--db_he", default="herreria")
    p.add_argument("--db_vi", default="vidrio")
    p.add_argument("--db_pl", default="plasticos")
    p.add_argument("--db_ot", default="otros")
    return p.parse_args()


def main():
    """Función principal de la aplicación."""
    args = parse_args()
    app = QApplication(sys.argv)
    win = PaquetesAluminioUI(
        server=args.server,
        db_al=args.db_al,
        db_hr=args.db_hr,
        db_he=args.db_he,
        db_vi=args.db_vi,
        db_pl=args.db_pl,
        db_ot=args.db_ot
    )
    win.show()
    win.raise_()
    win.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()