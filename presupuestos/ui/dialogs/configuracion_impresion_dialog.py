# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/configuracion_impresion_dialog.py
Diálogo para configurar descuento e IVA antes de imprimir.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QDoubleSpinBox, QDialogButtonBox,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

import sys
import os

# Asegurar path para importaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from presupuestos.core.constants import ICON_PATH
except ImportError:
    ICON_PATH = None


class ConfiguracionImpresionDialog(QDialog):
    """
    Diálogo para configurar descuento e IVA antes de imprimir/vista previa.
    Emite la señal 'configuracion_aceptada' con los valores configurados.
    """

    configuracion_aceptada = pyqtSignal(dict)

    def __init__(self, descuento_actual: float = 0.0, iva_actual: float = 16.0, parent=None):
        super().__init__(parent)
        self.descuento_actual = descuento_actual
        self.iva_actual = iva_actual
        self.guardar_en_bd = False

        self.setWindowTitle("Configuración de Impresión")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(280)

        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self._build_ui()
        self._setup_connections()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Grupo: Valores de Cálculo
        group_box = QGroupBox("Valores para el Cálculo")
        form_layout = QFormLayout(group_box)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        # Descuento
        self.sp_descuento = QDoubleSpinBox()
        self.sp_descuento.setRange(0.0, 100.0)
        self.sp_descuento.setDecimals(2)
        self.sp_descuento.setSingleStep(1.0)
        self.sp_descuento.setSuffix(" %")
        self.sp_descuento.setValue(self.descuento_actual)
        self.sp_descuento.setToolTip("Porcentaje de descuento a aplicar sobre el subtotal")
        form_layout.addRow("Descuento:", self.sp_descuento)

        # IVA
        self.sp_iva = QDoubleSpinBox()
        self.sp_iva.setRange(0.0, 100.0)
        self.sp_iva.setDecimals(2)
        self.sp_iva.setSingleStep(1.0)
        self.sp_iva.setSuffix(" %")
        self.sp_iva.setValue(self.iva_actual)
        self.sp_iva.setToolTip("Porcentaje de IVA a aplicar")
        form_layout.addRow("IVA:", self.sp_iva)

        main_layout.addWidget(group_box)

        # Grupo: Opciones
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)

        self.chk_guardar = QCheckBox("Guardar descuento en el presupuesto")
        self.chk_guardar.setToolTip(
            "Si se activa, el descuento se guardará en la base de datos\n"
            "y se usará por defecto en futuras impresiones."
        )
        options_layout.addWidget(self.chk_guardar)

        # Etiqueta informativa
        info_label = QLabel(
            "Nota: El descuento se aplica sobre el SUBTOTAL "
            "(después de MO + ACC + Desperdicio + F.V.)"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        options_layout.addWidget(info_label)

        main_layout.addWidget(options_group)

        # Botones
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_aceptar)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _setup_connections(self):
        self.chk_guardar.toggled.connect(self._on_guardar_toggled)

    def _on_guardar_toggled(self, checked: bool):
        self.guardar_en_bd = checked

    def _on_aceptar(self):
        config = {
            'descuento': self.sp_descuento.value(),
            'iva': self.sp_iva.value(),
            'guardar_en_bd': self.guardar_en_bd
        }
        self.configuracion_aceptada.emit(config)
        self.accept()

    def get_descuento(self) -> float:
        return self.sp_descuento.value()

    def get_iva(self) -> float:
        return self.sp_iva.value()

    def get_guardar_en_bd(self) -> bool:
        return self.guardar_en_bd