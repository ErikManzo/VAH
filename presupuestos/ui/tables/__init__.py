# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/tables/__init__.py
Paquete de tablas especializadas del módulo de presupuestos.

Tablas disponibles:
- TablaPaquetes: Tabla de 6 columnas para paquetes padre
- TablaAnidada: Tabla de 11 columnas para componentes de paquetes
"""

from .paquetes import TablaPaquetes
from .anidada import TablaAnidada

__all__ = [
    'TablaPaquetes',
    'TablaAnidada',
]