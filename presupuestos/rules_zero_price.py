
# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/rules_zero_price.py
Valida antes de agregar para evitar renglones con precio 0.00
"""
from typing import NamedTuple, List

class GuardResult(NamedTuple):
    proceed: bool
    faltantes: List[str]

def guard_before_add(
    *, svc, tipo: str, clave: str, color: str | None, precio_kg: float | None = None
) -> GuardResult:
    falt = []
    ok = True
    t = (tipo or "").strip().upper()

    if t in {"AL", "ALUMINIO"}:
        price = svc.aluminio_precio(clave, color=color)
        if not price or float(price) <= 0:
            ok = False; falt.append(f"AL:{clave}")

    elif t in {"VI", "VIDRIO"}:
        p = svc.vidrio_precio(clave)
        if not p or float(p) <= 0:
            ok = False; falt.append(f"VI:{clave}")

    elif t in {"HE", "HERRERIA", "HERRERÍA"}:
        kg = svc.herreria_kg_por_m(clave)
        if kg is None or float(kg) <= 0:
            ok = False; falt.append(f"HE-KG/M:{clave}")
        try:
            pk = float(precio_kg or 0)
        except Exception:
            pk = 0.0
        if pk <= 0:
            ok = False; falt.append("HE:$KG=0")

    elif t in {"HR", "HERRAJES"}:
        p = svc.herrajes_precio(clave)
        if not p or float(p) <= 0:
            ok = False; falt.append(f"HR:{clave}")

    elif t in {"PL", "PLASTICOS", "PLÁSTICOS"}:
        p = svc.plasticos_precio(clave)
        if not p or float(p) <= 0:
            ok = False; falt.append(f"PL:{clave}")

    elif t in {"OT", "OTROS"}:
        p = svc.otros_precio(clave)
        if not p or float(p) <= 0:
            ok = False; falt.append(f"OT:{clave}")

    elif t in {"PAQ-AL", "PAQUETE ALUMINIO", "PAQUETE_ALUMINIO"}:
        items = svc.paquete_aluminio_items(clave) or []
        for it in items:
            subt = (it.get("tipo") or "").upper()
            subc = it.get("clave") or ""
            if subt == "AL":
                p = svc.aluminio_precio(subc, color=None)
                if not p or float(p) <= 0:
                    ok = False; falt.append(f"AL:{subc}")
            elif subt in {"HE", "HERRERIA", "HERRERÍA"}:
                kg = svc.herreria_kg_por_m(subc)
                if kg is None or float(kg) <= 0:
                    ok = False; falt.append(f"HE-KG/M:{subc}")
                try:
                    pk = float(precio_kg or 0)
                except Exception:
                    pk = 0.0
                if pk <= 0:
                    ok = False; falt.append("HE:$KG=0")
            elif subt == "HR":
                p = svc.herrajes_precio(subc)
                if not p or float(p) <= 0:
                    ok = False; falt.append(f"HR:{subc}")
            elif subt == "PL":
                p = svc.plasticos_precio(subc)
                if not p or float(p) <= 0:
                    ok = False; falt.append(f"PL:{subc}")
            elif subt == "OT":
                p = svc.otros_precio(subc)
                if not p or float(p) <= 0:
                    ok = False; falt.append(f"OT:{subc}")
            elif subt == "VI":
                p = svc.vidrio_precio(subc)
                if not p or float(p) <= 0:
                    ok = False; falt.append(f"VI:{subc}")

    elif t in {"PAQ-HR", "PAQUETE HERRAJES", "PAQUETE_HERRAJES"}:
        total = svc.paquete_herrajes_precio_total(clave)
        if not total or float(total) <= 0:
            ok = False; falt.append(f"PH:{clave}")

    return GuardResult(proceed=ok, faltantes=falt)
