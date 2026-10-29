"""
Funciones utilitarias para el módulo Herrajes
"""

from decimal import Decimal
from typing import Optional, Tuple
import pandas as pd
import re


from common.logger_config import get_logger
logger = get_logger('materiales.herrajes.utils')

def dec2(valor) -> Decimal:
    """
    Convierte un valor de texto/numérico a Decimal con 2 decimales.
    """
    try:
        return Decimal(str(valor)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")

def ordenar_registros_asc(registros: list[dict]) -> list[dict]:
    """
    Ordena registros por clave ascendente.
    """
    return sorted(registros, key=lambda r: r.get("clave", ""))

# ============== AUTO-DETECCIÓN DE COLUMNAS PARA IMPORTACIÓN ==============

# Palabras clave para detectar cada tipo de columna (insensible a mayúsculas)
_CLAVE_KEYWORDS = [
    "clave", "parte", "código", "codigo", "sku", "id", "clv",
    "cve", "key", "code", "producto_id", "item", "numero_parte",
]
_DESCRIPCION_KEYWORDS = [
    "descripcion", "descripción", "nombre", "producto", "concepto",
    "description", "name", "articulo", "artículo", "material",
]
_UM_KEYWORDS = [
    "um", "unidad", "u.m.", "medida", "unit", "udm", "u_m",
    "unidad_medida", "presentacion", "presentación",
]
_PRECIO_KEYWORDS = [
    "nuevo", "precio", "neto", "actual", "costo", "importe",
    "p.u.", "pu", "precio_unitario", "precio_lista", "price",
    "costo_unitario", "valor", "total",
]

# Patrones para validar datos en columnas
_UM_VALUES = {
    "PZ", "PZA", "PZS", "PIEZA", "PIEZAS",
    "CJ", "CAJA", "CAJAS",
    "CT", "CTO", "CIENTO", "CIENTOS",
    "ML", "MIL", "MILLAR",
    "RL", "ROLLO", "ROLLOS",
    "KT", "KIT", "KITS",
    "JG", "JUEGO", "JUEGOS",
    "PAQ", "PACK", "PAQUETE",
    "BOL", "BOLSA", "BOLSAS",
    "EA", "CADA UNO",
    "ST", "SET",
    "MT", "METRO", "METROS",
    "KG", "KILO", "KILOGRAMO",
    "PAR", "PARES",
}

def _normalize_header(val: str) -> str:
    """Normaliza un encabezado para comparación: minúsculas, sin espacios extra, sin acentos."""
    if not isinstance(val, str):
        return ""
    # Quitar acentos
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
        "ü": "u", "Ü": "u", "ñ": "n", "Ñ": "n",
    }
    for old, new in replacements.items():
        val = val.replace(old, new)
    return val.strip().lower()

def _is_clave_column(series: pd.Series) -> float:
    """
    Calcula un score (0-1) de qué tan probable es que esta columna sea la clave.
    - Valores sin espacios
    - Longitud promedio entre 5 y 20
    - Alfanuméricos con guiones/puntos
    - Pocos valores nulos
    - Valores únicos
    """
    s = series.dropna().astype(str)
    if len(s) < 3:
        return 0.0

    score = 0.0

    # Sin espacios
    with_spaces = s.str.contains(" ", na=False).mean()
    score += (1.0 - with_spaces) * 0.3

    # Longitud promedio adecuada
    avg_len = s.str.len().mean()
    if 5 <= avg_len <= 20:
        score += 0.2
    elif 3 <= avg_len <= 25:
        score += 0.1

    # Alfanuméricos (permitiendo guiones, puntos, guiones bajos)
    alphanum = s.str.match(r"^[A-Za-z0-9._\-]+$", na=False).mean()
    score += alphanum * 0.3

    # Alta unicidad (las claves suelen ser únicas)
    uniqueness = len(s.unique()) / len(s)
    score += uniqueness * 0.2

    return score

def _is_descripcion_column(series: pd.Series) -> float:
    """
    Calcula un score (0-1) de qué tan probable es que esta columna sea la descripción.
    - Texto largo (>15 chars promedio)
    - Contiene espacios
    - Variedad de caracteres
    """
    s = series.dropna().astype(str)
    if len(s) < 3:
        return 0.0

    score = 0.0

    # Longitud promedio larga
    avg_len = s.str.len().mean()
    if avg_len > 30:
        score += 0.4
    elif avg_len > 15:
        score += 0.25
    elif avg_len > 10:
        score += 0.1

    # Contiene espacios
    with_spaces = s.str.contains(" ", na=False).mean()
    score += with_spaces * 0.3

    # No es numérico
    try:
        numeric_ratio = pd.to_numeric(s, errors="coerce").notna().mean()
        score += (1.0 - numeric_ratio) * 0.3
    except Exception:
        score += 0.3

    return score

