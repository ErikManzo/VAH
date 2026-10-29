# -*- coding: utf-8 -*-
r"""
D:\vah\principal\__init__.py

Este archivo convierte el directorio 'principal' en un paquete Python.
Permite importar componentes desde otras partes del ERP si fuera necesario.

Exporta la clase principal MainWindow para facilitar su uso desde otros módulos.
"""

from __future__ import annotations

# Importar la clase principal para que esté disponible al hacer:
# from principal import MainWindow
from principal.pantalla_principal import MainWindow

# También exponer la función launch_unique si se necesita lanzar módulos desde aquí
from principal.pantalla_principal import launch_unique, get_app_root, VAH_ROOT

__all__ = [
    "MainWindow",
    "launch_unique",
    "get_app_root",
    "VAH_ROOT",
]