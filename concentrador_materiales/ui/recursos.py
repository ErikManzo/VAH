# -*- coding: utf-8 -*-
"""
Recursos y estilos para la UI del Concentrador de Materiales
"""

# Estilos QSS (basados en el ERP existente)
ESTILO_CONCENTRADOR = """
QWidget {
    background-color: #EEF2F6;
    font-family: Segoe UI;
    font-size: 10pt;
}
QGroupBox {
    border: 1px solid #cfd8e3;
    border-radius: 6px;
    margin-top: 10px;
    font-size: 9pt;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    margin-left: 8px;
    color: #374151;
}
QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #cfd8e3;
    padding: 4px 6px;
    border-radius: 5px;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #2563EB;
    outline: none;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cfd8e3;
    padding: 6px 12px;
    border-radius: 6px;
}
QPushButton:hover {
    background-color: #e6eefc;
}
QHeaderView::section {
    background-color: #1f6feb;
    color: white;
    font-weight: bold;
    border: none;
}
QTableWidget {
    background: #ffffff;
    border: 1px solid #cfd8e3;
    alternate-background-color: #f8f9fc;
}
QTabWidget::pane {
    border: 1px solid #cfd8e3;
    background: #ffffff;
}
QTabBar::tab {
    background: #e9ecef;
    padding: 8px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #1f6feb;
    color: white;
}
QProgressBar {
    border: 1px solid #cfd8e3;
    border-radius: 5px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #1f6feb;
    border-radius: 5px;
}
QStatusBar {
    background-color: #e9ecef;
    border-top: 1px solid #cfd8e3;
}
QLabel#total_label {
    font-weight: bold;
    color: #1f6feb;
}
"""

# Constantes de UI
TAMANIO_COLUMNAS = {
    "CLAVE": 120,
    "DESCRIPCION": 250,
    "METROS": 100,
    "TRAMOS": 100,
    "M2": 100,
    "HOJAS": 100,
    "KILOGRAMOS": 100,
    "PIEZAS": 80,
    "ORIGEN": 100,
    "DIMENSIONES": 120,
    "LARGO": 80,
    "CA": 60,
    "CH": 60,
}

# Textos de tooltips
TOOLTIPS = {
    "clave": "Identificador único del material",
    "descripcion": "Descripción del material",
    "metros": "Metros lineales totales (base para consolidación)",
    "tramos": "Tramos comerciales requeridos (CEIL metros / largo comercial)",
    "origen": "DIRECTO = del catálogo, PAQUETE = componente de paquete",
    "piezas_cxc": "Cantidad original desde CXC (cantidad_facturada)",
    "largo_tramo": "Longitud comercial del tramo (desde catálogo)",
    "dimensiones": "Dimensiones originales: ancho × alto (en metros)",
}