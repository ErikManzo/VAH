# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/calculators/paquete_aluminio.py
Calculador para PAQUETES DE ALUMINIO (PAQ-AL).

NOTA IMPORTANTE:
Este calculador SOLO retorna la suma de P.U. de los componentes.
NO aplica Desperdicio ni Factor de Venta.
El Desperdicio y F.V. se aplican a nivel PARTIDA en _recalc_summary().
"""

from typing import Dict, Any, Tuple
from .aluminio import compute_aluminio
from .herreria import compute_herreria
from .vidrio import compute_vidrio
from .plasticos import compute_plasticos
from .otros import compute_otros
from .herrajes import compute_herrajes
from .paquete_herrajes import compute_paquete_herrajes_inline


def compute_paquete_aluminio_inline(
    *,
    svc,
    clave: str,
    color: str | None,
    ancho: float,
    alto: float,
    piezas: int,
    extra: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Calcula el Precio Unitario e Importe de un paquete de aluminio.
    NO aplica Desperdicio ni F.V. (se aplican a nivel partida).
    """
    items = svc.paquete_aluminio_items(clave)
    if not items:
        return 0.0, 0.0

    suma_pu = 0.0

    for it in items:
        sub = (it.get("tipo") or "").strip().upper()
        subc = it.get("clave") or ""
        cantidad = int(it.get("cantidad") or 1)

        if sub == "AL":
            ca = float(it.get("horizontal") or 0)
            ch = float(it.get("vertical") or 0)
            pu, _ = compute_aluminio(
                svc=svc, clave=subc, color=color, ancho=ancho, alto=alto,
                piezas=1, ca=ca * cantidad, ch=ch * cantidad, extra=extra
            )
            suma_pu += pu

        elif sub in ("HE", "HERRERIA", "HERRERÍA"):
            extra_herr = dict(extra)
            extra_herr["color"] = color
            pu, _ = compute_herreria(
                svc=svc, clave=subc, piezas=cantidad, ancho=ancho, alto=alto,
                extra=extra_herr
            )
            suma_pu += pu

        elif sub == "HR":
            pu, _ = compute_herrajes(svc=svc, clave=subc, piezas=cantidad, extra=extra)
            suma_pu += pu

        elif sub == "PH":
            pu, _ = compute_paquete_herrajes_inline(
                svc=svc, clave=subc, piezas=cantidad, extra=extra
            )
            suma_pu += pu

        elif sub == "PL":
            pu, _ = compute_plasticos(svc=svc, clave=subc, piezas=cantidad, extra=extra)
            suma_pu += pu

        elif sub == "OT":
            pu, _ = compute_otros(svc=svc, clave=subc, piezas=cantidad, extra=extra)
            suma_pu += pu

        elif sub == "VI":
            pu, _ = compute_vidrio(
                svc=svc, clave=subc, color=color, ancho=ancho, alto=alto,
                piezas=cantidad, extra=extra
            )
            suma_pu += pu

    piezas_int = max(1, int(piezas or 1))
    return suma_pu, suma_pu * piezas_int