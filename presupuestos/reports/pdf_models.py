# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/pdf_models.py
Modelos de datos para el generador de PDF
NUEVO: TotalesPresupuesto soporta descuento_porcentaje:
descuento_monto = subtotal × pct/100
subtotal_descuentado = subtotal − descuento_monto
iva_monto = subtotal_descuentado × iva/100
total = subtotal_descuentado + iva_monto
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PartidaPresupuesto:
    """Modelo de datos para una partida de presupuesto"""
    numero: int
    titulo: str
    descripcion: str
    precio_unitario: float
    piezas: int
    importe: float

@dataclass
class TotalesPresupuesto:
    """Modelo de datos para los totales del presupuesto (con descuento)"""
    subtotal: float
    iva_porcentaje: float = 16.0
    descuento_porcentaje: float = 0.0
    descuento_monto: float = 0.0
    subtotal_descuentado: float = 0.0
    iva_monto: float = 0.0
    total: float = 0.0

    def __post_init__(self):
        self.descuento_monto = self.subtotal * (self.descuento_porcentaje / 100.0)
        self.subtotal_descuentado = self.subtotal - self.descuento_monto
        self.iva_monto = self.subtotal_descuentado * (self.iva_porcentaje / 100.0)
        self.total = self.subtotal_descuentado + self.iva_monto

    def validar(self) -> tuple[bool, List[str]]:
        errores = []
        if self.subtotal < 0:
            errores.append("Subtotal no puede ser negativo")
        if self.descuento_porcentaje < 0 or self.descuento_porcentaje > 100:
            errores.append("Descuento fuera de rango (0-100)")
        return len(errores) == 0, errores

@dataclass
class DatosPresupuesto:
    """Modelo de datos completo para el presupuesto"""
    cliente: str
    num_presupuesto: int
    obra: str
    fecha: str
    anodizado: str
    partidas: List[PartidaPresupuesto] = field(default_factory=list)
    totales: Optional[TotalesPresupuesto] = None
    forma_pago: str = "60% AL ACEPTAR EL PRESUPUESTO / 40% AL TERMINAR"
    plazo_entrega: str = "SERÁ DE COMÚN ACUERDO"
    notas: str = ""
    descuento_porcentaje: float = 0.0

    def __post_init__(self):
        if self.totales is None and self.partidas:
            subtotal = sum(p.importe for p in self.partidas)
            self.totales = TotalesPresupuesto(
                subtotal=subtotal,
                descuento_porcentaje=self.descuento_porcentaje
            )

    def validar(self) -> tuple[bool, List[str]]:
        errores = []
        if not self.cliente or not self.cliente.strip():
            errores.append("Cliente requerido")
        if self.num_presupuesto <= 0:
            errores.append("Número de presupuesto inválido")
        if not self.partidas:
            errores.append("No hay partidas")
        return len(errores) == 0, errores