# d:\vah\materiales\aluminio\utils.py
"""
Funciones generales: dec2, normalize_largo, natural_key_for_clave, ordenar_registros_asc, merge_max, norm_header.
Así evitas duplicación y centralizas la lógica común.
"""

from decimal import Decimal
import re

# =====================================================
# === CAMPOS DE PRECIO EN BD
# =====================================================
CAMPOS_PRECIO_BD = [
    "sa", "nat", "bmo",
    "e100", "e200", "e400",
    "bco", "hue", "np",
    "gris", "cho", "ace",
    "madl", "madt"
]

# =====================================================
# === FUNCIONES DE APOYO
# =====================================================

def dec2(val) -> Decimal:
    """Convierte a Decimal de forma segura."""
    try:
        if val is None:
            return Decimal("0.00")
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return Decimal("0.00")

def merge_max(reg1: dict, reg2: dict, campos: list) -> dict:
    """Combina dos registros conservando el valor máximo por campo."""
    result = reg1.copy()
    for c in campos:
        v1 = dec2(reg1.get(c, 0))
        v2 = dec2(reg2.get(c, 0))
        result[c] = max(v1, v2)
    return result

def ordenar_registros_asc(registros: list) -> list:
    """Ordena por clave ascendente usando lógica natural (números y letras)."""
    return sorted(registros, key=lambda r: natural_key_for_clave(r.get("clave", "")))

def natural_key_for_clave(clave: str):
    """Convierte clave en lista de tokens para ordenar natural (ej. 100A < 100B < 101)."""
    return [int(text) if text.isdigit() else text for text in re.split(r"(\d+)", clave)]

def norm_header(val: str) -> str:
    """Normaliza encabezados de Excel (mayúsculas y sin espacios extra)."""
    if not val:
        return ""
    return str(val).strip().upper().replace(".", "").replace("-", "").replace("_", "")
#
#
#