# -*- coding: utf-8 -*-
"""
Módulo Concentrador de Materiales - ERP VAH

Propósito: Generar explosión global de materiales a partir de
partidas aceptadas dentro de CXC (Cuentas por Cobrar).

Autor: Arquitecto de Software VAH
Fecha: 03/06/2026
Versión: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "ERP VAH Team"
__description__ = "Concentrador de Materiales - Explosión global desde CXC"

from concentrador_materiales.repositories.cxc_repository import CXCRepository
from concentrador_materiales.repositories.materiales_repository import MaterialesRepository
from concentrador_materiales.repositories.paquetes_repository import PaquetesRepository
from concentrador_materiales.repositories.concentrador_repository import ConcentradorRepository

__all__ = [
    "CXCRepository",
    "MaterialesRepository",
    "PaquetesRepository",
    "ConcentradorRepository",
]