# -*- coding: utf-8 -*-
"""
Modelos del Módulo Concentrador de Materiales

Clases exportadas:
- MaterialConcentrado: Representa un material concentrado
- ReporteConcentrado: Resumen ejecutivo de la concentración
- TipoMaterial: Enumeración de tipos de almacén
- TipoPaquete: Enumeración de tipos de paquete
- OrigenMaterial: Origen del material (DIRECTO/PAQUETE)
"""

from concentrador_materiales.models.concentrado import (
    MaterialConcentrado,
    ReporteConcentrado
)
from concentrador_materiales.models.tipos import (
    TipoMaterial,
    TipoPaquete,
    OrigenMaterial
)

__all__ = [
    "MaterialConcentrado",
    "ReporteConcentrado",
    "TipoMaterial",
    "TipoPaquete",
    "OrigenMaterial",
]