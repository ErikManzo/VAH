# -*- coding: utf-8 -*-
"""
Estilos unificados para todo el ERP VAH.
"""

from PyQt6.QtGui import QFont

# Colores (iguales a los usados en Presupuestos)
COLOR_PRIMARIO = "#1f6feb"
COLOR_PRIMARIO_OSCURO = "#1557b0"
COLOR_FONDO_VENTANA = "#f6f8fc"
COLOR_TEXTO = "#1f2937"
COLOR_BOTON_HOVER = "#e6eefc"
COLOR_BORDE = "#cfd8e3"
COLOR_GRIS_CLARO = "#f0f4f8"

# QSS unificado (base)
QSS_BASE = """
QMainWindow, QDialog {
    background: #f6f8fc;
}
QTabWidget::pane {
    border: 0px;
}
QTabBar::tab {
    padding: 6px 12px;
    margin: 2px;
    border-radius: 8px;
    background: #e9edf5;
    color: #1f2937;
}
QTabBar::tab:selected {
    background: white;
    font-weight: 600;
}
QMenu {
    background: #ffffff;
    border: 1px solid #e5e7eb;
}
QMenu::item {
    padding: 6px 24px;
}
QMenu::item:selected {
    background: #e6eefc;
}
QPushButton {
    background: #e9edf5;
    border: 1px solid #cfd8e3;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover {
    background: #dce3ec;
}
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #cfd8e3;
    border-radius: 4px;
    padding: 4px;
}
QTableWidget {
    alternate-background-color: #f9fafb;
    selection-background-color: #e6eefc;
}
"""


def aplicar_estilo(ventana):
    """Aplica el estilo base a una ventana (QMainWindow o QDialog)."""
    ventana.setStyleSheet(QSS_BASE)
    ventana.setFont(QFont("Segoe UI", 9))
