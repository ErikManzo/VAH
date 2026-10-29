# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

@dataclass
class ConfiguracionCxcModel:
    id: Optional[int]
    iva_default: Decimal
    descuento_default: Decimal
    prefijo_factura: Optional[str]
    siguiente_folio: Optional[int]