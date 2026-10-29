# -*- coding: utf-8 -*-
# D:\vah\materiales\vidrio\cargar_excel_vidrio.py
r"""
Importador Excel → SQL Server para VIDRIO (dbo.materiales_vidrio).

Campos esperados (nombres flexibles):
- Clave
- Descripción / Descripcion / Nombre / Artículo / Articulo / Desc / ...
- Precio

Robustez:
- Detecta el encabezado aunque no esté en la primera fila.
- Acepta acentos y variantes (Descripción/Descripcion, Artículo/Articulo).
- Convierte “Precio” a número (admite coma/punto, $ y miles).
- Deduplica por Clave dentro del archivo:
    Descripción = primera no vacía
    Precio      = MAX del lote (evita bajar precios si hay duplicados)
- MERGE set-based:
    MATCHED      → UPDATE (coalesce desc, T.Precio = MAX(T.Precio, S.Precio))
    NOT MATCHED  → INSERT
- Si no encuentra la columna de descripción por nombre, la **infiera**:
    busca la primera columna de **texto** que no sea Clave ni Precio.
- Genera CSV con rechazados en D:\vah\logs\rechazados_vidrio_YYYYMMDD_HHMMSS.csv
- Imprime en consola las columnas mapeadas: Clave, Descripción, Precio.

Uso:
    python -m materiales.vidrio.cargar_excel_vidrio
    (usa la ruta por defecto)
o:
    python -m materiales.vidrio.cargar_excel_vidrio "C:\ruta\vidrio.xlsx" "NombreDeHoja"

Requisitos:
    pip install pandas openpyxl pyodbc
"""

from __future__ import annotations

import os, sys, csv, datetime as dt, re
from typing import Optional, Tuple, List, Dict

import pandas as pd
import numpy as np
import pyodbc
import unicodedata
from common.logger_config import get_logger

logger = get_logger("materiales.vidrio.cargar_excel")

# -------- Config --------
DEFAULT_XLSX = r"C:\Users\Personal\OneDrive\Escritorio\vidrio.xlsx"

# Conexión/tabla (igual a tus módulos)
DEFAULT_SERVER   = r"DESKTOP-AE60PIU\SQLEXPRESS"
DEFAULT_DATABASE = "vidrio"
DEFAULT_TABLE    = "dbo.materiales_vidrio"

# ------------------------ utilidades ------------------------
def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _canon(s) -> str:
    if s is None: return ""
    s = str(s).strip()
    s = _strip_accents(s).lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _coerce_num(x) -> Optional[float]:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip().replace("$", "").replace(" ", "")
    # coma/punto
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s and "." not in s:
        s = s.replace(".", "").replace(",", ".")
    s = re.sub(r"[^0-9\.\-]", "", s)
    if s in ("", ".", "-", "-.", ".-"):
        return None
    try:
        return float(s)
    except Exception:
        return None

def _find_header_row(df: pd.DataFrame) -> int:
    """Busca fila con 'Clave' y ('Descripcion'|'Descripción'|'Nombre'|'Articulo'/'Artículo') y 'Precio'."""
    targets_desc = {"descripcion", "descripción", "nombre", "articulo", "artículo", "desc"}
    targets_precio = {"precio", "precio unitario", "p.u.", "pu", "importe", "monto", "valor", "costo"}
    for i in range(min(30, len(df))):
        row = [_canon(v) for v in df.iloc[i].tolist()]
        if "clave" in row and (targets_desc & set(row)) and (targets_precio & set(row)):
            return i
    # fallback: clave + algún número (si el nombre de precio es raro)
    for i in range(min(30, len(df))):
        row = [_canon(v) for v in df.iloc[i].tolist()]
        if "clave" in row:
            return i
    return 0

def _load_excel(file_path: str, sheet_name: Optional[str]) -> pd.DataFrame:
    """
    Lee Excel con o sin nombre de hoja:
      - Si sheet_name viene vacío/None → primera hoja (índice 0).
      - Si sheet_name es nombre o índice → esa hoja.
      - Si read_excel devuelve un dict → toma la primera hoja.
    """
    sheet_key = 0 if (sheet_name is None or str(sheet_name).strip() == "") else sheet_name

    raw = pd.read_excel(
        file_path,
        sheet_name=sheet_key,      # puede ser 0, int, o str
        header=None,
        dtype=object,
        engine="openpyxl"
    )
    if isinstance(raw, dict):
        raw = next(iter(raw.values()))

    hdr = _find_header_row(raw)
    header = [str(x).strip() for x in raw.iloc[hdr].tolist()]
    df = raw.iloc[hdr+1:].copy()
    df.columns = header
    df.reset_index(drop=True, inplace=True)
    return df

