# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/calculators/__init__.py
Dispatch central de cálculos para todos los tipos de materiales.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from . import aluminio as calc_al
from . import vidrio as calc_vi
from . import plasticos as calc_pl
from . import herrajes as calc_hr
from . import otros as calc_ot
from . import paquete_aluminio as calc_paq_al
from . import paquete_herrajes as calc_paq_hr

try:
    from .herreria import compute_herreria_legacy as calc_he_legacy
except ImportError:
    def calc_he_legacy(*args, **kwargs):
        return 0.0, 0.0


@dataclass
class EspecificacionesCtx:
    svc: Any
    tipo: str
    clave: str
    color: Optional[str]
    ancho: float
    alto: float
    piezas: int
    ca: float
    ch: float
    extra: Dict[str, Any]


def dispatch_calculo(ctx: EspecificacionesCtx) -> Tuple[float, float]:
    t = (ctx.tipo or "").strip().upper()

    if t in ("AL", "ALUMINIO"):
        return calc_al.compute_aluminio(
            svc=ctx.svc, clave=ctx.clave, color=ctx.color,
            ancho=ctx.ancho, alto=ctx.alto, piezas=ctx.piezas,
            ca=ctx.ca, ch=ctx.ch, extra=ctx.extra,
        )

    if t in ("HE", "HERRERIA", "HERRERÍA"):
        extra_completo = dict(ctx.extra) if ctx.extra else {}
        extra_completo["precio_kg"] = ctx.extra.get("precio_kg", 0)
        extra_completo["ca"] = ctx.ca
        extra_completo["ch"] = ctx.ch
        return calc_he_legacy(
            svc=ctx.svc, clave=ctx.clave, piezas=ctx.piezas,
            ancho=ctx.ancho, alto=ctx.alto, extra=extra_completo,
        )

    if t in ("VI", "VIDRIO"):
        return calc_vi.compute_vidrio(
            svc=ctx.svc, clave=ctx.clave, color=ctx.color,
            ancho=ctx.ancho, alto=ctx.alto, piezas=ctx.piezas, extra=ctx.extra,
        )

    if t in ("PL", "PLASTICOS", "PLÁSTICOS"):
        return calc_pl.compute_plasticos(
            svc=ctx.svc, clave=ctx.clave, piezas=ctx.piezas, extra=ctx.extra
        )

    if t in ("HR", "HERRAJES"):
        return calc_hr.compute_herrajes(
            svc=ctx.svc, clave=ctx.clave, piezas=ctx.piezas, extra=ctx.extra
        )

    if t in ("OT", "OTROS"):
        return calc_ot.compute_otros(
            svc=ctx.svc, clave=ctx.clave, piezas=ctx.piezas, extra=ctx.extra
        )

    if t in ("PAQ-AL", "PAQUETE ALUMINIO", "PAQUETE_ALUMINIO"):
        return calc_paq_al.compute_paquete_aluminio_inline(
            svc=ctx.svc, clave=ctx.clave, color=ctx.color,
            ancho=ctx.ancho, alto=ctx.alto, piezas=ctx.piezas, extra=ctx.extra,
        )

    if t in ("PAQ-HR", "PAQUETE HERRAJES", "PAQUETE_HERRAJES"):
        return calc_paq_hr.compute_paquete_herrajes_inline(
            svc=ctx.svc, clave=ctx.clave, piezas=ctx.piezas, extra=ctx.extra,
        )

    price = ctx.svc.try_precio_generico(ctx.tipo, ctx.clave)
    if price is None:
        return 0.0, 0.0
    pu = float(price)
    return pu, pu * max(1, int(ctx.piezas or 1))