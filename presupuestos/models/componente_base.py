# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/models/componente_base.py
Modelo de datos para componentes base de paquetes (SIN multiplicadores aplicados).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ComponenteBase:
    """
    Representa un componente base de un paquete, SIN multiplicadores aplicados.
    Los multiplicadores se aplican durante la consolidación a materiales.
    """
    tipo: str  # AL, HR, OT, PL, VI, HE, PH
    clave: str  # Clave del material/paquete
    descripcion: str  # Descripción
    cantidad_base: float = 1.0  # Cantidad definida en el paquete (SIN multiplicar)
    horizontal: float = 1.0  # CA (para aluminio)
    vertical: float = 1.0  # CH (para aluminio)
    multiplicador_ph: float = 1.0  # >1 para componentes que vienen de un PH
    es_ph: bool = False  # True si es un paquete anidado (PH)
    datos_originales: Dict[str, Any] = field(default_factory=dict)

    @property
    def ca(self) -> float:
        """Alias para horizontal (compatibilidad)."""
        return self.horizontal

    @property
    def ch(self) -> float:
        """Alias para vertical (compatibilidad)."""
        return self.vertical