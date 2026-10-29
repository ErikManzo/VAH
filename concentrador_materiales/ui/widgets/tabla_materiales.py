# -*- coding: utf-8 -*-
"""
Widget de tabla personalizada para materiales concentrados
"""

from typing import List, Optional
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal

from concentrador_materiales.models.concentrado import MaterialConcentrado
from concentrador_materiales.ui.recursos import TAMANIO_COLUMNAS


from common.logger_config import get_logger
logger = get_logger('concentrador.ui.widgets.tabla_materiales')

class TablaMateriales(QTableWidget):
    """
    Tabla personalizada para mostrar materiales concentrados.
    Emite señal cuando se hace doble clic en una fila.
    """

    fila_doble_clic = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.columnas = []
        self.setup_ui()

    def setup_ui(self):
        """Configura la apariencia de la tabla."""
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.itemDoubleClicked.connect(self._on_item_double_click)

    def _on_item_double_click(self, item):
        """Maneja doble clic en una fila."""
        row = item.row()
        material = self.item_data(row)
        if material:
            self.fila_doble_clic.emit(material)

    def item_data(self, row: int) -> Optional[MaterialConcentrado]:
        """Obtiene el MaterialConcentrado asociado a una fila."""
        item = self.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _obtener_valor(self, material: MaterialConcentrado, campo: str):
        """Obtiene el valor de un campo del material."""
        if campo == "dimensiones" and material.ancho_original and material.alto_original:
            return f"{material.ancho_original:.2f}×{material.alto_original:.2f}"
        if campo == "largo_tramo":
            return material.largo_tramo
        return getattr(material, campo, None)

    def _formatear_valor(self, valor, formato: str, unidad: str) -> str:
        """Formatea un valor según el formato especificado."""
        if valor is None:
            return ""
        if formato == "int":
            return f"{int(valor)}{' ' + unidad if unidad else ''}"
        elif formato == "decimal_2":
            return f"{float(valor):.2f}{' ' + unidad if unidad else ''}"
        elif formato == "decimal_3":
            return f"{float(valor):.3f}{' ' + unidad if unidad else ''}"
        else:
            return f"{valor}{' ' + unidad if unidad else ''}"

    def cargar_materiales(self, materiales: List[MaterialConcentrado], columnas: List[dict]):
        """
        Carga una lista de materiales en la tabla.

        Args:
            materiales: Lista de MaterialConcentrado
            columnas: Lista de diccionarios con definición de columnas
        """
        self.columnas = columnas
        self.setRowCount(0)

        if not materiales:
            return

        # Configurar columnas
        self.setColumnCount(len(columnas))
        for col, col_def in enumerate(columnas):
            self.setHorizontalHeaderItem(col, QTableWidgetItem(col_def["titulo"]))
            ancho = col_def.get("ancho", TAMANIO_COLUMNAS.get(col_def["campo"].upper(), 100))
            self.setColumnWidth(col, ancho)

        # Llenar filas
        for row, material in enumerate(materiales):
            self.insertRow(row)

            for col, col_def in enumerate(columnas):
                valor = self._obtener_valor(material, col_def["campo"])
                texto = self._formatear_valor(
                    valor,
                    col_def.get("formato", ""),
                    col_def.get("unidad", "")
                )

                item = QTableWidgetItem(texto)
                item.setData(Qt.ItemDataRole.UserRole, material)

                # Alinear números a la derecha
                if isinstance(valor, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # Negrita para la unidad principal
                if col_def.get("negrita", False):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.setItem(row, col, item)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)