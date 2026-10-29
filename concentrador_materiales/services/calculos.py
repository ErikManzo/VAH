# -*- coding: utf-8 -*-
"""
Fórmulas matemáticas centralizadas para el concentrador.

Reglas oficiales:
- VIDRIO: ancho y alto en metros, área = ancho × alto
- ALUMINIO: metros_lineales = (ca × ancho) + (ch × alto)
- HERRERIA: usar item["metros"] si existe, o calcular con misma fórmula
- CEIL para todos los redondeos

Prohibido:
- Inventar valores para largo NULL
- Conversiones de unidades (metros es la única unidad)
"""

import math
from typing import Optional, Tuple


def ceil_float(valor: float) -> float:
    """
    Redondea hacia arriba usando CEIL.

    Args:
        valor: Número a redondear

    Returns:
        CEIL(valor) como float
    """
    if valor <= 0:
        return 0.0
    return math.ceil(valor)


def metros_lineales_aluminio(ca: float, ancho: float, ch: float, alto: float) -> float:
    """
    Calcula metros lineales para aluminio.

    Fórmula oficial: (ca × ancho) + (ch × alto)
    donde ancho y alto están en metros.

    Args:
        ca: Cantidad de veces que participa el ancho
        ancho: Ancho en metros
        ch: Cantidad de veces que participa el alto
        alto: Alto en metros

    Returns:
        Metros lineales calculados
    """
    return (ca * ancho) + (ch * alto)


def metros_lineales_paquete_aluminio(
        horizontal: int,
        vertical: int,
        ancho_paquete: float,
        alto_paquete: float
) -> float:
    """
    Calcula metros lineales por paquete de aluminio.

    Fórmula oficial: (horizontal × ancho) + (vertical × alto)

    Args:
        horizontal: Cantidad horizontal del componente
        vertical: Cantidad vertical del componente
        ancho_paquete: Ancho del paquete en metros
        alto_paquete: Alto del paquete en metros

    Returns:
        Metros lineales por paquete
    """
    return (horizontal * ancho_paquete) + (vertical * alto_paquete)


def area_vidrio(ancho: float, alto: float) -> float:
    """
    Calcula área en metros cuadrados para vidrio.

    Fórmula oficial: ancho × alto
    donde ancho y alto están en metros.

    Args:
        ancho: Ancho en metros
        alto: Alto en metros

    Returns:
        Área en metros cuadrados
    """
    return ancho * alto


def calcular_tramos(metros_totales: float, largo_tramo: Optional[float]) -> Optional[int]:
    """
    Calcula cantidad de tramos para aluminio.

    IMPORTANTE: Si largo_tramo es None o <= 0, retorna None
    (NO inventar valores).

    Args:
        metros_totales: Metros totales a cubrir
        largo_tramo: Longitud del tramo en metros (desde materiales_aluminio)

    Returns:
        Número de tramos (CEIL), o None si largo_tramo es inválido
    """
    if metros_totales <= 0:
        return 0

    if largo_tramo is None or largo_tramo <= 0:
        return None

    return math.ceil(metros_totales / largo_tramo)


def calcular_hojas(m2_totales: float, hoja_area: float = 9.36) -> int:
    """
    Calcula cantidad de hojas para vidrio.

    Fórmula oficial: CEIL(m2_totales / 9.36)
    donde 9.36 = 3.60 × 2.60 (hoja estándar)

    Args:
        m2_totales: Metros cuadrados totales
        hoja_area: Área de una hoja estándar (default 9.36)

    Returns:
        Número de hojas (CEIL)
    """
    if m2_totales <= 0:
        return 0
    return math.ceil(m2_totales / hoja_area)


def calcular_piezas_herreria(metros_totales: float, longitud_perfil: float = 6.00) -> int:
    """
    Calcula cantidad de piezas para herrería.

    Fórmula oficial: CEIL(metros_totales / 6.00)

    Args:
        metros_totales: Metros totales del perfil
        longitud_perfil: Longitud estándar del perfil (default 6.00)

    Returns:
        Número de piezas (CEIL)
    """
    if metros_totales <= 0:
        return 0
    return math.ceil(metros_totales / longitud_perfil)


def metros_totales_herreria(item: dict) -> Tuple[float, bool]:
    """
    Obtiene o calcula metros totales para herrería.

    Regla: Usar item["metros"] si existe, sino calcular.

    Args:
        item: Diccionario con datos de items_partida

    Returns:
        Tupla (metros_totales, usado_metros_calculado)
        usado_metros_calculado es True si se usó el campo metros de la BD
    """
    # Priorizar campo metros si existe y es válido
    if item.get("metros") is not None and item["metros"] > 0:
        return float(item["metros"]), True

    # Calcular con fórmula estándar
    ca = float(item.get("ca", 1.0))
    ancho = float(item.get("ancho", 0.0))
    ch = float(item.get("ch", 1.0))
    alto = float(item.get("alto", 0.0))

    metros = (ca * ancho) + (ch * alto)
    return metros, False