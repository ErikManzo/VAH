# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/__init__.py

Paquete principal del sistema de presupuestos VAH.
"""
import sys
import os
import logging

# Configurar logging básico para que se vean errores de importación
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio actual al path para importaciones absolutas
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Versión del paquete
__version__ = "2.0.0"
__author__ = "Equipo de Desarrollo VAH"
__description__ = "Sistema de Presupuestos para Aluminio y Herrería"

# ============================================================================
# IMPORTACIÓN ROBUSTA DEL MÓDULO PRINCIPAL
# ============================================================================
PresupuestosWindow = None
main = None

# Intento 1: importación absoluta (cuando se ejecuta como script)
try:
    from modulo_presupuestos import PresupuestosWindow as _PresupuestosWindow, main as _main

    PresupuestosWindow = _PresupuestosWindow
    main = _main
    logger.info("Importación exitosa desde modulo_presupuestos (absoluta)")
except ImportError as e:
    logger.debug(f"Importación absoluta falló: {e}")

    # Intento 2: importación relativa (cuando se ejecuta como módulo)
    try:
        from .modulo_presupuestos import PresupuestosWindow as _PresupuestosWindow, main as _main

        PresupuestosWindow = _PresupuestosWindow
        main = _main
        logger.info("Importación exitosa desde .modulo_presupuestos (relativa)")
    except ImportError as e:
        logger.error(f"Importación relativa falló: {e}")

        # Intento 3: importación directa con sys.path (fallback)
        try:
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from modulo_presupuestos import PresupuestosWindow as _PresupuestosWindow, main as _main

            PresupuestosWindow = _PresupuestosWindow
            main = _main
            logger.info("Importación exitosa desde modulo_presupuestos (fallback)")
        except ImportError as e:
            logger.critical(f"No se pudo importar el módulo principal: {e}")


            # Definir clases dummy para que no falle la importación
            class PresupuestosWindow:
                def __init__(self, *args, **kwargs):
                    raise ImportError("No se pudo cargar el módulo principal")


            def main():
                print("Error: No se pudo cargar el módulo principal")
                sys.exit(1)

# ============================================================================
# EXPORTAR CONSTANTES (si es necesario)
# ============================================================================
try:
    from .core import constants
except ImportError:
    try:
        from core import constants
    except ImportError:
        constants = None

__all__ = [
    'PresupuestosWindow',
    'main',
    'constants',
    '__version__',
    '__author__',
    '__description__'
]