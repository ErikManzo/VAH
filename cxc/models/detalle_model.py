# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class CxcDetalleModel:
    id: Optional[int]
    cxc_id: int
    presupuesto_id: int
    partida_id: int
    cantidad_facturada: Decimal
    precio_unitario: Decimal
    importe: Decimal
    created_at: Optional[datetime]