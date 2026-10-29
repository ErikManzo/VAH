r"""
Módulo: proveedor_service.py
Ubicación: D:\vah\proveedores\services

Servicio simplificado que usa SOLO el repositorio SQL Server.
"""

from typing import Any, Dict, List, Optional

from common.logger_config import get_logger
from proveedores.repositories.proveedor_repository import ProveedorRepository

logger = get_logger("proveedores.services.proveedor_service")


class ProveedorService:
    """
    Servicio que centraliza la lógica de negocio de Proveedores.
    Usa ProveedorRepository para acceso a SQL Server.
    """

    def __init__(self):
        self.repo = ProveedorRepository()

    # ---------------------------------------------------------
    # Métodos CRUD
    # ---------------------------------------------------------
    def listar_todos(self) -> List[Dict[str, Any]]:
        """Lista todos los proveedores."""
        return self.repo.listar_todos()

    def buscar_por_empresa(self, nombre: str) -> List[Dict[str, Any]]:
        """Busca proveedores por empresa (prefijo)."""
        return self.repo.buscar_por_empresa(nombre)

    def obtener_por_id(self, proveedor_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un proveedor por ID."""
        return self.repo.obtener_por_id(proveedor_id)

    def insertar(self, proveedor: Any) -> bool:
        """Inserta un nuevo proveedor."""
        return self.repo.insertar(proveedor)

    def guardar(self, proveedor: Any) -> bool:
        """Alias para insertar."""
        return self.repo.insertar(proveedor)

    def actualizar(self, proveedor: Any) -> bool:
        """Actualiza un proveedor existente."""
        return self.repo.actualizar(proveedor)

    def eliminar(self, proveedor_id: int) -> bool:
        """Elimina un proveedor por ID."""
        return self.repo.eliminar(proveedor_id)

    def agrupar_coincidencias_por_id(self, ids):
        """Agrupa múltiples registros."""
        return self.repo.agrupar_coincidencias_por_id(ids)