def _is_um_column(series: pd.Series) -> float:
    """
    Calcula un score (0-1) de qué tan probable es que esta columna sea la UM.
    - Valores cortos (1-4 caracteres)
    - Coinciden con valores UM conocidos
    """
    s = series.dropna().astype(str).str.strip().str.upper()
    if len(s) < 3:
        return 0.0

    score = 0.0

    # Valores cortos
    avg_len = s.str.len().mean()
    if 1 <= avg_len <= 5:
        score += 0.3
    elif avg_len <= 8:
        score += 0.15

    # Coincidencia con valores UM conocidos
    um_match = s.isin(_UM_VALUES).mean()
    score += um_match * 0.5

    # Pocos valores únicos (las UM se repiten)
    uniqueness = len(s.unique()) / len(s)
    if uniqueness < 0.1:
        score += 0.2
    elif uniqueness < 0.3:
        score += 0.1

    return score

def _is_precio_column(series: pd.Series) -> float:
    """
    Calcula un score (0-1) de qué tan probable es que esta columna sea el precio.
    - Valores numéricos
    - Con decimales
    - > 0
    """
    s = series.dropna()
    if len(s) < 3:
        return 0.0

    score = 0.0

    # Intentar convertir a numérico
    try:
        numeric = pd.to_numeric(s.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
        valid = numeric.dropna()
        if len(valid) < len(s) * 0.5:
            return 0.0

        # Mayoría positivos
        positive_ratio = (valid > 0).mean()
        score += positive_ratio * 0.4

        # Tienen decimales (los precios suelen tener .00 o .##)
        has_decimals = valid.apply(lambda x: float(x) != int(float(x))).mean()
        score += has_decimals * 0.2

        # Rango razonable de precios
        mean_val = valid.mean()
        if 0.1 <= mean_val <= 100000:
            score += 0.2

        # Variedad de valores
        uniqueness = len(valid.unique()) / len(valid)
        if uniqueness > 0.3:
            score += 0.2

    except Exception:
        return 0.0

    return score

def detectar_columnas_excel(
        df_head: pd.DataFrame,
        headers: list,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Detecta automáticamente las columnas de Clave, Descripción, UM y Precio
    en un DataFrame de Excel.

    Args:
        df_head: DataFrame con las primeras filas del Excel (incluyendo encabezados)
        headers: Lista de nombres de columna (encabezados)

    Returns:
        Tuple con (nombre_columna_clave, nombre_columna_descripcion,
                   nombre_columna_um, nombre_columna_precio)
        None en cada posición si no se pudo detectar.
    """
    result = [None, None, None, None]  # clave, desc, um, precio

    # Primera pasada: buscar por nombre de encabezado
    header_matches = {
        "clave": [],
        "descripcion": [],
        "um": [],
        "precio": [],
    }

    for i, header in enumerate(headers):
        norm = _normalize_header(str(header))
        col_name = str(header).strip()

        # Buscar coincidencias exactas o parciales en keywords
        for kw in _CLAVE_KEYWORDS:
            if kw in norm or norm in kw:
                header_matches["clave"].append((i, col_name, 0.9))
                break

        for kw in _DESCRIPCION_KEYWORDS:
            if kw in norm or norm in kw:
                header_matches["descripcion"].append((i, col_name, 0.9))
                break

        for kw in _UM_KEYWORDS:
            if kw in norm or norm in kw:
                header_matches["um"].append((i, col_name, 0.9))
                break

        for kw in _PRECIO_KEYWORDS:
            if kw in norm or norm in kw:
                header_matches["precio"].append((i, col_name, 0.9))
                break

    # Si encontramos coincidencias por nombre, usar la mejor (primera)
    for field, matches in header_matches.items():
        if matches:
            # Ordenar por score descendente
            matches.sort(key=lambda x: x[2], reverse=True)
            idx = ["clave", "descripcion", "um", "precio"].index(field)
            result[idx] = matches[0][1]

    # Segunda pasada: si algún campo no se detectó, analizar por contenido
    if None in result:
        for i, header in enumerate(headers):
            col_name = str(header).strip()
            if i < len(df_head.columns):
                series = df_head.iloc[:, i]

                # Solo evaluar columnas no asignadas ya
                if result[0] is None:
                    score = _is_clave_column(series)
                    if score > 0.5:
                        result[0] = col_name

                if result[1] is None:
                    score = _is_descripcion_column(series)
                    if score > 0.5:
                        result[1] = col_name

                if result[2] is None:
                    score = _is_um_column(series)
                    if score > 0.5:
                        result[2] = col_name

                if result[3] is None:
                    score = _is_precio_column(series)
                    if score > 0.5:
                        result[3] = col_name

    return tuple(result)