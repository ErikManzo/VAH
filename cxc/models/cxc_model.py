# -*- coding: utf-8 -*-
from datetime import date
from typing import Optional
from decimal import Decimal

class CxcModel:
    id: Optional[int] = None
    presupuesto_id: Optional[int] = None
    cliente_id: Optional[int] = None
    folio: Optional[str] = None
    tipo_operacion: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha_emision: Optional[date] = None
    # ELIMINADO: fecha_acuerdo: Optional[date] = None
    subtotal: Decimal = Decimal('0.00')
    descuento_porcentaje: Optional[Decimal] = None
    descuento_monto: Optional[Decimal] = None
    iva_porcentaje: Optional[Decimal] = None
    iva_monto: Optional[Decimal] = None
    total: Decimal = Decimal('0.00')
    saldo_pendiente: Decimal = Decimal('0.00')
    estado: str = "EN CURSO"
    notas: Optional[str] = None
    presupuesto_aceptado: Optional[bool] = None
    fecha_aceptacion: Optional[date] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)