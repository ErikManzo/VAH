# -*- coding: utf-8 -*-
r"""
Pantalla de Herrajes (PyQt6)
VERSIÓN CORREGIDA:
Menús organizados (Archivo, Herramientas, Ayuda)
Botones CRUD con colores profesionales
Navegación simple con focus_simple.py
Conserva: ImportDialog, ImportWorker, VentanaDivisora
"""
import os
import sys
import csv
import json
import datetime
import tempfile
from decimal import Decimal
from typing import List, Dict, Optional

PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QGroupBox, QFileDialog,
    QAbstractItemView, QGridLayout, QSizePolicy, QProgressDialog,
    QStatusBar, QDialog, QComboBox, QCheckBox, QDialogButtonBox,
    QScrollArea, QMenuBar,
)
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QRect, QEvent
from PyQt6.QtGui import QIcon, QDoubleValidator, QAction, QKeySequence
from common.app_paths import get_logs_dir, get_resource_path
from common.estilos import QSS_BASE
from common.focus_simple import NavLineEdit as NavLineEditSimple
from common.pdf_utils import get_pdf_path
from common.logger_config import get_logger
from common.manuales import abrir_manual_pdf

logger = get_logger('materiales.herrajes.pantalla')

from materiales.herrajes.db_manager import DBManager
from materiales.herrajes.imprimir import imprimir_pdf_guardar
from materiales.herrajes.utils import dec2, detectar_columnas_excel
from materiales.herrajes.ventana_divisora import VentanaDivisora

# Parsers
from materiales.herrajes.parsers import parse_excel_profilo, parse_excel_herralum

# Configuración de mapeo
_MAPPING_CONFIG_PATH = os.path.join(get_logs_dir(), "herrajes_column_mapping.json")


