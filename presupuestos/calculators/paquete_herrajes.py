# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/calculators/paquete_herrajes.py
Calculador para PAQUETES DE HERRAJES (PAQ-HR).

NOTA IMPORTANTE:
Este calculador SOLO retorna la suma de P.U. de los componentes.
NO aplica Desperdicio ni Factor de Venta.
El Desperdicio y F.V. se aplican a nivel PARTIDA en _recalc_summary().
"""

from typing import Dict, Any, Tuple


def compute_paquete_herrajes_inline(
    *,
    svc,
    clave: str,
    piezas: int,
    extra: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Calcula el Precio Unitario e Importe de un paquete de herrajes.
    NO aplica Desperdicio ni F.V. (se aplican a nivel partida).
    """
    suma_componentes = float(svc.paquete_herrajes_precio_total(clave) or 0)
    piezas_int = max(1, int(piezas or 1))
    return suma_componentes, suma_componentes * piezas_int