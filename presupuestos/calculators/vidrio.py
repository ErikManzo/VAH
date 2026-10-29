# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/calculators/vidrio.py
Calculador para materiales de VIDRIO.
"""

from typing import Dict, Any, Tuple
import math


def _ceil_step(x: float, step: float = 0.05) -> float:
    """Redondeo industrial hacia arriba al múltiplo de 0.05."""
    if step <= 0:
        return float(x or 0)
    return round(math.ceil((float(x or 0)) / step) * step, 2)


def compute_vidrio(
    *,
    svc,
    clave: str,
    color: str | None = None,
    ancho: float,
    alto: float,
    piezas: int,
    extra: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Calcula el costo del vidrio basado en m² con redondeo industrial.
    El parámetro 'color' se mantiene por compatibilidad pero no se usa.
    """
    piezas = max(1, int(piezas or 1))
    ancho_adj = _ceil_step(float(ancho or 0), 0.05)
    alto_adj = _ceil_step(float(alto or 0), 0.05)
    m2 = max(0.0, ancho_adj * alto_adj)
    price_m2 = svc.vidrio_precio(clave)

    if price_m2 is None or float(price_m2) <= 0:
        return 0.0, 0.0

    pu = m2 * float(price_m2)
    return pu, pu * piezas