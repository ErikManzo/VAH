# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ComponentePaquete:
    """Representa un componente individual dentro de un paquete."""
    tipo: str                     # AL, HR, PH, etc.
    clave: str
    descripcion: str
    cantidad_base: int            # cantidad definida en el paquete (sin multiplicar por piezas)
    horizontal: float = 1.0
    vertical: float = 1.0
    es_anidado: bool = False      # True si proviene de un paquete anidado
    datos_originales: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Paquete:
    """Representa un paquete padre (el que se muestra en tabla paquetes)."""
    tipo: str
    clave: str
    descripcion: str
    ancho: float
    alto: float
    piezas: int = 1
    es_anidado: bool = False
    padre_clave: Optional[str] = None
    componentes: List[ComponentePaquete] = field(default_factory=list)