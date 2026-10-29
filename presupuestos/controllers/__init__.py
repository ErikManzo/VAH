# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/controllers/__init__.py
Paquete de controladores del módulo de presupuestos.

Controladores disponibles:
- PresupuestoController: Gestión de presupuestos y partidas (CRUD, navegación)
- PaquetesController: Lógica de paquetes (carga, actualización, consolidación)
"""

from .presupuesto_controller import PresupuestoController
from .paquetes_controller import PaquetesController

__all__ = [
    'PresupuestoController',
    'PaquetesController',
]