# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/models/__init__.py
Paquete de modelos de dominio del módulo de presupuestos.

Modelos disponibles:
- ComponentePaquete: Componente individual dentro de un paquete
- Paquete: Paquete padre (mostrado en tabla de paquetes)
"""

from .paquete import ComponentePaquete, Paquete

__all__ = [
    'ComponentePaquete',
    'Paquete',
]