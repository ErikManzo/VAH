# -*- coding: utf-8 -*-
"""
Mapeador de tipos para normalización en memoria.

Reglas:
- AL → ALUMINIO
- ALUMINIO → ALUMINIO
- Los demás tipos se mapean directamente
"""

from typing import Dict, Any
from concentrador_materiales.models.tipos import TipoMaterial, TipoPaquete


class MapeadorTipos:
    """
    Normaliza tipos de materiales y paquetes en memoria.
    NO modifica la base de datos.
    """

    # Mapeo interno para normalización (solo en memoria)
    _MAPEO_MATERIALES = {
        # Aluminio - ambos son equivalentes
        "AL": "ALUMINIO",
        "ALUMINIO": "ALUMINIO",

        # Herrería
        "HERRERIA": "HERRERIA",
        "HERRERÍA": "HERRERIA",

        # Herrajes
        "HERRAJES": "HERRAJES",
        "HERRAJE": "HERRAJES",

        # Vidrio
        "VIDRIO": "VIDRIO",

        # Plásticos
        "PLASTICOS": "PLASTICOS",
        "PLÁSTICOS": "PLASTICOS",

        # Otros
        "OTROS": "OTROS",
    }

    # Tipos que representan paquetes
    _TIPOS_PAQUETE = {
        "PAQUETE ALUMINIO",
        "PAQUETE ALUMINIUM",
        "PAQUETE HERRAJES",
        "PAQUETE HERRAJE",
    }

    def __init__(self):
        """Inicializa el mapeador."""
        self._cache_tipos: Dict[str, str] = {}

    def obtener_almacen_normalizado(self, tipo_original: str) -> str:
        """
        Normaliza un tipo de material a su almacén correspondiente.

        Args:
            tipo_original: Tipo original desde items_partida (ej: "AL", "ALUMINIO")

        Returns:
            Almacén normalizado (ej: "ALUMINIO") o "DESCONOCIDO"
        """
        if not tipo_original:
            return "DESCONOCIDO"

        # Verificar cache
        tipo_upper = tipo_original.strip().upper()
        if tipo_upper in self._cache_tipos:
            return self._cache_tipos[tipo_upper]

        # Mapear
        resultado = self._MAPEO_MATERIALES.get(tipo_upper, "DESCONOCIDO")
        self._cache_tipos[tipo_upper] = resultado
        return resultado

    def es_tipo_paquete(self, tipo: str) -> bool:
        """
        Determina si un tipo representa un paquete.

        Args:
            tipo: Tipo desde items_partida

        Returns:
            True si es un tipo de paquete
        """
        if not tipo:
            return False
        return tipo.strip().upper() in self._TIPOS_PAQUETE

    def normalizar_tipo_paquete(self, tipo_paquete: str) -> TipoPaquete:
        """
        Normaliza un tipo de paquete desde partida_paquetes.

        Args:
            tipo_paquete: Tipo desde partida_paquetes.tipo_paquete

        Returns:
            TipoPaquete normalizado
        """
        return TipoPaquete.from_string(tipo_paquete)

    def obtener_tipo_material_enum(self, tipo_original: str) -> TipoMaterial:
        """
        Obtiene el enum TipoMaterial a partir del tipo original.

        Args:
            tipo_original: Tipo original desde items_partida

        Returns:
            TipoMaterial correspondiente
        """
        return TipoMaterial.from_string(self.obtener_almacen_normalizado(tipo_original))