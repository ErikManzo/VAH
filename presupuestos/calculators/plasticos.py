
# -*- coding: utf-8 -*-
from typing import Dict, Any, Tuple

def compute_plasticos(*, svc, clave: str, piezas: int, extra: Dict[str, Any]) -> Tuple[float, float]:
    piezas = max(1, int(piezas or 1))
    precio = svc.plasticos_precio(clave)
    if precio is None:
        return 0.0, 0.0
    pu = float(precio)
    return pu, pu * piezas
