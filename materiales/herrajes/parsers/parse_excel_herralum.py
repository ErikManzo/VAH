


# D:\vah\materiales\herrajes\parsers\parse_excel_herralum.py

"""
Parser de Excel - Proveedor HERRALUM

Lee el archivo Excel y detecta automáticamente:
  - La fila de encabezados (la que tiene más celdas no vacías en las primeras 20 filas)
  - Las columnas mapeadas por el usuario o auto-detectadas
  - Los datos empiezan en la fila siguiente a los encabezados

Reglas de PRECIO UNITARIO:
  - PZ / PZA / PZS / PIEZA -> factor = 1
  - CJ / CAJA              -> 144
  - CT                     -> 100
  - ML                     -> 1000
  - RL                     -> factor variable extraído de la descripción
  - Unidades de empaque:   -> factor = n si desc contiene "(nPZ)"
  - Otros                  -> 1

CONVERSIÓN DE PRECIO:
  - Elimina $, espacios y COMAS (separadores de miles)
  - Convierte el texto limpio a Decimal(10,2)
  - Ej: "2,330.20" -> Decimal('2330.20')

FACTOR RL:
  - Busca patrones: "1600MT", "(280MT)", "8X200MT"
  - Lista ampliada de valores permitidos
  - Si no encuentra factor -> rechazado para corrección manual
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from decimal import Decimal, localcontext, InvalidOperation, ROUND_HALF_UP
import pandas as pd
import re


from common.logger_config import get_logger
logger = get_logger('materiales.herrajes.parsers.parse_excel_herralum')

_DEC2 = Decimal("0.01")
_DEC_ZERO = Decimal("0.00")

_UNIT_DIVISORS_FIXED = {
    "PZ": 1, "PZA": 1, "PZS": 1, "PIEZA": 1,
    "CJ": 144, "CAJA": 144,
    "CT": 100,
    "ML": 1000,
}
_PACK_UNITS = {"CJ", "CAJA", "KT", "KIT", "PAQ", "PACK", "PK", "BOL", "BOLSA"}

# Valores permitidos como factor RL (AMPLIADO)
_RL_ALLOWED = {
    5, 10, 25, 30, 50, 100, 150, 200, 250, 280, 300,
    500, 1000, 1400, 1600, 2000, 5000,
}

_MAX_HEADER_SEARCH_ROWS = 20

def _find_best_header_row(df: pd.DataFrame, max_rows: int = _MAX_HEADER_SEARCH_ROWS) -> int:
    """Encuentra la fila con más celdas no vacías en las primeras `max_rows` filas."""
    search_limit = min(max_rows, len(df))
    best_row = 0
    best_count = 0
    for i in range(search_limit):
        row = df.iloc[i]
        non_null = sum(1 for v in row if pd.notna(v) and str(v).strip() != "")
        if non_null > best_count:
            best_count = non_null
            best_row = i
    return best_row

def _normalize_header(val) -> str:
    """Normaliza un valor de encabezado."""
    if pd.isna(val):
        return ""
    return str(val).strip()

# ============ CONVERSIÓN DE PRECIO ============
def _precio_to_decimal(x) -> Optional[Decimal]:
    """
    Convierte cualquier formato de precio a Decimal(10,2).
    - Elimina $, espacios, y COMAS (separadores de miles)
    - Convierte el texto limpio a Decimal
    - Retorna None si no es convertible
    """
    if pd.isna(x):
        return None
    txt = str(x).strip()
    if txt == "":
        return None

    # Eliminar $, espacios, y TODAS las comas (separadores de miles)
    txt = txt.replace("$", "").replace(" ", "").replace(",", "")

    # Eliminar cualquier caracter que no sea dígito, punto o signo negativo
    txt = re.sub(r"[^0-9\.\-]", "", txt)

    if txt == "" or txt in {".", "-", "-.", ".-"}:
        return None

    with localcontext() as ctx:
        ctx.traps[InvalidOperation] = False
        try:
            d = Decimal(txt)
        except Exception:
            return None
        if not d.is_finite():
            return None
        try:
            d = d.quantize(_DEC2, rounding=ROUND_HALF_UP)
        except InvalidOperation:
            return None
        if not d.is_finite():
            return None
        return d if d >= 0 else None

# ============ FACTOR POR UNIDAD ============
def _extract_pack_from_desc(desc: str) -> Optional[int]:
    """Extrae factor de empaque de descripción: '(nPZ)' -> n."""
    if pd.isna(desc):
        return None
    m = re.search(r"\((\d+)\s*(PZ|PZA|PZS|PIEZA)\)", str(desc).upper())
    try:
        return int(m.group(1)) if m else None
    except Exception:
        return None

def _extract_rl_factor(desc: str) -> Optional[int]:
    """
    Extrae el factor de conversión para RL desde la descripción.

    Busca patrones como:
      - "8X200MT", "8 X 200 MT" -> captura el segundo número
      - "1600MT", "(280MT)", "280 M", "280 MTS"
      - Cualquier número en _RL_ALLOWED como último recurso

    Retorna el factor si está en _RL_ALLOWED, o None si no se encuentra.
    """
    if pd.isna(desc):
        return None
    txt = str(desc).upper()

    # Patrón 1: "8X200MT", "8 X 200 MT", "8*200MT" -> capturar números
    for m in re.finditer(r"(\d+)\s*[Xx\*]\s*(\d+)\s*(?:MT|MTS|M)?", txt):
        val2 = int(m.group(2))
        if val2 in _RL_ALLOWED:
            return val2
        val1 = int(m.group(1))
        if val1 in _RL_ALLOWED:
            return val1

    # Patrón 2: "1600MT", "(280MT)", "280 M", "280 MTS"
    for m in re.finditer(r"\b(\d{1,4})\s*(?:MT|MTS|M)\b", txt):
        val = int(m.group(1))
        if val in _RL_ALLOWED:
            return val

    # Patrón 3: Cualquier número en _RL_ALLOWED (último recurso)
    for m in re.finditer(r"\b(\d{1,4})\b", txt):
        val = int(m.group(1))
        if val in _RL_ALLOWED:
            return val

    return None

def _factor_por_unidad(unidad: str, descripcion: str) -> Optional[int]:
    """Calcula el factor de conversión según la unidad y descripción."""
    um = (str(unidad).strip().upper() if unidad is not None else "")
    if um in _UNIT_DIVISORS_FIXED:
        factor = _UNIT_DIVISORS_FIXED[um]
    elif um == "RL":
        f = _extract_rl_factor(descripcion)
        return f if f and f > 0 else None
    else:
        factor = 1
    if um in _PACK_UNITS:
        n = _extract_pack_from_desc(descripcion)
        if n and n > 0:
            factor = n
    return max(int(factor or 1), 1)

# ============ VALIDACIÓN DE CLAVE ============
_CLAVE_RE = re.compile(r"^[A-Z0-9._\-]+$")

def _clave_valida(x) -> bool:
    """Valida que la clave sea alfanumérica, sin espacios, <= 20 chars."""
    if pd.isna(x):
        return False
    s = str(x).strip().upper()
    if not s:
        return False
    if " " in s:
        return False
    if len(s) > 20:
        return False
    if not _CLAVE_RE.match(s):
        return False
    return True

def _clean_clave(x) -> str:
    """
    Limpia una clave preservando TODOS los caracteres.
    Si pandas leyó un número 100100000.0, lo convierte a "100100000".
    """
    if pd.isna(x):
        return ""
    s = str(x).strip().upper()
    if s.endswith(".0") and len(s) > 2:
        s = s[:-2]
    return s

# ============ PARSER PRINCIPAL ============
def parse_excel_herralum(
        path_xlsx: str,
        sheet_name: Optional[str] = None,
        start_row_excel: Optional[int] = None,
        column_mapping: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Lee el Excel de Herralum y calcula PRECIO UNITARIO.

    Args:
        path_xlsx: Ruta del archivo Excel
        sheet_name: Nombre de la hoja (None = primera)
        start_row_excel: IGNORADO (se detecta automáticamente)
        column_mapping: {"clave": "Parte", "descripcion": "Descripción",
                         "um": "UM", "precio": "Nuevo"}

    Returns:
        (validos, rechazados)
    """
    # Seleccionar hoja
    if sheet_name is None:
        try:
            xlf = pd.ExcelFile(path_xlsx)
            sheet = xlf.sheet_names[0] if xlf.sheet_names else 0
        except Exception:
            sheet = 0
    else:
        sheet = sheet_name

    # ===== PASO 1: Leer TODO como string =====
    df_raw = pd.read_excel(
        path_xlsx,
        sheet_name=sheet,
        header=None,
        engine="openpyxl",
        dtype=str,
        keep_default_na=False,
        na_filter=False,
    )

    if isinstance(df_raw, dict):
        df_raw = next(iter(df_raw.values()))

    df_raw = df_raw.fillna("")

    # ===== PASO 2: Encontrar fila de encabezados =====
    header_row_idx = _find_best_header_row(df_raw)
    headers = [_normalize_header(h) for h in df_raw.iloc[header_row_idx].tolist()]

    # ===== PASO 3: Datos desde fila siguiente =====
    data_start_idx = header_row_idx + 1

    # ===== PASO 4: Buscar columnas por nombre =====
    def _find_col_index(col_name: str) -> Optional[int]:
        if not col_name:
            return None
        col_norm = col_name.strip().lower()
        for i, h in enumerate(headers):
            if h.lower() == col_norm:
                return i
        for i, h in enumerate(headers):
            if col_norm in h.lower():
                return i
        for i, h in enumerate(headers):
            if h.lower() and h.lower() in col_norm:
                return i
        return None

    if column_mapping is None:
        # Auto-detección por contenido
        clave_idx = None
        desc_idx = None
        um_idx = None
        precio_idx = None

        sample_data = df_raw.iloc[data_start_idx:data_start_idx + 50]

        for col_idx in range(len(df_raw.columns)):
            col_vals = sample_data.iloc[:, col_idx].astype(str).str.strip()
            col_vals = col_vals[col_vals != ""]
            if len(col_vals) < 3:
                continue

            col_upper = col_vals.str.upper()

            # UM
            um_set = set(_UNIT_DIVISORS_FIXED.keys()) | {"EA", "JG", "KT", "ST", "MT", "KG", "PAR"}
            if um_idx is None and col_upper.isin(um_set).mean() > 0.3:
                um_idx = col_idx
                continue

            # Clave
            if clave_idx is None:
                no_spaces = (~col_vals.str.contains(" ")).mean()
                alphanum = col_vals.str.match(r"^[A-Za-z0-9._\-]+$").mean()
                avg_len = col_vals.str.len().mean()
                if no_spaces > 0.9 and alphanum > 0.8 and 3 <= avg_len <= 20:
                    clave_idx = col_idx
                    continue

            # Descripción
            if desc_idx is None:
                avg_len = col_vals.str.len().mean()
                with_spaces = col_vals.str.contains(" ").mean()
                if avg_len > 20 and with_spaces > 0.5:
                    desc_idx = col_idx
                    continue

            # Precio
            if precio_idx is None:
                try:
                    numeric = pd.to_numeric(
                        col_vals.str.replace(r"[$,]", "", regex=True),
                        errors="coerce",
                    )
                    valid = numeric.dropna()
                    if len(valid) > len(col_vals) * 0.6 and (valid > 0).mean() > 0.5:
                        precio_idx = col_idx
                except Exception:
                    pass

        df = pd.DataFrame()
        if clave_idx is not None:
            raw_claves = df_raw.iloc[data_start_idx:, clave_idx].reset_index(drop=True)
            df["clave"] = raw_claves.apply(_clean_clave)
        if desc_idx is not None:
            df["descripcion"] = df_raw.iloc[data_start_idx:, desc_idx].reset_index(drop=True)
        if um_idx is not None:
            df["unidad"] = df_raw.iloc[data_start_idx:, um_idx].reset_index(drop=True)
        if precio_idx is not None:
            raw_precios = df_raw.iloc[data_start_idx:, precio_idx].reset_index(drop=True)
            df["precio"] = raw_precios.apply(_precio_to_decimal)
    else:
        clave_idx = _find_col_index(column_mapping.get("clave", ""))
        desc_idx = _find_col_index(column_mapping.get("descripcion", ""))
        um_idx = _find_col_index(column_mapping.get("um", ""))
        precio_idx = _find_col_index(column_mapping.get("precio", ""))

        df = pd.DataFrame()
        if clave_idx is not None:
            raw_claves = df_raw.iloc[data_start_idx:, clave_idx].reset_index(drop=True)
            df["clave"] = raw_claves.apply(_clean_clave)
        if desc_idx is not None:
            df["descripcion"] = df_raw.iloc[data_start_idx:, desc_idx].reset_index(drop=True)
        if um_idx is not None:
            df["unidad"] = df_raw.iloc[data_start_idx:, um_idx].reset_index(drop=True)
        if precio_idx is not None:
            raw_precios = df_raw.iloc[data_start_idx:, precio_idx].reset_index(drop=True)
            df["precio"] = raw_precios.apply(_precio_to_decimal)

    # ===== PASO 5: Validar columnas =====
    required_cols = ["clave", "descripcion", "unidad", "precio"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"No se encontraron las columnas: {', '.join(missing)}.\n"
            f"Encabezados en fila {header_row_idx + 1}: {headers}\n"
            f"Columnas: {list(df.columns)}"
        )

    df = df[df["clave"].astype(str).str.strip() != ""]
    df = df.dropna(how="all")

    # ===== PASO 6: Normalizar =====
    df["clave"] = df["clave"].astype(str).apply(_clean_clave)
    df["descripcion"] = df["descripcion"].astype(str).str.strip()
    df["unidad"] = df["unidad"].astype(str).str.strip().str.upper()

    # Factores por unidad
    factores = df.apply(
        lambda r: _factor_por_unidad(r.get("unidad", ""), r.get("descripcion", "")),
        axis=1,
    )

    # Precio unitario = precio_lista / factor
    def _precio_unitario(p: Optional[Decimal], f: Optional[int]) -> Optional[Decimal]:
        if p is None or f is None or f <= 0:
            return None
        with localcontext() as ctx:
            ctx.traps[InvalidOperation] = False
            try:
                tmp = p / Decimal(f)
            except InvalidOperation:
                return None
            if not tmp.is_finite():
                return None
            try:
                val = tmp.quantize(_DEC2, rounding=ROUND_HALF_UP)
            except InvalidOperation:
                return None
            if not val.is_finite():
                return None
        return val if val >= 0 else None

    precio_unit = [_precio_unitario(p, f) for p, f in zip(df["precio"], factores)]

    # ===== PASO 7: Motivos de rechazo =====
    motivo = pd.Series("", index=df.index, dtype="string")

    m = ~df["clave"].apply(_clave_valida)
    motivo.loc[m] = "clave_larga_o_invalida"

    m = df["descripcion"].isna() | (df["descripcion"].astype(str).str.strip() == "")
    motivo.loc[m & (motivo == "")] = "descripcion_vacia"

    mask_rl = df["unidad"].astype(str).str.upper().eq("RL")
    m = mask_rl & pd.Series([(f is None) for f in factores], index=df.index)
    motivo.loc[m & (motivo == "")] = "unidad_rl_factor_desconocido"

    m = pd.Series([(pu is None) for pu in precio_unit], index=df.index)
    motivo.loc[m & (motivo == "")] = "precio_invalido_o_cero"

    # ===== PASO 8: Válidos y rechazados =====
    valid_idx = motivo.index[motivo.eq("")]
    validos: List[Dict] = []
    for i in valid_idx:
        pu = precio_unit[i]
        validos.append({
            "clave": str(df.at[i, "clave"]),
            "descripcion": str(df.at[i, "descripcion"]),
            "precio": pu if pu is not None else _DEC_ZERO,
        })

    rechazados: List[Dict] = []
    rej_idx = motivo.index[motivo.ne("")]
    for i in rej_idx:
        rechazados.append({
            "row": int(i) + data_start_idx + 1,
            "clave": "" if pd.isna(df.at[i, "clave"]) else str(df.at[i, "clave"]),
            "descripcion": "" if pd.isna(df.at[i, "descripcion"]) else str(df.at[i, "descripcion"]),
            "unidad": "" if pd.isna(df.at[i, "unidad"]) else str(df.at[i, "unidad"]),
            "precio": "" if pd.isna(df.at[i, "precio"]) else str(df.at[i, "precio"]),
            "motivo": str(motivo.at[i]),
        })

    return validos, rechazados