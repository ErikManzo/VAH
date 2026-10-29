# -*- coding: utf-8 -*-
"""
Clase base abstracta para todos los explosores.

Proporciona funcionalidad común:
- Registro de advertencias y errores
- Acceso a repositorios de materiales
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from concentrador_materiales.services.logger_config import (

    registrar_advertencia,
    registrar_error,
    registrar_info
)


from common.logger_config import get_logger
logger = get_logger('concentrador.services.explosor_base')

class ExplosorBase(ABC):
    """
    Clase abstracta para explosores de materiales.

    Todos los explosores deben implementar el método explotar().
    """

    def __init__(self, materiales_repo):
        """
        Inicializa el explosor.

        Args:
            materiales_repo: Repositorio de materiales para consultas
        """
        self.materiales_repo = materiales_repo
        self._advertencias: List[Dict[str, Any]] = []
        self._errores: List[Dict[str, Any]] = []

    @abstractmethod
    def explotar(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Explota un item de partida en materiales concentrados.

        Args:
            item: Diccionario con datos de items_partida
            cantidad_cxc: Cantidad desde CXC (cantidad_facturada)
            context: Contexto adicional (ancho/alto de paquete, etc.)

        Returns:
            Lista de MaterialConcentrado
        """
        pass

    def _registrar_advertencia(
            self,
            codigo: str,
            mensaje: str,
            datos: Optional[Dict[str, Any]] = None
    ):
        """
        Registra una advertencia.

        Args:
            codigo: Código de la advertencia
            mensaje: Mensaje descriptivo
            datos: Datos adicionales
        """
        self._advertencias.append({
            "codigo": codigo,
            "mensaje": mensaje,
            "datos": datos or {}
        })
        registrar_advertencia(codigo, mensaje, datos)

    def _registrar_error(
            self,
            codigo: str,
            mensaje: str,
            datos: Optional[Dict[str, Any]] = None
    ):
        """
        Registra un error.

        Args:
            codigo: Código del error
            mensaje: Mensaje descriptivo
            datos: Datos adicionales
        """
        self._errores.append({
            "codigo": codigo,
            "mensaje": mensaje,
            "datos": datos or {}
        })
        registrar_error(codigo, mensaje, datos)

    def _registrar_info(
            self,
            codigo: str,
            mensaje: str,
            datos: Optional[Dict[str, Any]] = None
    ):
        """
        Registra información.

        Args:
            codigo: Código de información
            mensaje: Mensaje descriptivo
            datos: Datos adicionales
        """
        registrar_info(codigo, mensaje, datos)

    def obtener_advertencias(self) -> List[Dict[str, Any]]:
        """Retorna la lista de advertencias."""
        return self._advertencias.copy()

    def obtener_errores(self) -> List[Dict[str, Any]]:
        """Retorna la lista de errores."""
        return self._errores.copy()