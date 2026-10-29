# -*- coding: utf-8 -*-
"""
Diálogo para mostrar advertencias y errores del proceso
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QTabWidget, QWidget
)
from PyQt6.QtCore import Qt


from common.logger_config import get_logger
logger = get_logger('concentrador.ui.dialogs.advertencias')

class AdvertenciasDialog(QDialog):
    """
    Diálogo que muestra las advertencias y errores generados durante la concentración.
    """

    def __init__(self, advertencias: List[Dict[str, Any]], errores: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advertencias y Errores")
        self.setModal(True)
        self.setMinimumSize(700, 400)

        self.advertencias = advertencias
        self.errores = errores

        self.setup_ui()

    def setup_ui(self):
        """Construye la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # Pestaña de advertencias
        tab_warnings = QWidget()
        warnings_layout = QVBoxLayout(tab_warnings)

        lbl_warnings = QLabel(f"Total de advertencias: {len(self.advertencias)}")
        lbl_warnings.setStyleSheet("font-weight: bold; color: #e67e22;")
        warnings_layout.addWidget(lbl_warnings)

        self.tabla_warnings = self._crear_tabla()
        self._llenar_tabla(self.tabla_warnings, self.advertencias, "warning")
        warnings_layout.addWidget(self.tabla_warnings)

        # Pestaña de errores
        tab_errors = QWidget()
        errors_layout = QVBoxLayout(tab_errors)

        lbl_errors = QLabel(f"Total de errores: {len(self.errores)}")
        lbl_errors.setStyleSheet("font-weight: bold; color: #e74c3c;")
        errors_layout.addWidget(lbl_errors)

        self.tabla_errores = self._crear_tabla()
        self._llenar_tabla(self.tabla_errores, self.errores, "error")
        errors_layout.addWidget(self.tabla_errores)

        tabs.addTab(tab_warnings, "⚠️ Advertencias")
        tabs.addTab(tab_errors, "❌ Errores")

        layout.addWidget(tabs)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cerrar)
        layout.addLayout(btn_layout)

    def _crear_tabla(self) -> QTableWidget:
        """Crea una tabla para mostrar advertencias/errores."""
        tabla = QTableWidget()
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["Código", "Mensaje", "Datos", "Archivo sugerido"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return tabla

    def _llenar_tabla(self, tabla: QTableWidget, items: List[Dict[str, Any]], tipo: str):
        """Llena la tabla con los items."""
        tabla.setRowCount(len(items))

        for row, item in enumerate(items):
            codigo = item.get("codigo", "")
            mensaje = item.get("mensaje", "")
            datos = item.get("datos", {})

            datos_str = ", ".join(f"{k}={v}" for k, v in datos.items() if v)
            archivo = self._sugerir_archivo(codigo)

            tabla.setItem(row, 0, QTableWidgetItem(codigo))
            tabla.setItem(row, 1, QTableWidgetItem(mensaje))
            tabla.setItem(row, 2, QTableWidgetItem(datos_str[:200]))
            tabla.setItem(row, 3, QTableWidgetItem(archivo))

    def _sugerir_archivo(self, codigo: str) -> str:
        """Sugiere un archivo basado en el código de error."""
        sugerencias = {
            "LARGO_NULO": "materiales_aluminio",
            "COMPONENTE_SIN_LARGO": "materiales_aluminio",
            "CLAVE_HUERFANA": "catálogo correspondiente",
            "TIPO_PAQUETE_DESCONOCIDO": "partida_paquetes",
            "KG_POR_METRO_CERO": "materiales_herreria",
        }
        return sugerencias.get(codigo, "Validar configuración")