def _load_mapping_config() -> dict:
    """Carga la configuración guardada de mapeo de columnas."""
    try:
        if os.path.exists(_MAPPING_CONFIG_PATH):
            with open(_MAPPING_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_mapping_config(config: dict):
    """Guarda la configuración de mapeo de columnas."""
    try:
        os.makedirs(os.path.dirname(_MAPPING_CONFIG_PATH), exist_ok=True)
        with open(_MAPPING_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _find_header_row(df: pd.DataFrame, max_rows: int = 20) -> int:
    """Busca la fila con más celdas no vacías."""
    search_limit = min(max_rows, len(df))
    best_row = 0
    best_count = 0
    for i in range(search_limit):
        non_null = df.iloc[i].notna().sum()
        if non_null > best_count:
            best_count = non_null
            best_row = i
    return best_row


# ==========================
# Diálogo de Importación
# ==========================
class ImportDialog(QDialog):
    """Diálogo para seleccionar hojas y mapear columnas antes de importar."""
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.setWindowTitle(f"Configurar Importación - {self.file_name}")
        self.setMinimumSize(780, 580)
        
        saved_config = _load_mapping_config()
        self.saved_sheet_config = saved_config.get(self.file_name, {})
        self.sheets_info = self._analyze_excel()
        self.selected_sheets: List[str] = []
        self.column_mapping: Dict[str, str] = {}
        self.result_accepted = False
        
        self._ui()
        self._load_saved_or_detect()
    
    def _analyze_excel(self) -> dict:
        try:
            xl = pd.ExcelFile(self.file_path)
            sheets = {}
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(self.file_path, sheet_name=sheet_name, header=None, nrows=30, dtype=str, keep_default_na=False, na_filter=False)
                sheets[sheet_name] = df.fillna("")
            return sheets
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo:\n{e}")
            return {}
    
    def _get_headers(self, df: pd.DataFrame) -> list:
        header_row_idx = _find_header_row(df)
        if header_row_idx < len(df):
            row = df.iloc[header_row_idx]
            return [str(h).strip() if pd.notna(h) and str(h).strip() != "" else f"Columna {i+1}" for i, h in enumerate(row.tolist())]
        return []
    
    def _get_data_preview(self, df: pd.DataFrame) -> pd.DataFrame:
        header_row_idx = _find_header_row(df)
        data_start = header_row_idx + 1
        if len(df) > data_start:
            data = df.iloc[data_start:data_start + 5].copy()
            data.columns = range(len(data.columns))
            return data
        return pd.DataFrame()
    
    def _ui(self):
        layout = QVBoxLayout()
        
        # Hojas a procesar
        sheets_group = QGroupBox("Hojas a procesar")
        sheets_layout = QVBoxLayout()
        self.sheet_checkboxes = {}
        for sheet_name in self.sheets_info.keys():
            cb = QCheckBox(sheet_name)
            cb.setChecked(True)
            sheets_layout.addWidget(cb)
            self.sheet_checkboxes[sheet_name] = cb
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(sheets_layout)
        scroll.setWidget(scroll_widget)
        scroll.setMaximumHeight(120)
        sheets_group.setLayout(QVBoxLayout())
        sheets_group.layout().addWidget(scroll)
        layout.addWidget(sheets_group)
        
        # Mapeo de columnas
        mapping_group = QGroupBox("Mapeo de columnas")
        mapping_layout = QGridLayout()
        headers = []
        if self.sheets_info:
            first_sheet = list(self.sheets_info.values())[0]
            headers = self._get_headers(first_sheet)
        
        self.combo_clave = QComboBox()
        self.combo_desc = QComboBox()
        self.combo_um = QComboBox()
        self.combo_precio = QComboBox()
        
        for combo in [self.combo_clave, self.combo_desc, self.combo_um, self.combo_precio]:
            combo.addItem("(Seleccionar)", None)
            for h in headers:
                combo.addItem(h, h)
            combo.setMinimumWidth(200)
        
        mapping_layout.addWidget(QLabel("Clave:"), 0, 0)
        mapping_layout.addWidget(self.combo_clave, 0, 1)
        mapping_layout.addWidget(QLabel("Descripción:"), 0, 2)
        mapping_layout.addWidget(self.combo_desc, 0, 3)
        mapping_layout.addWidget(QLabel("UM:"), 1, 0)
        mapping_layout.addWidget(self.combo_um, 1, 1)
        mapping_layout.addWidget(QLabel("Precio:"), 1, 2)
        mapping_layout.addWidget(self.combo_precio, 1, 3)
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Previsualización
        preview_group = QGroupBox("Previsualización (primeras filas de datos)")
        preview_layout = QVBoxLayout()
        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        for combo in [self.combo_clave, self.combo_desc, self.combo_um, self.combo_precio]:
            combo.currentIndexChanged.connect(self._update_preview)
    
    def _load_saved_or_detect(self):
        saved_mapping = self.saved_sheet_config.get("mapping", None)
        if saved_mapping:
            self._select_combo(self.combo_clave, saved_mapping.get("clave"))
            self._select_combo(self.combo_desc, saved_mapping.get("descripcion"))
            self._select_combo(self.combo_um, saved_mapping.get("um"))
            self._select_combo(self.combo_precio, saved_mapping.get("precio"))
            saved_sheets = self.saved_sheet_config.get("sheets", [])
            for name, cb in self.sheet_checkboxes.items():
                cb.setChecked(name in saved_sheets if saved_sheets else True)
        else:
            self._auto_detect()
        self._update_preview()
    
    def _auto_detect(self):
        if not self.sheets_info:
            return
        first_sheet = list(self.sheets_info.values())[0]
        headers = self._get_headers(first_sheet)
        df_data = self._get_data_preview(first_sheet)
        if df_data.empty or not headers:
            return
        detected = detectar_columnas_excel(df_data, headers)
        if detected[0]:
            self._select_combo(self.combo_clave, detected[0])
        if detected[1]:
            self._select_combo(self.combo_desc, detected[1])
        if detected[2]:
            self._select_combo(self.combo_um, detected[2])
        if detected[3]:
            self._select_combo(self.combo_precio, detected[3])
        has_missing = any(d is None for d in detected)
        if has_missing:
            missing_fields = []
            names = ["Clave", "Descripción", "UM", "Precio"]
            for i, (d, name) in enumerate(zip(detected, names)):
                if d is None:
                    missing_fields.append(name)
            QMessageBox.information(self, "Columnas no detectadas",
                                    f"No se pudieron detectar automáticamente las columnas:\n"
                                    f"{', '.join(missing_fields)}\n\n"
                                    f"Por favor, selecciónelas manualmente de la lista.")
    
    def _select_combo(self, combo: QComboBox, text: str):
        if not text:
            return
        text_norm = str(text).strip().lower()
        for i in range(combo.count()):
            item_data = combo.itemData(i)
            if item_data and str(item_data).strip().lower() == text_norm:
                combo.setCurrentIndex(i)
                return
        for i in range(combo.count()):
            item_data = combo.itemData(i)
            if item_data and text_norm in str(item_data).strip().lower():
                combo.setCurrentIndex(i)
                return
    
    def _update_preview(self):
        self.preview_table.clear()
        mapping = {
            "clave": self.combo_clave.currentData(),
            "descripcion": self.combo_desc.currentData(),
            "um": self.combo_um.currentData(),
            "precio": self.combo_precio.currentData(),
        }
        if not any(mapping.values()):
            self.preview_table.setColumnCount(0)
            self.preview_table.setRowCount(0)
            return
        first_sheet_name = None
        for name, cb in self.sheet_checkboxes.items():
            if cb.isChecked():
                first_sheet_name = name
                break
        if not first_sheet_name:
            self.preview_table.setColumnCount(0)
            self.preview_table.setRowCount(0)
            return
        df = self.sheets_info.get(first_sheet_name)
        if df is None:
            return
        headers = self._get_headers(df)
        data = self._get_data_preview(df)
        if data.empty:
            return
        
        def find_idx(col_name):
            if not col_name:
                return None
            col_name_norm = str(col_name).strip().lower()
            for i, h in enumerate(headers):
                if h.strip().lower() == col_name_norm:
                    return i
            for i, h in enumerate(headers):
                if col_name_norm in h.strip().lower():
                    return i
            return None
        
        idxs = {k: find_idx(v) for k, v in mapping.items()}
        valid_idxs = {k: v for k, v in idxs.items() if v is not None}
        if not valid_idxs:
            self.preview_table.setColumnCount(0)
            self.preview_table.setRowCount(0)
            return
        cols = list(valid_idxs.keys())
        self.preview_table.setColumnCount(len(cols))
        self.preview_table.setHorizontalHeaderLabels([c.upper() for c in cols])
        self.preview_table.setRowCount(len(data))
        for r, (_, row) in enumerate(data.iterrows()):
            for c, col_name in enumerate(cols):
                idx = idxs[col_name]
                if idx is not None and idx < len(row):
                    val = str(row.iloc[idx]) if pd.notna(row.iloc[idx]) else ""
                else:
                    val = ""
                self.preview_table.setItem(r, c, QTableWidgetItem(val))
        self.preview_table.resizeColumnsToContents()
    
    def _accept(self):
        self.selected_sheets = [name for name, cb in self.sheet_checkboxes.items() if cb.isChecked()]
        if not self.selected_sheets:
            QMessageBox.warning(self, "Validación", "Seleccione al menos una hoja para procesar.")
            return
        mapping = {
            "clave": self.combo_clave.currentData(),
            "descripcion": self.combo_desc.currentData(),
            "um": self.combo_um.currentData(),
            "precio": self.combo_precio.currentData(),
        }
        missing = [k for k, v in mapping.items() if not v]
        if missing:
            QMessageBox.warning(self, "Validación", f"Seleccione las columnas para: {', '.join(missing)}")
            return
        self.column_mapping = mapping
        self.result_accepted = True
        config = _load_mapping_config()
        config[self.file_name] = {"sheets": self.selected_sheets, "mapping": mapping}
        _save_mapping_config(config)
        self.accept()


# ==========================
# Worker de importación
# ==========================
class ImportWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, path, server, database, table, selected_sheets, column_mapping):
        super().__init__()
        self.path = path
        self.server = server
        self.database = database
        self.table = table
        self.selected_sheets = selected_sheets
        self.column_mapping = column_mapping
    
    def _sniff_proveedor(self, xlsx_path, sheet):
        try:
            df_head = pd.read_excel(xlsx_path, sheet_name=sheet, header=None, nrows=100, dtype=str, keep_default_na=False, na_filter=False)
            _UNIDADES_MEDIDA = {"PZ", "PZA", "PZS", "PIEZA", "PIEZAS", "CJ", "CAJA", "CAJAS", "CT", "CTO", "CIENTO", "CIENTOS",
                                "ML", "MIL", "MILLAR", "RL", "ROLLO", "ROLLOS", "KT", "KIT", "KITS", "JG", "JUEGO", "JUEGOS",
                                "PAQ", "PACK", "PAQUETE", "PK", "BOL", "BOLSA", "BOLSAS", "EA", "ST", "SET", "MT", "METRO", "METROS",
                                "KG", "KILO", "KILOGRAMO", "PAR", "PARES"}
            header_row = _find_header_row(df_head)
            data_start = header_row + 1
            if len(df_head) > data_start:
                data = df_head.iloc[data_start:]
                for col_idx in range(len(data.columns)):
                    col_vals = data.iloc[:, col_idx].dropna().astype(str).str.strip().str.upper()
                    unique_vals = set(col_vals.head(100))
                    matches = unique_vals & _UNIDADES_MEDIDA
                    if len(matches) >= 2:
                        return "herralum"
            if header_row < len(df_head):
                headers = [str(h).strip().lower() if pd.notna(h) else "" for h in df_head.iloc[header_row].tolist()]
                um_keywords = ("um", "unidad", "u.m.", "udm", "medida", "presentacion")
                for h in headers:
                    for kw in um_keywords:
                        if kw in h:
                            return "herralum"
        except Exception:
            pass
        return "profilo"
    
    def run(self):
        try:
            ext = os.path.splitext(self.path)[1].lower()
            self.status.emit("Leyendo archivo...")
            all_results = {}
            total_insertados = 0
            total_actualizados = 0
            total_rechazados = 0
            total_duplicados = 0
            all_rech_logs = []
            
            for sheet_name in self.selected_sheets:
                self.status.emit(f"Procesando hoja: {sheet_name}")
                proveedor = "profilo"
                validos, rechazados = [], []
                
                if ext in (".xlsx", ".xls"):
                    proveedor = self._sniff_proveedor(self.path, sheet_name)
                    self.status.emit(f"Proveedor detectado: {proveedor.upper()}")
                    if proveedor == "herralum":
                        validos, rechazados = parse_excel_herralum(
                            self.path, sheet_name=sheet_name, column_mapping=self.column_mapping
                        )
                    else:
                        validos, rechazados = parse_excel_profilo(self.path, sheet_name=sheet_name)
                elif ext == ".csv":
                    from materiales.herrajes.parsers.parse_csv import parse_csv_generico
                    validos = parse_csv_generico(self.path)
                    rechazados = []
                else:
                    raise ValueError(f"Extensión no soportada: {ext}")
                
                from collections import Counter, defaultdict
                c = Counter([r["clave"] for r in validos])
                dups_claves = [k for k, v in c.items() if v > 1]
                dups_colapsados = sum(v - 1 for v in c.values() if v > 1)
                log_dups = None
                if dups_claves:
                    os.makedirs(r"D:\vah\logs", exist_ok=True)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_dups = rf"D:\vah\logs\duplicados_{proveedor}_{sheet_name}_{ts}.csv"
                    mapa = defaultdict(list)
                    for r in validos:
                        if r["clave"] in dups_claves:
                            mapa[r["clave"]].append(r)
                    with open(log_dups, "w", newline="", encoding="utf-8-sig") as f:
                        wr = csv.writer(f)
                        wr.writerow(["clave", "ocurrencias", "precios", "descripcion_ejemplo", "precio_max"])
                        for k, lst in sorted(mapa.items()):
                            precios = [float(x["precio"]) for x in lst]
                            desc_ej = next((x["descripcion"] for x in lst if str(x["descripcion"]).strip()), "")
                            wr.writerow([k, len(lst), "|".join(f"{p:.2f}" for p in precios), desc_ej, f"{max(precios):.2f}"])
                
                self.status.emit(f"Hoja '{sheet_name}' - {proveedor.upper()} | Válidos: {len(validos)} | Rechazados: {len(rechazados)} | Duplicados: {dups_colapsados}")
                
                db = DBManager(server=self.server, database=self.database, table=self.table)
                self.status.emit(f"Actualizando BD para hoja '{sheet_name}'...")
                insertados, actualizados = db.bulk_upsert_max_precio(validos)
                
                log_rech = None
                if rechazados:
                    os.makedirs(r"D:\vah\logs", exist_ok=True)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_rech = rf"D:\vah\logs\rechazados_{proveedor}_{sheet_name}_{ts}.csv"
                    cols = ["row", "clave", "descripcion", "unidad", "precio", "motivo"]
                    with open(log_rech, "w", newline="", encoding="utf-8-sig") as f:
                        wr = csv.DictWriter(f, fieldnames=cols)
                        wr.writeheader()
                        for r in rechazados:
                            wr.writerow({c: r.get(c, "") for c in cols})
                
                all_results[sheet_name] = {
                    "proveedor": proveedor,
                    "insertados": insertados,
                    "actualizados": actualizados,
                    "rechazados": len(rechazados),
                    "duplicados_colapsados": dups_colapsados,
                    "log": log_rech,
                    "log_dups": log_dups,
                    "rechazados_data": rechazados,
                }
                total_insertados += insertados
                total_actualizados += actualizados
                total_rechazados += len(rechazados)
                total_duplicados += dups_colapsados
                if log_rech:
                    all_rech_logs.append(log_rech)
            
            self.progress.emit(100)
            self.finished.emit({
                "results_by_sheet": all_results,
                "totals": {
                    "insertados": total_insertados,
                    "actualizados": total_actualizados,
                    "rechazados": total_rechazados,
                    "duplicados_colapsados": total_duplicados,
                },
                "logs_rechazados": all_rech_logs,
            })
        except Exception as e:
            self.error.emit(str(e))


# ==========================
# Pantalla principal
# ==========================
class PantallaHerrajes(QMainWindow):
    def __init__(self, db_name: str = "herrajes"):
        super().__init__()
        self.setWindowTitle("VAH - Módulo Herrajes")
        
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
        act_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("Materiales_Herrajes", "operativo", self))
        menu_ayuda.addAction(act_manual_operativo)
        act_manual_tecnico = QAction("Manual Técnico", self)
        act_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("Materiales_Herrajes", "tecnico", self))
        menu_ayuda.addAction(act_manual_tecnico)
        
        for icon_name in ("logo.jpg", "logo.png", "logo_00001.ico"):
            logo_path = get_resource_path(icon_name)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break
        
        self._geom_applied = False
        self._workspace_rect: Optional[QRect] = self._read_workspace_env()
        self.db = DBManager(database="herrajes")
        self.modo = "nuevo"
        self.clave_en_edicion: str | None = None
        
        self._estilos()
        self._ui()
        self._conectar_eventos()
        self._setup_shortcuts()
        self._setup_simple_navigation()
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
    
    def _setup_shortcuts(self):
        def _act(seq: str, slot):
            a = QAction(self)
            a.setShortcut(QKeySequence(seq))
            a.triggered.connect(slot)
            self.addAction(a)
        
        _act("Ctrl+S", self._on_guardar)
        _act("Ctrl+F", lambda: (self.buscar_input.setEnabled(True), self.buscar_input.setFocus(), self.buscar_input.selectAll()))
        _act("Delete", self._modo_eliminar)
        _act("Ctrl+P", self._on_imprimir)
        _act("F5", self._on_refresh)
        _act("Esc", self._on_salir)
    
    def _set_controles_habilitados(self, enabled: bool):
        for b, btn in self.botones.items():
            if b != "Guardar":
                btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setEnabled(enabled)
        self.clave_input.setEnabled(enabled)
        self.descripcion_input.setEnabled(enabled)
        self.precio_input.setEnabled(enabled)
        self.table.setEnabled(enabled)
    
    def _estilos(self):
        self.setStyleSheet(QSS_BASE + """
            QWidget { background-color: #D9E0E7; font-family: Segoe UI; font-size: 10pt; }
            QGroupBox { border: 1px solid #cfd8e3; border-radius: 6px; margin-top: 10px; font-size: 9pt; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;
                               padding: 0 6px; margin-left: 8px; color: #374151; }
            QLineEdit { background: #ffffff; border: 1px solid #cfd8e3; padding: 4px 6px; border-radius: 4px; }
            QLineEdit:focus { border: 2px solid #2563EB; outline: none; }
            QPushButton { background-color: #ffffff; border: 1px solid #cfd8e3; padding: 6px 12px; border-radius: 6px; }
            QPushButton:hover { background-color: #e6eefc; }
            QHeaderView::section { background-color: #1f6feb; color: white; font-weight: bold; border: none; }
        """)
    
    def _ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        if not self.statusBar():
            self.setStatusBar(QStatusBar())
        
        # Datos del Herraje
        datos_group = QGroupBox("Datos del Herraje")
        grid = QGridLayout()
        self.clave_input = NavLineEditSimple()
        self.clave_input.setMaxLength(20)
        self.descripcion_input = NavLineEditSimple()
        self.descripcion_input.setMaxLength(100)
        self.precio_input = NavLineEditSimple()
        self.precio_input.setPlaceholderText("0.00")
        validator = QDoubleValidator(0.00, 9999999.99, 2)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.precio_input.setValidator(validator)
        self.precio_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.clave_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clave_input.setFixedWidth(160)
        self.precio_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.precio_input.setFixedWidth(110)
        self.descripcion_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        grid.addWidget(QLabel("Clave:"), 0, 0)
        grid.addWidget(self.clave_input, 0, 1)
        grid.addWidget(QLabel("Descripción:"), 0, 2)
        grid.addWidget(self.descripcion_input, 0, 3, 1, 5)
        grid.addWidget(QLabel("Precio:"), 0, 8)
        grid.addWidget(self.precio_input, 0, 9)
        grid.setColumnStretch(1, 0)
        for c in (3, 4, 5, 6, 7):
            grid.setColumnStretch(c, 1)
        grid.setColumnStretch(9, 0)
        grid.setColumnMinimumWidth(1, 160)
        grid.setColumnMinimumWidth(9, 110)
        datos_group.setLayout(grid)
        layout.addWidget(datos_group)
        
        # === Botones CRUD principales (visibles con colores) ===
        self.botones = {}
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
        for b in ("Editar", "Eliminar", "Limpiar", "Refresh", "Imprimir", "Salir", "Importar"):
            self.botones[b].setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Buscar
        buscar_layout = QHBoxLayout()
        buscar_layout.addWidget(QLabel("Buscar por clave:"))
        self.buscar_input = NavLineEditSimple()
        self.buscar_input.setEnabled(False)
        buscar_layout.addWidget(self.buscar_input)
        layout.addLayout(buscar_layout)
        
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["CLAVE", "DESCRIPCIÓN", "PRECIO"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
    
    def _conectar_eventos(self):
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
        self.table.itemDoubleClicked.connect(self._editar_desde_tabla)
    
    def _setup_simple_navigation(self) -> None:
        """Configura el orden de tabulación simple (Enter = Tab)."""
        widgets_en_orden = [
            self.clave_input,
            self.descripcion_input,
            self.precio_input,
            self.botones["Guardar"],
            self.botones["Editar"],
            self.botones["Eliminar"],
            self.botones["Limpiar"],
            self.buscar_input,
            self.table,
        ]
        for anterior, siguiente in zip(widgets_en_orden, widgets_en_orden[1:]):
            self.setTabOrder(anterior, siguiente)
    
    def Inicio(self):
        self.modo = "nuevo"
        self.clave_en_edicion = None
        self.clave_input.clear()
        self.descripcion_input.clear()
        self.precio_input.clear()
        self.buscar_input.clear()
        self.buscar_input.setEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(0)
        self.clave_input.setFocus()
        self.statusBar().showMessage("Pantalla en estado inicial.", 3000)
    
    def _llenar_tabla(self, registros: List[Dict]):
        ordenados = sorted(registros, key=lambda r: (r.get("clave", "") or "").upper())
        self.table.setRowCount(0)
        for r in ordenados:
            row = self.table.rowCount()
            self.table.insertRow(row)
            clave = str(r.get("clave", "") or "")
            desc = str(r.get("descripcion", "") or "")
            try:
                precio = f"{dec2(r.get('precio', '0.00')):.2f}"
            except Exception:
                precio = "0.00"
            for col, val in enumerate([clave, desc, precio]):
                self.table.setItem(row, col, QTableWidgetItem(val))
    
    def _on_guardar(self):
        clave = self.clave_input.text().strip()
        if not clave:
            QMessageBox.warning(self, "Validación", "Debe capturar la clave.")
            return
        descripcion = self.descripcion_input.text().strip()
        if not descripcion:
            QMessageBox.warning(self, "Validación", "Debe capturar la descripción.")
            return
        precio_txt = (self.precio_input.text() or "").strip() or "0.00"
        try:
            precio = dec2(precio_txt)
        except Exception:
            QMessageBox.warning(self, "Validación", "Precio inválido.")
            return
        if precio <= Decimal("0.00"):
            QMessageBox.warning(self, "Validación", "Debe capturar un precio mayor a 0.")
            return
        reg = {"clave": clave, "descripcion": descripcion, "precio": precio}
        try:
            if self.modo == "editar":
                if self.clave_en_edicion is None:
                    QMessageBox.warning(self, "Editar", "No hay registro seleccionado para editar.")
                    return
                if clave != self.clave_en_edicion and self.db.existe_clave(clave):
                    QMessageBox.warning(self, "Duplicidad", f"La clave '{clave}' ya existe.")
                    return
                self.db.actualizar_por_clave(self.clave_en_edicion, reg)
                QMessageBox.information(self, "Editar", "Registro actualizado con éxito")
                self.Inicio()
                return
            if self.db.existe_clave(clave):
                QMessageBox.warning(self, "Duplicidad", f"La clave '{clave}' ya está registrada.")
                return
            self.db.insertar(reg)
            QMessageBox.information(self, "Guardar", "Información guardada con éxito")
            self.Inicio()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No fue posible guardar:\n{e}")
    
    def _modo_editar(self):
        self.modo = "editar"
        self.clave_en_edicion = None
        self.buscar_input.setEnabled(True)
        self.buscar_input.clear()
        self.buscar_input.setFocus()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.statusBar().showMessage("Modo edición activo. Escribe la clave para ver coincidencias.", 4000)
    
    def _editar_desde_tabla(self):
        row = self.table.currentRow()
        if row >= 0:
            self._copiar_fila_a_campos(row)
    
    def _copiar_fila_a_campos(self, row: int):
        self.clave_en_edicion = self.table.item(row, 0).text()
        self.clave_input.setText(self.clave_en_edicion)
        self.descripcion_input.setText(self.table.item(row, 1).text())
        self.precio_input.setText(self.table.item(row, 2).text())
        self.statusBar().showMessage(f"Editando {self.clave_en_edicion}", 3000)
    
    def _modo_eliminar(self):
        if self.modo != "eliminar":
            self.modo = "eliminar"
            self.buscar_input.setEnabled(True)
            self.buscar_input.clear()
            try:
                self._llenar_tabla(self.db.listar_todos())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No fue posible cargar datos:\n{e}")
            self.buscar_input.setFocus()
            self.statusBar().showMessage("Modo eliminar activo. Selecciona y presiona Eliminar para confirmar.", 6000)
            return
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Eliminar", "Selecciona un registro y vuelve a presionar Eliminar.")
            return
        clave = self.table.item(row, 0).text()
        resp = QMessageBox.question(self, "Eliminar", f"¿Seguro que deseas eliminar {clave}?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.db.eliminar_por_clave(clave)
                QMessageBox.information(self, "Eliminar", "Registro eliminado.")
                self.Inicio()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")
    
    def _on_refresh(self):
        self.Inicio()
        self.statusBar().showMessage("Pantalla refrescada (limpia).", 3000)
    
    def _on_importar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "",
                                               "Excel (*.xlsx *.xls);;CSV (*.csv);;Todos (*.*)")
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext in (".xlsx", ".xls"):
            dialog = ImportDialog(path, parent=self)
            if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result_accepted:
                return
            selected_sheets = dialog.selected_sheets
            column_mapping = dialog.column_mapping
        else:
            selected_sheets = [None]
            column_mapping = {}
        
        self._set_controles_habilitados(False)
        progress = QProgressDialog("Preparando importación...", "", 0, 100, self)
        progress.setWindowTitle("Importando...")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            progress.setCancelButton(None)
        except Exception:
            progress.setCancelButtonText("")
        progress.setValue(0)
        progress.show()
        
        self._import_thread = QThread(self)
        self._import_worker = ImportWorker(
            path=path, server=self.db.server, database=self.db.database, table=self.db.table,
            selected_sheets=selected_sheets, column_mapping=column_mapping,
        )
        self._import_worker.moveToThread(self._import_thread)
        self._import_thread.started.connect(self._import_worker.run)
        self._import_worker.progress.connect(progress.setValue)
        self._import_worker.status.connect(progress.setLabelText)
        
        def _cleanup():
            try:
                progress.setValue(100)
                progress.close()
            except Exception:
                pass
            try:
                self._import_thread.quit()
                self._import_thread.wait()
            except Exception:
                pass
            try:
                self._import_worker.deleteLater()
                self._import_thread.deleteLater()
            except Exception:
                pass
            self._import_worker = None
            self._import_thread = None
            self._set_controles_habilitados(True)
        
        def _ok(payload):
            try:
                result = payload if isinstance(payload, dict) else {}
                results_by_sheet = result.get("results_by_sheet", {})
                totals = result.get("totals", {})
                all_rech_logs = result.get("logs_rechazados", [])
                
                # ===== VENTANA DIVISORA PARA RECHAZADOS POR PRECIO_INVALIDO_O_CERO =====
                total_actualizados_extra = 0
                total_rechazados_corregidos = 0
                for sheet, sheet_result in results_by_sheet.items():
                    rechazados_data = sheet_result.get("rechazados_data", [])
                    precio_rech = [r for r in rechazados_data if r.get("motivo") == "precio_invalido_o_cero"]
                    if precio_rech:
                        ventana = VentanaDivisora(precio_rech, parent=self)
                        ventana.exec()
                        if ventana.resultados:
                            actualizar_regs = []
                            for res in ventana.resultados:
                                if res["nuevo_precio"] is not None and res["nuevo_precio"] > 0:
                                    actualizar_regs.append({
                                        "clave": res["clave"],
                                        "descripcion": res["descripcion"],
                                        "precio": float(res["nuevo_precio"]),
                                    })
                                    total_actualizados_extra += 1
                                    total_rechazados_corregidos += 1
                            if actualizar_regs:
                                db_temp = DBManager(
                                    server=self.db.server,
                                    database=self.db.database,
                                    table=self.db.table,
                                )
                                for reg in actualizar_regs:
                                    try:
                                        db_temp.insertar_o_actualizar(reg)
                                    except Exception:
                                        pass
                    sheet_result["rechazados"] = sheet_result["rechazados"] - total_rechazados_corregidos
                    sheet_result["actualizados"] = sheet_result["actualizados"] + total_actualizados_extra
                
                totals["rechazados"] = sum(s["rechazados"] for s in results_by_sheet.values())
                totals["actualizados"] = sum(s["actualizados"] for s in results_by_sheet.values())
                # ===== FIN VENTANA DIVISORA =====
                
                msg_parts = ["✅ Importación completada\n"]
                for sheet, sheet_result in results_by_sheet.items():
                    msg_parts.append(
                        f" Hoja '{sheet}' ({sheet_result.get('proveedor', 'desconocido').upper()}):\n"
                        f"   - Insertados: {sheet_result.get('insertados', 0)}\n"
                        f"   - Actualizados (precio máximo): {sheet_result.get('actualizados', 0)}\n"
                        f"   - Rechazados: {sheet_result.get('rechazados', 0)}\n"
                        f"   - Duplicados colapsados: {sheet_result.get('duplicados_colapsados', 0)}"
                    )
                    if sheet_result.get("log"):
                        msg_parts.append(f"   - Log rechazados: {sheet_result['log']}")
                    msg_parts.append("")
                
                msg_parts.append(
                    f" TOTALES:\n"
                    f"   - Insertados: {totals.get('insertados', 0)}\n"
                    f"   - Actualizados: {totals.get('actualizados', 0)}\n"
                    f"   - Rechazados: {totals.get('rechazados', 0)}\n"
                    f"   - Duplicados colapsados: {totals.get('duplicados_colapsados', 0)}"
                )
                
                # ===== LISTA DE RL PENDIENTES =====
                rl_pendientes = []
                for log_path in all_rech_logs:
                    if log_path and os.path.exists(log_path):
                        try:
                            with open(log_path, "r", encoding="utf-8-sig") as f:
                                reader = csv.DictReader(f)
                                for row in reader:
                                    if row.get("motivo") == "unidad_rl_factor_desconocido":
                                        rl_pendientes.append({
                                            "clave": row.get("clave", ""),
                                            "descripcion": row.get("descripcion", ""),
                                            "precio_lista": row.get("precio", ""),
                                        })
                        except Exception:
                            pass
                
                if rl_pendientes:
                    msg_parts.append("\n" + "=" * 55)
                    msg_parts.append("⚠️  REGISTROS RL PENDIENTES DE CORRECCIÓN MANUAL")
                    msg_parts.append("   (No se encontró factor de conversión en la descripción)")
                    msg_parts.append("=" * 55)
                    for r in rl_pendientes:
                        desc_corta = r['descripcion'][:70] if len(r['descripcion']) > 70 else r['descripcion']
                        msg_parts.append(f"   • {r['clave']} | {desc_corta} | Precio lista: {r['precio_lista']}")
                    msg_parts.append(f"\n   Total RL pendientes: {len(rl_pendientes)}")
                    msg_parts.append("   Corrija manualmente en el archivo Excel o en la base de datos.")
                
                QMessageBox.information(self, "Importación", "\n".join(msg_parts))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un problema al finalizar:\n{e}")
            finally:
                _cleanup()
                self.Inicio()
        
        def _fail(msg: str):
            try:
                QMessageBox.critical(self, "Error", f"No se pudo completar la importación:\n{msg}")
            finally:
                _cleanup()
                self.Inicio()
        
        self._import_worker.finished.connect(_ok)
        self._import_worker.error.connect(_fail)
        self._import_thread.start()
    
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
            QMessageBox.critical(self, "Error", f"No fue posible recuperar datos:\n{e}")
            self.Inicio()
            return
        
        if not registros:
            QMessageBox.warning(self, "Imprimir", "No hay registros para imprimir.")
            self.Inicio()
            return
        
        registros = sorted(registros, key=lambda r: (r.get("clave", "") or "").upper())
        
        if msg.clickedButton() == btn_pantalla:
            self._llenar_tabla(registros)
            return
        
        if msg.clickedButton() == btn_pdf:
            try:
                path = get_pdf_path("Herrajes", "Materiales herrajes.pdf")
                imprimir_pdf_guardar(registros, parent=self, filename=path, title="Materiales herrajes",
                                     page_size="LETTER", orientation="portrait", repeat_header=True,
                                     footer_pattern="Pagina {page}")
                QMessageBox.information(self, "Imprimir", f"PDF generado con éxito:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No fue posible generar el PDF:\n{e}")
            self.Inicio()
            return
        
        if msg.clickedButton() == btn_impresora:
            try:
                try:
                    import win32print, win32api
                except ImportError:
                    QMessageBox.warning(self, "Impresora", "No hay Impresora conectada")
                    self.Inicio()
                    return
                printer_name = win32print.GetDefaultPrinter()
                if not printer_name or "PDF" in (printer_name or "").upper():
                    QMessageBox.warning(self, "Impresora", "No hay Impresora conectada")
                    self.Inicio()
                    return
                temp_pdf = os.path.join(tempfile.gettempdir(), "herrajes_tmp.pdf")
                imprimir_pdf_guardar(registros, parent=None, filename=temp_pdf, title="Materiales herrajes",
                                     page_size="LETTER", orientation="portrait", repeat_header=True,
                                     footer_pattern="Pagina {page}")
                win32api.ShellExecute(0, "print", temp_pdf, None, ".", 0)
                QMessageBox.information(self, "Imprimir", "Documento enviado a la impresora.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No fue posible imprimir:\n{e}")
            self.Inicio()
    
    def _on_salir(self):
        self.close()
    
    def _buscar_dinamico(self):
        if not self.buscar_input.isEnabled():
            return
        prefijo = (self.buscar_input.text() or "").strip().upper()
        try:
            regs = self.db.listar_todos()
            if prefijo:
                regs = [r for r in regs if (r.get("clave", "") or "").upper().startswith(prefijo)]
            self._llenar_tabla(regs)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No fue posible buscar:\n{e}")
    
    def _seleccion_tabla(self):
        if self.modo == "editar":
            row = self.table.currentRow()
            if row >= 0:
                self._copiar_fila_a_campos(row)


# ==================================
# Main
# ==================================
if __name__ == "__main__":
    vah_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.isdir(vah_root) and vah_root not in sys.path:
        sys.path.insert(0, vah_root)
    app = QApplication(sys.argv)
    win = PantallaHerrajes()
    win.show()
    win.raise_()
    win.activateWindow()
    sys.exit(app.exec())
