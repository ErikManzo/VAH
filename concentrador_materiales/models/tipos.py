# -*- coding: utf-8 -*-
"""
Enumeraciones para tipos de materiales y paquetes
"""
from enum import Enum, auto

class TipoMaterial(Enum):
    """
    Tipos de almacén para materiales.
    AL y ALUMINIO se normalizan a ALUMINIO en memoria.
    """
    ALUMINIO = "ALUMINIO"
    HERRERIA = "HERRERIA"
    HERRAJES = "HERRAJES"
    VIDRIO = "VIDRIO"
    PLASTICOS = "PLASTICOS"
    OTROS = "OTROS"
    DESCONOCIDO = "DESCONOCIDO"

    @classmethod
    def from_string(cls, valor: str) -> "TipoMaterial":
        """
        Convierte un string a TipoMaterial.
        Normaliza AL y ALUMINIO al mismo valor.
        """
        if not valor:
            return cls.DESCONOCIDO

        valor_upper = valor.strip().upper()

        # AL y ALUMINIO son equivalentes
        if valor_upper in ("AL", "ALUMINIO"):
            return cls.ALUMINIO

        mapping = {
            "HERRERIA": cls.HERRERIA,
            "HERRERÍA": cls.HERRERIA,
            "HERRAJES": cls.HERRAJES,
            "HERRAJE": cls.HERRAJES,
            "VIDRIO": cls.VIDRIO,
            "PLASTICOS": cls.PLASTICOS,
            "PLÁSTICOS": cls.PLASTICOS,
            "OTROS": cls.OTROS,
        }

        return mapping.get(valor_upper, cls.DESCONOCIDO)


class TipoPaquete(Enum):
    """
    Tipos de paquete reconocidos por el sistema.
    """
    ALUMINIO = "ALUMINIO"
    HERRAJES = "HERRAJES"
    DESCONOCIDO = "DESCONOCIDO"

    @classmethod
    def from_string(cls, valor: str) -> "TipoPaquete":
        """
        Convierte un string a TipoPaquete.
        Soporta formatos:
        - "PAQUETE ALUMINIO" (desde BD)
        - "ALUMINIO" (directo)
        """
        if not valor:
            return cls.DESCONOCIDO

        valor_upper = valor.strip().upper()

        # CORRECCIÓN: Eliminar prefijo "PAQUETE " si existe
        if valor_upper.startswith("PAQUETE "):
            valor_upper = valor_upper[8:].strip()

        mapping = {
            "ALUMINIO": cls.ALUMINIO,
            "ALUMINIUM": cls.ALUMINIO,
            "HERRAJES": cls.HERRAJES,
            "HERRAJE": cls.HERRAJES,
        }

        return mapping.get(valor_upper, cls.DESCONOCIDO)


class OrigenMaterial:
    """
    Constantes para el origen del material.
    """
    DIRECTO = "DIRECTO"
    PAQUETE = "PAQUETE"