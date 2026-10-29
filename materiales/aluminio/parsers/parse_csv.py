# D:\vah\materiales\aluminio\parsers\parse_csv.py

"""
para probar importaciones sin abrir la GUI

Script de pruebas rápidas para parsers de Excel, PDF y CSV.
No abre GUI, solo imprime resultados básicos en consola.
"""

import csv
from decimal import Decimal

from ..utils import dec2, merge_max, CAMPOS_PRECIO_BD
from ..restricciones import (
    is_title_like, desc_bloqueada, registro_todo_ceros, CLAVES_IGNORADAS
)


# =====================================================
# === PARSER DE CSV
# =====================================================

def parse_csv_generico(filename: str, delimiter: str = ",") -> list[dict]:
    """
    Parser genérico para archivos CSV de materiales de aluminio.
    - Espera encabezados tipo Excel (CLAVE/CLAVES, DESCRIPCION, SA, NAT, ...).
    - Aplica las mismas restricciones que Excel/PDF.
    - Consolida por clave conservando el mayor precio por campo.
    """
    regs_consol: dict[str, dict] = {}

    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        if not reader.fieldnames:
            return []

        for row in reader:
            # --- Clave
            clave = (row.get("CLAVE") or row.get("CLAVES") or "").strip().upper()
            if not clave or clave in CLAVES_IGNORADAS:
                continue

            # --- Descripción
            desc = (row.get("DESCRIPCION") or row.get("DESCRIPCIÓN") or "").strip()
            if is_title_like(desc) or desc_bloqueada(desc):
                continue

            # --- Base del registro
            reg = {"clave": clave, "descripcion": desc, "largo": Decimal("6.10")}
            for k in CAMPOS_PRECIO_BD:
                reg[k] = Decimal("0.00")

            # --- Volcado de precios
            for campo in CAMPOS_PRECIO_BD:
                val = dec2(row.get(campo.upper()))
                reg[campo] = max(reg[campo], val)

            if registro_todo_ceros(reg):
                continue

            if clave not in regs_consol:
                regs_consol[clave] = reg
            else:
                regs_consol[clave] = merge_max(regs_consol[clave], reg, CAMPOS_PRECIO_BD)

    return list(regs_consol.values())

#
#
#