def _guess_text_column(df: pd.DataFrame, exclude: set) -> Optional[str]:
    """
    Elige la primera columna que parezca de TEXTO (no numérica) y no esté en exclude.
    Criterio: en una muestra de hasta 100 filas, ≥60% valores no numéricos no vacíos.
    """
    sample_size = min(100, len(df))
    for col in df.columns:
        if col in exclude:
            continue
        serie = df[col].head(sample_size)
        nonnum = 0; nonempty = 0
        for v in serie:
            if v is None or (isinstance(v, float) and np.isnan(v)):
                continue
            nonempty += 1
            if _coerce_num(v) is None:
                nonnum += 1
        if nonempty > 0 and (nonnum / nonempty) >= 0.6:
            return col
    return None

def _pick_columns(df: pd.DataFrame) -> Tuple[str, str, str]:
    """Devuelve nombres reales de columnas: (clave_col, desc_col, precio_col) con tolerancia y fallback."""
    name_by_canon = { _canon(c): c for c in df.columns }

    # Clave (obligatoria)
    if "clave" not in name_by_canon:
        raise RuntimeError("No encontré columna 'Clave' en el encabezado.")
    clave_col = name_by_canon["clave"]

    # Precio (obligatoria por nombre o inferencia)
    precio_syns = ("precio","precio unitario","p.u.","pu","importe","monto","valor","costo")
    precio_col = None
    for syn in precio_syns:
        if syn in name_by_canon:
            precio_col = name_by_canon[syn]
            break
    if not precio_col:
        # si no hay nombre claro, intenta la última columna con suficientes números
        numeric_candidates = []
        for col in df.columns:
            sample = df[col].head(50).apply(_coerce_num)
            if sample.notna().sum() >= max(5, int(len(sample)*0.3)):
                numeric_candidates.append(col)
        if numeric_candidates:
            precio_col = numeric_candidates[-1]
        else:
            raise RuntimeError("No encontré una columna apropiada para 'Precio'.")

    # Descripción (flexible + fallback)
    desc_syns = (
        "descripcion","descripción","nombre","articulo","artículo",
        "desc","descrip","descripcion corta","descripcion larga","nombre articulo","nombre del articulo"
    )
    desc_col = None
    for syn in desc_syns:
        if syn in name_by_canon:
            desc_col = name_by_canon[syn]
            break

    if not desc_col:
        # Fallback: detectar columna de texto que no sea Clave ni Precio
        exclude = {clave_col, precio_col}
        desc_col = _guess_text_column(df, exclude)
        if not desc_col:
            remaining = [c for c in df.columns if c not in exclude]
            if len(remaining) == 1:
                desc_col = remaining[0]
            else:
                raise RuntimeError(
                    "No encontré columna de Descripción/Nombre y no pude inferir una columna de texto."
                )

    return clave_col, desc_col, precio_col

def _prepare_rows(df: pd.DataFrame, clave_col: str, desc_col: str, precio_col: str) -> Tuple[List[Tuple[str,str,float]], List[Dict]]:
    rows = []
    rechazados = []
    for idx, row in df.iterrows():
        clave = str(row.get(clave_col) or "").strip()
        desc  = str(row.get(desc_col) or "").strip()
        precio = _coerce_num(row.get(precio_col))
        if not clave:
            rechazados.append({"motivo":"sin_clave","fila":int(idx)+1,"clave":clave,"descripcion":desc,"valor":row.get(precio_col)}); continue
        if len(clave) > 20:
            rechazados.append({"motivo":"clave>20","fila":int(idx)+1,"clave":clave,"descripcion":desc,"valor":row.get(precio_col)}); continue
        if len(desc) > 100:
            desc = desc[:100]
        if precio is None:
            rechazados.append({"motivo":"precio_invalido","fila":int(idx)+1,"clave":clave,"descripcion":desc,"valor":row.get(precio_col)}); continue
        rows.append((clave, desc if desc else None, round(float(precio),2)))
    return rows, rechazados

