
# -*- coding: utf-8 -*-
from typing import Dict, Any, Tuple
import math

def _ceil_step(x: float, step: float = 0.05) -> float:
    if step <= 0:
        return float(x or 0)
    return round(math.ceil((float(x or 0)) / step) * step, 2)

def compute_aluminio(*, svc, clave: str, color: str|None, ancho: float, alto: float,
                     piezas: int, ca: float, ch: float, extra: Dict[str, Any]) -> Tuple[float, float]:
    piezas = max(1, int(piezas or 1))
    ca = float(ca or 0); ch = float(ch or 0)
    ancho_adj = _ceil_step(float(ancho or 0), 0.05)
    alto_adj  = _ceil_step(float(alto or 0), 0.05)
    largo = svc.aluminio_largo(clave)
    if not largo or largo <= 0.10:
        return 0.0, 0.0
    precio = svc.aluminio_precio(clave, color)
    if precio is None:
        return 0.0, 0.0
    # Margen de corte estándar para aluminio (10 cm)
    MARGEN_CORTE_ALUMINIO = 0.10
    factor = float(precio) / float(largo - MARGEN_CORTE_ALUMINIO)
    metros = (ca * ancho_adj) + (ch * alto_adj)
    pu = metros * factor
    return pu, pu * piezas
