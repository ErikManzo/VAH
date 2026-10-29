# -*- coding: utf-8 -*-
import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDoubleSpinBox,
    QDialogButtonBox
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from presupuestos.core.constants import ICON_PATH


class _BaseEditarValorGlobalDialog(QDialog):
    def __init__(self, titulo: str, mensaje: str, valor_actual: float,
                 minimo: float, maximo: float, decimales: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(420)

        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        layout = QVBoxLayout(self)

        lbl_msg = QLabel(mensaje)
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg)

        self.sp_valor = QDoubleSpinBox(self)
        self.sp_valor.setRange(minimo, maximo)
        self.sp_valor.setDecimals(decimales)
        self.sp_valor.setValue(float(valor_actual))
        self.sp_valor.setSuffix(" %")
        layout.addWidget(self.sp_valor)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar a todas las partidas")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_valor(self) -> float:
        return float(self.sp_valor.value())


class EditarDesperdicioDialog(_BaseEditarValorGlobalDialog):
    def __init__(self, valor_actual: float, parent=None):
        super().__init__(
            "Editar Desperdicio Global del Presupuesto",
            "Este cambio afectará a TODAS las partidas del presupuesto actual.",
            valor_actual,
            0.0,
            100.0,
            2,
            parent,
        )


class EditarFVDialog(_BaseEditarValorGlobalDialog):
    def __init__(self, valor_actual: float, parent=None):
        super().__init__(
            "Editar Factor de Venta Global del Presupuesto",
            "Este cambio afectará a TODAS las partidas del presupuesto actual.",
            valor_actual,
            0.0,
            1000.0,
            2,
            parent,
        )
