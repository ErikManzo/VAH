# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

@dataclass
class PagoModel:
    id: Optional[int]
    cxc_id: int
    fecha_pago: date
    monto: Decimal
    metodo_pago: str
    concepto: str
    cuenta_destino: str
    referencia: Optional[str]
    notas: Optional[str]
    created_at: Optional[datetime]