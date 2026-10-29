# -*- coding: utf-8 -*-
"""
Diálogo de detalle de material - Muestra trazabilidad completa
"""

from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox
)
from PyQt6.QtGui import QFont

from concentrador_materiales.models.concentrado import MaterialConcentrado


from common.logger_config import get_logger
logger = get_logger('concentrador.ui.dialogs.detalle_material')

class DetalleMaterialDialog(QDialog):
    """
    Diálogo que muestra toda la información y trazabilidad de un material.
    """

    def __init__(self, material: MaterialConcentrado, parent=None):
        super().__init__(parent)
        self.material = material
        self.setWindowTitle(f"Detalle del material - {material.clave}")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        """Construye la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        # Información general
        gb_general = QGroupBox("INFORMACIÓN GENERAL")
        grid_general = QGridLayout(gb_general)

        grid_general.addWidget(QLabel("Clave:"), 0, 0)
        grid_general.addWidget(QLabel(self.material.clave), 0, 1)
        grid_general.addWidget(QLabel("Descripción:"), 1, 0)
        grid_general.addWidget(QLabel(self.material.descripcion), 1, 1)
        grid_general.addWidget(QLabel("Almacén:"), 2, 0)
        grid_general.addWidget(QLabel(self.material.almacen), 2, 1)
        grid_general.addWidget(QLabel("Origen:"), 3, 0)

        origen_texto = self.material.origen
        if origen_texto == "PAQUETE":
            origen_texto = "📦 PAQUETE"
        else:
            origen_texto = "📄 DIRECTO"
        grid_general.addWidget(QLabel(origen_texto), 3, 1)

        layout.addWidget(gb_general)

        # Cantidades
        gb_cantidades = QGroupBox("CANTIDADES")
        grid_cantidades = QGridLayout(gb_cantidades)

        row = 0
        grid_cantidades.addWidget(QLabel("Cantidad CXC original:"), row, 0)
        grid_cantidades.addWidget(QLabel(f"{self.material.cantidad_cxc_original:.2f} piezas"), row, 1)

        row += 1
        if self.material.metros_totales is not None:
            grid_cantidades.addWidget(QLabel("Metros totales:"), row, 0)
            grid_cantidades.addWidget(QLabel(f"{self.material.metros_totales:.2f} m"), row, 1)
            row += 1

        if self.material.m2_totales is not None:
            grid_cantidades.addWidget(QLabel("Metros cuadrados totales:"), row, 0)
            grid_cantidades.addWidget(QLabel(f"{self.material.m2_totales:.2f} m²"), row, 1)
            row += 1

        if self.material.kilogramos_totales is not None:
            grid_cantidades.addWidget(QLabel("Kilogramos totales (costeo):"), row, 0)
            grid_cantidades.addWidget(QLabel(f"{self.material.kilogramos_totales:.2f} kg"), row, 1)
            row += 1

        if self.material.tramos_calculados is not None:
            grid_cantidades.addWidget(QLabel("Tramos requeridos:"), row, 0)
            tramos_text = f"{self.material.tramos_calculados} tramos"
            if self.material.almacen == "HERRERIA":
                tramos_text += " (6m c/u)"
            grid_cantidades.addWidget(QLabel(tramos_text), row, 1)
            row += 1

        if self.material.hojas_calculadas is not None:
            grid_cantidades.addWidget(QLabel("Hojas requeridas:"), row, 0)
            grid_cantidades.addWidget(QLabel(f"{self.material.hojas_calculadas} hojas"), row, 1)
            row += 1

        layout.addWidget(gb_cantidades)

        # Dimensiones originales
        if self.material.ancho_original or self.material.alto_original:
            gb_dimensiones = QGroupBox("DIMENSIONES ORIGINALES")
            grid_dim = QGridLayout(gb_dimensiones)

            grid_dim.addWidget(QLabel("Ancho:"), 0, 0)
            grid_dim.addWidget(QLabel(f"{self.material.ancho_original or 0:.2f} m"), 0, 1)
            grid_dim.addWidget(QLabel("Alto:"), 1, 0)
            grid_dim.addWidget(QLabel(f"{self.material.alto_original or 0:.2f} m"), 1, 1)

            if self.material.ca_original:
                grid_dim.addWidget(QLabel("CA (Cant. Ancho):"), 2, 0)
                grid_dim.addWidget(QLabel(f"{self.material.ca_original:.0f}"), 2, 1)
            if self.material.ch_original:
                grid_dim.addWidget(QLabel("CH (Cant. Alto):"), 3, 0)
                grid_dim.addWidget(QLabel(f"{self.material.ch_original:.0f}"), 3, 1)

            layout.addWidget(gb_dimensiones)

        # Trazabilidad
        gb_trazabilidad = QGroupBox("TRAZABILIDAD")
        grid_traz = QGridLayout(gb_trazabilidad)

        grid_traz.addWidget(QLabel("Presupuesto ID:"), 0, 0)
        grid_traz.addWidget(QLabel(str(self.material.presupuesto_id)), 0, 1)
        grid_traz.addWidget(QLabel("Partida ID:"), 1, 0)
        grid_traz.addWidget(QLabel(str(self.material.partida_id)), 1, 1)
        grid_traz.addWidget(QLabel("CXC ID:"), 2, 0)
        grid_traz.addWidget(QLabel(str(self.material.cxc_id)), 2, 1)
        grid_traz.addWidget(QLabel("Tipo original:"), 3, 0)
        grid_traz.addWidget(QLabel(self.material.tipo_original), 3, 1)

        layout.addWidget(gb_trazabilidad)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cerrar)
        layout.addLayout(btn_layout)