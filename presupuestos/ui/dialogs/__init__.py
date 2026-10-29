# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/__init__.py
Paquete de diálogos modales del módulo de presupuestos.

Diálogos disponibles:
- AbrirPresupuestoDialog: Búsqueda y selección de presupuestos existentes
- ParametrosSistemaDialog: Configuración de correo y parámetros
- NotasPresupuestoDialog: Configuración de notas, forma de pago, plazo de entrega
- EnviarCorreoDialog: Envío de presupuesto por correo
- EditarCorreoClienteDialog: Edición de correo del cliente
"""

from .abrir_presupuesto_dialog import AbrirPresupuestoDialog

# Nuevos diálogos
from .parametros_sistema_dialog import ParametrosSistemaDialog
from .notas_presupuesto_dialog import NotasPresupuestoDialog
from .enviar_correo_dialog import EnviarCorreoDialog
from .editar_correo_cliente_dialog import EditarCorreoClienteDialog

__all__ = [
    'AbrirPresupuestoDialog',
    'ParametrosSistemaDialog',
    'NotasPresupuestoDialog',
    'EnviarCorreoDialog',
    'EditarCorreoClienteDialog'
]