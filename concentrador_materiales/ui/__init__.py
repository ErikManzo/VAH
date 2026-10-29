# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Interfaz de Usuario del Módulo Concentrador de Materiales

Componentes:
- PantallaConcentrador: Ventana principal
- FiltrosDialog: Diálogo de filtros
- AdvertenciasDialog: Lista de advertencias/errores
- DetalleMaterialDialog: Trazabilidad del material
- ProgresoDialog: Barra de progreso durante procesamiento
- TablaMateriales: Widget de tabla personalizada
"""

from concentrador_materiales.ui.pantalla_concentrador import PantallaConcentrador
from concentrador_materiales.ui.dialogs.filtros_dialog import FiltrosDialog
from concentrador_materiales.ui.dialogs.advertencias_dialog import AdvertenciasDialog
from concentrador_materiales.ui.dialogs.detalle_material_dialog import DetalleMaterialDialog
from concentrador_materiales.ui.dialogs.progreso_dialog import ProgresoDialog, ConcentradorThread
from concentrador_materiales.ui.widgets.tabla_materiales import TablaMateriales
from concentrador_materiales.ui.widgets.barra_estado import BarraEstado

__all__ = [
    "PantallaConcentrador",
    "FiltrosDialog",
    "AdvertenciasDialog",
    "DetalleMaterialDialog",
    "ProgresoDialog",
    "ConcentradorThread",
    "TablaMateriales",
    "BarraEstado",
]