def _save_rejected(rechazados: List[Dict]) -> Optional[str]:
    if not rechazados:
        return None
    os.makedirs(r"D:\vah\logs", exist_ok=True)
    fn = fr"D:\vah\logs\rechazados_vidrio_{dt.datetime.now():%Y%m%d_%H%M%S}.csv"
    with open(fn, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["motivo","fila","clave","descripcion","valor"])
        w.writeheader(); w.writerows(rechazados)
    return fn

def _bulk_merge(rows: List[Tuple[str,str,float]]) -> Tuple[int,int]:
    """Carga rows a #imp y hace MERGE contra dbo.materiales_vidrio (mantiene PRECIO más alto)."""
    if not rows: return (0,0)
    cs = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DEFAULT_SERVER};"
        f"DATABASE={DEFAULT_DATABASE};"
        f"Trusted_Connection=yes;"
        f"Encrypt=yes;TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(cs, timeout=20)
    try:
        cur = conn.cursor()
        cur.execute("""
            IF OBJECT_ID('tempdb..#imp') IS NOT NULL DROP TABLE #imp;
            CREATE TABLE #imp(
              Clave       varchar(20)  NOT NULL,
              Descripcion varchar(100) NULL,
              Precio      decimal(10,2) NOT NULL
            );
        """)
        cur.fast_executemany = True
        cur.executemany("INSERT INTO #imp(Clave,Descripcion,Precio) VALUES (?,?,?);", rows)

        merge_sql = f"""
            ;WITH SRC AS (
              SELECT
                Clave,
                MIN(CASE WHEN Descripcion IS NOT NULL AND LTRIM(RTRIM(Descripcion))<>'' THEN Descripcion END) AS Descripcion,
                MAX(Precio) AS Precio
              FROM #imp
              GROUP BY Clave
            )
            MERGE {DEFAULT_TABLE} AS T
            USING SRC AS S
              ON T.Clave = S.Clave
            WHEN MATCHED THEN
              UPDATE SET
                T.Descripcion = COALESCE(S.Descripcion, T.Descripcion),
                T.Precio      = CASE WHEN S.Precio > T.Precio THEN S.Precio ELSE T.Precio END
            WHEN NOT MATCHED BY TARGET THEN
              INSERT(Clave,Descripcion,Precio)
              VALUES(S.Clave,S.Descripcion,S.Precio)
            OUTPUT $action AS accion;
        """
        cur.execute(merge_sql)
        actions = [r[0] for r in cur.fetchall()]
        conn.commit()
        return sum(1 for a in actions if a=="INSERT"), sum(1 for a in actions if a=="UPDATE")
    finally:
        try: conn.close()
        except Exception: pass

def importar(file_path: str, sheet_name: Optional[str]=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No existe el archivo: {file_path}")

    df = _load_excel(file_path, sheet_name)
    clave_col, desc_col, precio_col = _pick_columns(df)

    # --- INFO: columnas detectadas
    print("Columnas detectadas →",
          f"Clave: '{clave_col}' | Descripción: '{desc_col}' | Precio: '{precio_col}'")
    logger.info(
        "Columnas detectadas en importacion de vidrio: clave=%s descripcion=%s precio=%s",
        clave_col,
        desc_col,
        precio_col,
    )

    rows, rechazados = _prepare_rows(df, clave_col, desc_col, precio_col)

    insertados, actualizados = _bulk_merge(rows)
    rej = _save_rejected(rechazados)

    print("=== Importación VIDRIO ===")
    print(f"Archivo: {file_path}")
    print(f"Válidos: {len(rows)}  |  Insertados: {insertados}  |  Actualizados: {actualizados}")
    print(f"Rechazados: {len(rechazados)}")
    logger.info(
        "Importacion VIDRIO completada: archivo=%s validos=%s insertados=%s actualizados=%s rechazados=%s",
        file_path,
        len(rows),
        insertados,
        actualizados,
        len(rechazados),
    )
    if rej: print(f"Detalle rechazados: {rej}")
    if rej:
        logger.warning("Detalle de rechazados VIDRIO: %s", rej)

# -------- CLI --------
if __name__ == "__main__":
    path = DEFAULT_XLSX if len(sys.argv) < 2 else sys.argv[1]
    hoja = None if len(sys.argv) < 3 else sys.argv[2]
    importar(path, hoja)
