# -*- coding: utf-8 -*-
"""
Servicios del Módulo Concentrador de Materiales

Clases exportadas:
- MapeadorTipos: Normalización de tipos en memoria
- ExplosorBase: Clase abstracta para explosores
- ExplosorAluminio: Explosión de materiales aluminio
- ExplosorHerreria: Explosión de materiales herrería
- ExplosorHerrajes: Explosión de materiales herrajes
- ExplosorVidrio: Explosión de materiales vidrio
- ExplosorPlasticos: Explosión de materiales plásticos
- ExplosorOtros: Explosión de otros materiales
- DiagnosticoPaquetes: Diagnóstico de tipos de paquete
- ConcentradorService: Servicio orquestador principal
"""

from concentrador_materiales.services.mapeador_tipos import MapeadorTipos
from concentrador_materiales.services.explosor_base import ExplosorBase
from concentrador_materiales.services.explosor_aluminio import ExplosorAluminio
from concentrador_materiales.services.explosor_herreria import ExplosorHerreria
from concentrador_materiales.services.explosor_herrajes import ExplosorHerrajes
from concentrador_materiales.services.explosor_vidrio import ExplosorVidrio
from concentrador_materiales.services.explosor_plasticos import ExplosorPlasticos
from concentrador_materiales.services.explosor_otros import ExplosorOtros
from concentrador_materiales.services.diagnostico_paquetes import DiagnosticoPaquetes
from concentrador_materiales.services.concentrador_service import ConcentradorService
from concentrador_materiales.services.logger_config import (
    configurar_logger,
    obtener_logger,
    registrar_advertencia,
    registrar_error
)

__all__ = [
    "MapeadorTipos",
    "ExplosorBase",
    "ExplosorAluminio",
    "ExplosorHerreria",
    "ExplosorHerrajes",
    "ExplosorVidrio",
    "ExplosorPlasticos",
    "ExplosorOtros",
    "DiagnosticoPaquetes",
    "ConcentradorService",
    "configurar_logger",
    "obtener_logger",
    "registrar_advertencia",
    "registrar_error",
]