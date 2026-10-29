# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/calculators/herreria.py
Calculator para materiales de HERRERÍA - VERSIÓN FINAL CORREGIDA Y ROBUSTA.

FÓRMULAS VALIDADAS:
1. Kgs. = ((CA × ancho_redondeado) + (CH × alto_redondeado)) × Kg/m
2. P.U. = Kgs. × precio_kg
3. Importe = P.U. × Piezas

REDONDEO: Siempre hacia arriba al múltiplo de 0.05
EJEMPLO: 2.12 → 2.15, 1.68 → 1.70
"""

from typing import Dict, Any, Tuple
import math
import logging

# Configurar logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _ceil_step(x: float, step: float = 0.05) -> float:
    """Redondea hacia arriba al múltiplo de 'step' más cercano."""
    if step <= 0:
        return float(x or 0)
    try:
        return round(math.ceil((float(x or 0)) / step) * step, 2)
    except Exception as e:
        logger.error(f"Error en _ceil_step: {e}")
        return float(x or 0)


def compute_herreria(
        *,
        svc,
        clave: str,
        piezas: int,
        ancho: float,
        alto: float,
        extra: Dict[str, Any]
) -> Tuple[float, float, float]:
    """
    Calcula Precio Unitario, Importe y Kilogramos para materiales de herrería.

    Args:
        svc: Servicio de base de datos con método herreria_kg_por_m(clave)
        clave: Clave del material (ej: PTR32V, TUBE40)
        piezas: Número de piezas
        ancho: Ancho en METROS (desde la interfaz)
        alto: Alto en METROS (desde la interfaz)
        extra: Diccionario con:
            - precio_kg: Precio por kilogramo (obligatorio)
            - ca: Cantidad Ancho (número de tramos, default 1)
            - ch: Cantidad Alto (número de tramos, default 1)

    Returns:
        Tuple[precio_unitario, importe_total, kgs_totales]

    FÓRMULAS:
        1. ancho_red = _ceil_step(ancho, 0.05)
        2. alto_red = _ceil_step(alto, 0.05)
        3. metros_totales = (ca × ancho_red) + (ch × alto_red)
        4. kgs_totales = metros_totales × kg_m
        5. precio_unitario = kgs_totales × precio_kg
        6. importe_total = precio_unitario × piezas
    """
    try:
        # ========== VALIDACIONES INICIALES ==========
        logger.info(f"Iniciando cálculo para material: {clave}")

        if not svc:
            raise ValueError("Servicio de base de datos no proporcionado")

        if not clave or not clave.strip():
            raise ValueError("Clave de material no proporcionada")

        # ========== REDONDEO DE MEDIDAS ==========
        logger.info(f"Medidas originales - Ancho: {ancho}, Alto: {alto}")

        # Redondear al múltiplo de 0.05 hacia arriba
        ancho_red = _ceil_step(float(ancho or 0), 0.05)
        alto_red = _ceil_step(float(alto or 0), 0.05)

        logger.info(f"Medidas redondeadas - Ancho: {ancho_red}, Alto: {alto_red}")

        # NOTA: Las medidas YA están en METROS desde la interfaz
        # No convertir a cm ni dividir entre 100
        ancho_m = ancho_red
        alto_m = alto_red

        logger.info(f"Medidas en metros - Ancho: {ancho_m}m, Alto: {alto_m}m")

        # ========== OBTENER DATOS DE EXTRA ==========
        # Obtener precio por kg
        precio_kg = extra.get("precio_kg")
        if precio_kg is None:
            raise ValueError("Falta 'precio_kg' en parámetros extra")

        try:
            precio_kg = float(precio_kg)
        except (ValueError, TypeError):
            raise ValueError(f"Precio por kg inválido: {precio_kg}")

        if precio_kg <= 0:
            raise ValueError(f"Precio por kg debe ser positivo: {precio_kg}")

        # Obtener ca y ch (Cantidad Ancho y Cantidad Alto)
        ca = float(extra.get("ca", 0) or 0)
        ch = float(extra.get("ch", 0) or 0)

        # Valores por defecto si son cero
        if ca <= 0:
            ca = 1.0
            logger.info(f"Usando valor por defecto para ca: {ca}")

        if ch <= 0:
            ch = 1.0
            logger.info(f"Usando valor por defecto para ch: {ch}")

        logger.info(f"Datos extra - Precio/kg: ${precio_kg}, CA: {ca}, CH: {ch}")

        # ========== OBTENER KG/M DESDE BD ==========
        kg_m = svc.herreria_kg_por_m(clave)
        if kg_m is None:
            raise ValueError(f"No se encontró kg/m para la clave: {clave}")

        kg_m = float(kg_m)
        if kg_m <= 0:
            raise ValueError(f"Kg/m debe ser positivo: {kg_m}")

        logger.info(f"Kg/m desde BD: {kg_m} kg/m")

        # ========== CÁLCULO DE METROS TOTALES ==========
        metros_totales = (ca * ancho_m) + (ch * alto_m)
        logger.info(f"Metros totales: ({ca} × {ancho_m}) + ({ch} × {alto_m}) = {metros_totales}m")

        # ========== CÁLCULO DE KILOGRAMOS ==========
        kgs_totales = metros_totales * kg_m
        logger.info(f"Kgs totales: {metros_totales}m × {kg_m}kg/m = {kgs_totales}kg")

        # ========== CÁLCULO DE PRECIO UNITARIO ==========
        precio_unitario = kgs_totales * precio_kg
        logger.info(f"Precio unitario: {kgs_totales}kg × ${precio_kg}/kg = ${precio_unitario}")

        # ========== VALIDAR Y PROCESAR PIEZAS ==========
        try:
            piezas_int = int(float(piezas or 1))
            if piezas_int <= 0:
                piezas_int = 1
                logger.warning(f"Número de piezas inválido, usando 1: {piezas}")
        except (ValueError, TypeError):
            piezas_int = 1
            logger.warning(f"Error al convertir piezas, usando 1: {piezas}")

        logger.info(f"Número de piezas: {piezas_int}")

        # ========== CÁLCULO DE IMPORTE TOTAL ==========
        # ✅ FÓRMULA CORRECTA: Importe = P.U. × Piezas
        importe_total = precio_unitario * piezas_int
        logger.info(f"Importe total: ${precio_unitario} × {piezas_int} = ${importe_total}")

        # ========== REDONDEO FINAL ==========
        precio_unitario = round(precio_unitario, 2)
        importe_total = round(importe_total, 2)
        kgs_totales = round(kgs_totales, 3)

        logger.info(f"Resultados finales - P.U.: ${precio_unitario}, "
                    f"Importe: ${importe_total}, Kgs: {kgs_totales}kg")

        return precio_unitario, importe_total, kgs_totales

    except ValueError as ve:
        logger.error(f"Error de validación en herrería: {ve}")
        return 0.0, 0.0, 0.0
    except Exception as e:
        logger.error(f"Error inesperado en compute_herreria: {e}", exc_info=True)
        return 0.0, 0.0, 0.0


def compute_herreria_legacy(
        *,
        svc,
        clave: str,
        piezas: int,
        ancho: float,
        alto: float,
        extra: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Versión legacy que solo retorna (P.U., Importe) para compatibilidad.
    """
    try:
        pu, imp, _ = compute_herreria(
            svc=svc, clave=clave, piezas=piezas,
            ancho=ancho, alto=alto, extra=extra
        )
        return pu, imp
    except Exception as e:
        logger.error(f"Error en compute_herreria_legacy: {e}")
        return 0.0, 0.0


