


# D:\vah\materiales\herrajes\parsers\parse_excel_profilo.py
# -*- coding: utf-8 -*-
"""
Parser de Excel - Proveedor PROFILO (hoja de herrajes).

- Columna 2 -> clave   (0-based: df[2])
- Columna 3 -> descripcion (df[3])
- Columna 5 -> precio (df[5])
- Vectorizado, tolera $/comas/coma decimal.
- Devuelve (validos, rechazados) para diagnóstico.

Dependencias: pandas, openpyxl
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
import pandas as pd
import re


from common.logger_config import get_logger
logger = get_logger('materiales.herrajes.parsers.parse_excel_profilo')

_DEC2 = Decimal("0.01")

def _precio_decimal_series(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Normaliza una serie de precios a Decimal; si no es válido deja NaN y anota motivo.
    (Corregido: maneja pd.NA explícitamente para evitar "boolean value of NA is ambiguous".)
    """
    # Convertimos a dtype "string" (puede contener pd.NA)
    s = series.astype("string")

    # Normalización básica (preserva NA)
    s = s.str.strip()
    s = s.str.replace("$", "", regex=False).str.replace(" ", "", regex=False)

    # Casos con coma y punto: asumimos coma = miles -> quitamos comas
    mask_both = s.str.contains(",", na=False) & s.str.contains(r"\.", regex=True, na=False)
    s.loc[mask_both] = s.loc[mask_both].str.replace(",", "", regex=False)

    # Solo coma: tratar como decimal (y quitar puntos de miles)
    mask_coma = s.str.contains(",", na=False) & (~s.str.contains(r"\.", regex=True, na=False))
    s.loc[mask_coma] = s.loc[mask_coma].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)

    # Dejar solo dígitos, punto y signo
    s = s.str.replace(r"[^0-9\.\-]", "", regex=True)

    motivos = pd.Series("", index=s.index, dtype="string")

    def _to_dec(x) -> Optional[Decimal]:
        # --- MANEJO EXPLÍCITO DE NA ---
        if pd.isna(x):  # cubre None, NaN y pd.NA
            return None
        xs = str(x)
        if xs == "" or xs in {".", "-", "-.", ".-"}:
            return None
        try:
            d = Decimal(xs).quantize(_DEC2)
            return d if d > 0 else None
        except Exception:
            return None

    dec = s.map(_to_dec)
    motivos.loc[dec.isna()] = "precio_invalido_o_cero"
    return dec, motivos

def parse_excel_profilo(path_xlsx: str, sheet_name: Optional[str] = None) -> Tuple[List[Dict], List[Dict]]:
    # Elegir hoja: 'HERRAJES' si existe; o la primera que contenga 'HERRA'; si no, la 1ª
    xl = pd.ExcelFile(path_xlsx)
    if sheet_name is None:
        sheet = next((n for n in xl.sheet_names if "HERRA" in n.upper()), None)
        sheet = sheet or ("HERRAJES" if "HERRAJES" in xl.sheet_names else xl.sheet_names[0])
    else:
        sheet = sheet_name

    # Leemos sin encabezados
    df = pd.read_excel(path_xlsx, sheet_name=sheet, header=None, dtype={2: "string", 3: "string"})

    out = pd.DataFrame({
        "clave": df.get(2).astype("string").str.strip().str.upper(),
        "descripcion": df.get(3).astype("string").str.strip(),
        "precio_raw": df.get(5)
    }).dropna(how="all")

    # Normalizar precio
    precios, motivo_precio = _precio_decimal_series(out["precio_raw"])
    out["precio"] = precios
    out["motivo"] = motivo_precio

    # Motivos adicionales (manejo explícito de NA)
    out.loc[out["clave"].isna() | (out["clave"] == ""), "motivo"] = "clave_vacia"
    out.loc[out["descripcion"].isna() | (out["descripcion"] == ""), "motivo"] = "descripcion_vacia"

    # Válidos y rechazados
    validos_df = out[(out["motivo"] == "") & out["precio"].notna()][["clave", "descripcion", "precio"]].copy()
    rechaz_df = out[out["motivo"] != ""].copy()
    rechaz_df["row"] = rechaz_df.index + 1  # fila "humana" aprox.

    # A listas de dicts (sin NA)
    validos = [
        {"clave": str(r["clave"]), "descripcion": str(r["descripcion"]), "precio": r["precio"]}
        for _, r in validos_df.iterrows()
    ]
    rechazados = [
        {
            "row": int(r["row"]),
            "clave": ("" if pd.isna(r["clave"]) else str(r["clave"])),
            "descripcion": ("" if pd.isna(r["descripcion"]) else str(r["descripcion"])),
            "precio": r["precio_raw"],
            "motivo": str(r["motivo"]),
        }
        for _, r in rechaz_df.iterrows()
    ]

    return validos, rechazados

#
#