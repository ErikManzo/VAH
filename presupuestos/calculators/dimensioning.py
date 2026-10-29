# -*- coding: utf-8 -*-
r"""
D:\vah\presupuestos\calculators\dimensioning.py

Regla general de dimensionado (oculta a la UI):
- Para ANCHO/ALTO se usa SIEMPRE el siguiente múltiplo de 0.05 mayor al valor capturado.
  Ejemplos: 2.12→2.15, 1.65→1.70, 1.80→1.85, 2.15→2.20.
- Si el valor <= 0, se regresa 0.0 (no "sube" a 0.05).
- Redondeo robusto con Decimal para evitar errores binarios.
"""

from __future__ import annotations
from decimal import Decimal, ROUND_FLOOR, InvalidOperation


def adjust_dimension(value: float, step: float = 0.05) -> float:
    """
    Eleva 'value' al siguiente múltiplo de 'step' (estrictamente mayor), con 2 decimales.

    Args:
        value: valor original (float/str/Decimal).
        step: incremento (default 0.05).

    Returns:
        float con 2 decimales, aplicando:
            - si value <= 0: 0.00
            - si value > 0: siguiente múltiplo de 'step' estrictamente superior.

    Notas:
        • Se usa Decimal para evitar imprecisiones.
        • Siempre sube al siguiente múltiplo, incluso si ya está exacto.
    """
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        v = Decimal("0")

    if v <= 0:
        return 0.0

    s = Decimal(str(step))
    # n = floor(v/step) + 1  ⇒ múltiplo estrictamente mayor que v
    n = (v / s).to_integral_value(rounding=ROUND_FLOOR) + 1
    adjusted = (n * s).quantize(Decimal("0.00"))  # 2 decimales

    return float(adjusted)