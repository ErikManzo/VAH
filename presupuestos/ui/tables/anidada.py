# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from ...core.constants import A_TIPO, A_COLOR, A_CLAVE, A_DESC, A_CA, A_ANCHO, A_CH, A_ALTO, A_PZAS, A_PU, A_IMP
from ...core.utils import to_float as _f, set_table_money

class TablaAnidada(QTableWidget):
    """
    Tabla que muestra los componentes del paquete actual (11 columnas).
    Solo visual, no edición directa.
    """
    def __init__(self, parent=None):
        super().__init__(0, 11, parent)
        self.setHorizontalHeaderLabels([
            "Tipo", "Color", "Clave", "Descripción", "Cant. Ancho",
            "Ancho", "Cant. Alto", "Alto", "Piezas", "P.U.", "Importe"
        ])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSizePolicy(self.sizePolicy().Policy.Expanding, self.sizePolicy().Policy.Expanding)

    def limpiar(self):
        """Elimina todas las filas."""
        self.setRowCount(0)

    def agregar_componente(self, componente: dict, ancho_original: float, alto_original: float,
                            color: str, editable: bool = False):
        """
        Agrega una fila con los datos del componente.
        componente debe contener: tipo, clave, descripcion, cantidad_base, horizontal, vertical
        """
        row = self.rowCount()
        self.insertRow(row)

        # Tipo
        item = QTableWidgetItem(componente["tipo"])
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, A_TIPO, item)

        # Color
        item = QTableWidgetItem(color)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, A_COLOR, item)

        # Clave
        item = QTableWidgetItem(componente["clave"])
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, A_CLAVE, item)

        # Descripción
        item = QTableWidgetItem(componente["descripcion"])
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, A_DESC, item)

        # Cant. Ancho (horizontal)
        item = QTableWidgetItem(f"{componente.get('horizontal', 1.0):.0f}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, A_CA, item)

        # Ancho (original)
        item = QTableWidgetItem(f"{ancho_original:.2f}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setData(Qt.ItemDataRole.UserRole, ancho_original)
        self.setItem(row, A_ANCHO, item)

        # Cant. Alto (vertical)
        item = QTableWidgetItem(f"{componente.get('vertical', 1.0):.0f}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, A_CH, item)

        # Alto (original)
        item = QTableWidgetItem(f"{alto_original:.2f}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setData(Qt.ItemDataRole.UserRole, alto_original)
        self.setItem(row, A_ALTO, item)

        # Piezas (cantidad base)
        item = QTableWidgetItem(f"{componente['cantidad_base']}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, A_PZAS, item)

        # P.U. e Importe (se actualizarán después)
        self.setItem(row, A_PU, QTableWidgetItem("0.00"))
        self.setItem(row, A_IMP, QTableWidgetItem("0.00"))

    def obtener_componentes(self) -> list:
        """Devuelve lista de diccionarios con los datos de todas las filas."""
        componentes = []
        for r in range(self.rowCount()):
            comp = {
                "tipo": self.item(r, A_TIPO).text() if self.item(r, A_TIPO) else "",
                "color": self.item(r, A_COLOR).text() if self.item(r, A_COLOR) else "",
                "clave": self.item(r, A_CLAVE).text() if self.item(r, A_CLAVE) else "",
                "descripcion": self.item(r, A_DESC).text() if self.item(r, A_DESC) else "",
                "ca": _f(self.item(r, A_CA).text() if self.item(r, A_CA) else "1", 1.0),
                "ancho": _f(self.item(r, A_ANCHO).text() if self.item(r, A_ANCHO) else "0", 0.0),
                "ch": _f(self.item(r, A_CH).text() if self.item(r, A_CH) else "1", 1.0),
                "alto": _f(self.item(r, A_ALTO).text() if self.item(r, A_ALTO) else "0", 0.0),
                "piezas": _f(self.item(r, A_PZAS).text() if self.item(r, A_PZAS) else "1", 1.0),
                "pu": _f(self.item(r, A_PU).text() if self.item(r, A_PU) else "0", 0.0),
                "importe": _f(self.item(r, A_IMP).text() if self.item(r, A_IMP) else "0", 0.0)
            }
            componentes.append(comp)
        return componentes

    def actualizar_con_piezas(self, factor: float):
        """Multiplica las cantidades de piezas por el factor y recalcula."""
        for r in range(self.rowCount()):
            item_pzas = self.item(r, A_PZAS)
            if item_pzas:
                valor_base = _f(item_pzas.text(), 1.0)
                nuevo = valor_base * factor
                item_pzas.setText(f"{nuevo}")
                # Aquí se podría recalcular el importe si se desea