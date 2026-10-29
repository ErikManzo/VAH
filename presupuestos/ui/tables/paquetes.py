# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/tables/paquetes.py
Tabla de paquetes - VERSIÓN FINAL
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import pyqtSignal, Qt
from ...core.constants import P_TIPO, P_CLAVE, P_DESC, P_ANCHO, P_ALTO, P_PZAS


class TablaPaquetes(QTableWidget):
    """
    Tabla que muestra los paquetes padres (6 columnas).
    """
    paqueteAgregado = pyqtSignal(dict)
    piezasCambiadas = pyqtSignal(int, int)
    anchoCambiado = pyqtSignal(int, float)
    altoCambiado = pyqtSignal(int, float)
    paqueteEliminado = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(0, 6, parent)
        self.setHorizontalHeaderLabels(["Tipo", "Clave", "Descripción", "Ancho", "Alto", "Piezas"])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._editando = False
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item):
        if self._editando:
            return

        col = item.column()
        row = item.row()

        if col == P_PZAS:
            try:
                nuevas = int(item.text())
            except ValueError:
                nuevas = 1
                self.blockSignals(True)
                item.setText("1")
                self.blockSignals(False)
            self.piezasCambiadas.emit(row, nuevas)

        elif col == P_ANCHO:
            try:
                nuevo_ancho = float(item.text().replace(",", "."))
            except ValueError:
                nuevo_ancho = 0.0
                self.blockSignals(True)
                item.setText("0.00")
                self.blockSignals(False)
            self.anchoCambiado.emit(row, nuevo_ancho)

        elif col == P_ALTO:
            try:
                nuevo_alto = float(item.text().replace(",", "."))
            except ValueError:
                nuevo_alto = 0.0
                self.blockSignals(True)
                item.setText("0.00")
                self.blockSignals(False)
            self.altoCambiado.emit(row, nuevo_alto)

    def agregar_paquete(self, tipo: str, clave: str, descripcion: str,
                        ancho: float, alto: float, es_anidado: bool = False,
                        padre_clave: str = None) -> int:
        row = self.rowCount()
        self.insertRow(row)
        self.blockSignals(True)

        item_tipo = QTableWidgetItem(tipo)
        if es_anidado:
            item_tipo.setBackground(Qt.GlobalColor.lightGray)
        item_tipo.setFlags(item_tipo.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_tipo.setData(Qt.ItemDataRole.UserRole, {
            "clave": clave, "es_anidado": es_anidado, "padre_clave": padre_clave
        })
        self.setItem(row, P_TIPO, item_tipo)

        item_clave = QTableWidgetItem(clave)
        if es_anidado:
            item_clave.setBackground(Qt.GlobalColor.lightGray)
        item_clave.setFlags(item_clave.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, P_CLAVE, item_clave)

        item_desc = QTableWidgetItem(descripcion)
        if es_anidado:
            item_desc.setBackground(Qt.GlobalColor.lightGray)
        item_desc.setFlags(item_desc.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, P_DESC, item_desc)

        item_ancho = QTableWidgetItem(f"{ancho:.2f}")
        item_ancho.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if es_anidado:
            item_ancho.setFlags(item_ancho.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_ancho.setBackground(Qt.GlobalColor.lightGray)
        else:
            item_ancho.setBackground(Qt.GlobalColor.yellow)
        self.setItem(row, P_ANCHO, item_ancho)

        item_alto = QTableWidgetItem(f"{alto:.2f}")
        item_alto.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if es_anidado:
            item_alto.setFlags(item_alto.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_alto.setBackground(Qt.GlobalColor.lightGray)
        else:
            item_alto.setBackground(Qt.GlobalColor.yellow)
        self.setItem(row, P_ALTO, item_alto)

        item_pzas = QTableWidgetItem("1")
        item_pzas.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if es_anidado:
            item_pzas.setFlags(item_pzas.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_pzas.setBackground(Qt.GlobalColor.lightGray)
        else:
            item_pzas.setBackground(Qt.GlobalColor.yellow)
        self.setItem(row, P_PZAS, item_pzas)

        self.blockSignals(False)

        self.paqueteAgregado.emit({
            "fila": row,
            "tipo": tipo,
            "clave": clave,
            "descripcion": descripcion,
            "ancho": ancho,
            "alto": alto,
            "piezas": 1,
            "es_anidado": es_anidado,
            "padre_clave": padre_clave
        })
        return row

    def removeRow(self, row):
        super().removeRow(row)  # Primero eliminar la fila
        self.paqueteEliminado.emit(row)  # Luego emitir la señal

    def obtener_datos_paquete(self, fila: int) -> dict:
        item_tipo = self.item(fila, P_TIPO)
        user_data = item_tipo.data(Qt.ItemDataRole.UserRole) if item_tipo else {}

        item_pzas = self.item(fila, P_PZAS)
        piezas = 1
        if item_pzas:
            try:
                piezas = int(item_pzas.text())
            except ValueError:
                piezas = 1

        item_ancho = self.item(fila, P_ANCHO)
        ancho = 0.0
        if item_ancho:
            try:
                ancho = float(item_ancho.text().replace(",", "."))
            except ValueError:
                ancho = 0.0

        item_alto = self.item(fila, P_ALTO)
        alto = 0.0
        if item_alto:
            try:
                alto = float(item_alto.text().replace(",", "."))
            except ValueError:
                alto = 0.0

        return {
            "tipo": self.item(fila, P_TIPO).text() if self.item(fila, P_TIPO) else "",
            "clave": self.item(fila, P_CLAVE).text() if self.item(fila, P_CLAVE) else "",
            "descripcion": self.item(fila, P_DESC).text() if self.item(fila, P_DESC) else "",
            "ancho": ancho,
            "alto": alto,
            "piezas": piezas,
            "es_anidado": user_data.get("es_anidado", False) if user_data else False,
            "padre_clave": user_data.get("padre_clave") if user_data else None
        }

    def set_piezas_sin_senal(self, fila: int, piezas: int):
        self._editando = True
        item = self.item(fila, P_PZAS)
        if item:
            item.setText(str(piezas))
        self._editando = False

    def set_ancho_sin_senal(self, fila: int, ancho: float):
        self._editando = True
        item = self.item(fila, P_ANCHO)
        if item:
            item.setText(f"{ancho:.2f}")
        self._editando = False

    def set_alto_sin_senal(self, fila: int, alto: float):
        self._editando = True
        item = self.item(fila, P_ALTO)
        if item:
            item.setText(f"{alto:.2f}")
        self._editando = False