def test_calculo_ejemplo():
    """
    Función de prueba con el ejemplo que debe dar $7,215.00
    """

    class MockSvc:
        def herreria_kg_por_m(self, clave):
            # Para PTR32V, el Kg/m es 6.5
            if clave == "PTR32V":
                return 6.5
            return 5.0

    svc = MockSvc()

    print("\n" + "=" * 70)
    print("PRUEBA DEL CÁLCULO - DEBE DAR $7,215.00")
    print("=" * 70)

    print("DATOS DE ENTRADA:")
    print(f"  Clave: PTR32V")
    print(f"  Piezas: 2")
    print(f"  Ancho: 2.12 m")
    print(f"  Alto: 1.68 m")
    print(f"  Extra: precio_kg=50, ca=2, ch=4")
    print()

    pu, imp, kgs = compute_herreria(
        svc=svc,
        clave="PTR32V",
        piezas=2,
        ancho=2.12,
        alto=1.68,
        extra={
            "precio_kg": 50,
            "ca": 2,
            "ch": 4
        }
    )

    print("CÁLCULO PASO A PASO:")
    print(f"  1. Redondeo Ancho: 2.12 → {_ceil_step(2.12, 0.05)} m")
    print(f"  2. Redondeo Alto: 1.68 → {_ceil_step(1.68, 0.05)} m")
    print(f"  3. Metros totales: (2 × 2.15) + (4 × 1.70) = 4.30 + 6.80 = 11.10 m")
    print(f"  4. Kgs totales: 11.10 m × 6.5 kg/m = 72.15 kg")
    print(f"  5. Precio unitario: 72.15 kg × $50/kg = $3,607.50")
    print(f"  6. Importe total: $3,607.50 × 2 piezas = $7,215.00")
    print()

    print("RESULTADOS:")
    print(f"  Precio Unitario: ${pu:,.2f}")
    print(f"  Importe Total: ${imp:,.2f}")
    print(f"  Kilogramos: {kgs:,.3f} kg")
    print()

    if abs(imp - 7215.00) < 0.01:
        print("✅ ¡PRUEBA EXITOSA! El cálculo coincide con el resultado esperado.")
    else:
        print(f"❌ PRUEBA FALLIDA. Esperado: $7,215.00, Obtenido: ${imp:,.2f}")


if __name__ == "__main__":
    # Ejecutar prueba automática
    test_calculo_ejemplo()