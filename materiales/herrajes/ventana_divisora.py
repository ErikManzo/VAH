# D:\vah\materiales\herrajes\ventana_divisora.py
# -*- coding: utf-8 -*-
"""
Ventana auxiliar para ingresar la cantidad divisora de registros rechazados
por precio_invalido_o_cero.
"""

from typing import List, Dict, Optional
from decimal import Decimal, localcontext, InvalidOperation, ROUND_HALF_UP
from PyQt6.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QHBoxLayout, QPushButton, QHeaderView, QLabel, QMessageBox,
)
from PyQt6.QtCore import Qt

_DEC2 = Decimal("0.01")


class VentanaDivisora(QDialog):
    """
    Diálogo que muestra los registros rechazados por precio_invalido_o_cero
    y permite al usuario ingresar una cantidad divisora para calcular el precio unitario.
    """

    def __init__(self, rechazados: List[Dict], parent=None):
        """
        Args:
            rechazados: Lista de dicts con keys: clave, descripcion, precio (original), unidad, row
        """
        super().__init__(parent)
        self.setWindowTitle("Cantidad divisora para registros rechazados")
        self.setMinimumSize(850, 500)
        self.rechazados = rechazados
        self.resultados: Optional[List[Dict]] = None  # Será llenado al aceptar o cancelar

        self._ui()

    def _ui(self):
        layout = QVBoxLayout(self)

        # Etiqueta superior
        lbl = QLabel(
            "Los siguientes registros fueron rechazados por tener precio inválido o cero.\n"
            "Ingrese la <b>cantidad divisora</b> para calcular el precio unitario:\n"
            "<tt>Precio unitario = Precio original / Cantidad divisora</tt>"
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        # Tabla
        self.tabla = QTableWidget(len(self.rechazados), 5)
        self.tabla.setHorizontalHeaderLabels([
            "Clave", "Descripción", "Unidad", "Precio original", "Cantidad divisora"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        for i, item in enumerate(self.rechazados):
            clave = str(item.get("clave", "") or "")
            desc = str(item.get("descripcion", "") or "")
            unidad = str(item.get("unidad", "") or "")
            precio_str = str(item.get("precio", "") or "")

            # Intentar formatear el precio si es un número
            try:
                precio_val = float(precio_str.replace("$", "").replace(",", ""))
                precio_display = f"{precio_val:,.2f}"
            except Exception:
                precio_display = precio_str

            self.tabla.setItem(i, 0, QTableWidgetItem(clave))
            self.tabla.setItem(i, 1, QTableWidgetItem(desc))
            self.tabla.setItem(i, 2, QTableWidgetItem(unidad))
            self.tabla.setItem(i, 3, QTableWidgetItem(precio_display))

            # Columnas 0-3: solo lectura
            for col in range(4):
                item_widget = self.tabla.item(i, col)
                if item_widget:
                    item_widget.setFlags(item_widget.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Columna 4: editable (cantidad divisora)
            cantidad_item = QTableWidgetItem("")
            cantidad_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.tabla.setItem(i, 4, cantidad_item)

        layout.addWidget(self.tabla)

        # Botones
        botones_layout = QHBoxLayout()
        btn_aceptar = QPushButton("✅ Aceptar y calcular precios")
        btn_aceptar.setStyleSheet("QPushButton { background-color: #d4edda; } QPushButton:hover { background-color: #c3e6cb; }")
        btn_cancelar = QPushButton("❌ Cancelar (dejar sin precio)")
        btn_cancelar.setStyleSheet("QPushButton { background-color: #f8d7da; } QPushButton:hover { background-color: #f5c6cb; }")
        btn_aceptar.clicked.connect(self._aceptar)
        btn_cancelar.clicked.connect(self._cancelar)
        botones_layout.addWidget(btn_aceptar)
        botones_layout.addWidget(btn_cancelar)
        layout.addLayout(botones_layout)

    def _calcular_precio(self, precio_original_str: str, cantidad_divisora: float) -> Optional[Decimal]:
        """Calcula precio unitario = precio_original / cantidad_divisora"""
        try:
            # Limpiar precio original
            txt = precio_original_str.replace("$", "").replace(" ", "").replace(",", "")
            precio_original = float(txt)
        except Exception:
            return None

        if precio_original <= 0 or cantidad_divisora <= 0:
            return None

        with localcontext() as ctx:
            ctx.traps[InvalidOperation] = False
            try:
                d = Decimal(str(precio_original)) / Decimal(str(cantidad_divisora))
                d = d.quantize(_DEC2, rounding=ROUND_HALF_UP)
                return d if d > 0 else None
            except Exception:
                return None

    def _aceptar(self):
        self.resultados = []
        todos_vacios = True
        for i, item in enumerate(self.rechazados):
            cantidad_item = self.tabla.item(i, 4)
            cantidad_texto = cantidad_item.text().strip() if cantidad_item else ""

            if cantidad_texto == "":
                # No se ingresó cantidad -> dejar sin precio
                self.resultados.append({
                    "clave": item.get("clave", ""),
                    "descripcion": item.get("descripcion", ""),
                    "nuevo_precio": None,
                })
            else:
                todos_vacios = False
                try:
                    cantidad = float(cantidad_texto)
                    nuevo_precio = self._calcular_precio(
                        str(item.get("precio", "") or ""), cantidad
                    )
                    self.resultados.append({
                        "clave": item.get("clave", ""),
                        "descripcion": item.get("descripcion", ""),
                        "nuevo_precio": nuevo_precio,
                    })
                except ValueError:
                    QMessageBox.warning(
                        self, "Valor inválido",
                        f"La cantidad divisora para '{item.get('clave', '')}' no es un número válido.\n"
                        f"Corríjala o déjela vacía para omitir este registro."
                    )
                    return

        if todos_vacios:
            resp = QMessageBox.question(
                self, "Confirmar",
                "No ingresó ninguna cantidad divisora.\n"
                "Todos estos registros quedarán sin precio (0.00).\n\n"
                "¿Desea continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp == QMessageBox.StandardButton.No:
                return

        self.accept()

    def _cancelar(self):
        # Todo queda sin precio
        self.resultados = [
            {"clave": item.get("clave", ""), "descripcion": item.get("descripcion", ""), "nuevo_precio": None}
            for item in self.rechazados
        ]
        self.accept()