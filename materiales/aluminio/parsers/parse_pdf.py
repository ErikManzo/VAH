# D:\vah\materiales\aluminio\parsers\parse_pdf.py

import logging
import pdfplumber
from decimal import Decimal, InvalidOperation

from materiales.aluminio.db import upsert_material, get_material_by_clave
from materiales.aluminio.utils import CAMPOS_PRECIO_BD, merge_max

# =============================
# LOGGING LOCAL
# =============================
def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.FileHandler("parse_pdf.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger

log = get_logger("parse_pdf")

# =============================
# FUNCIONES AUXILIARES
# =============================
LARGOS_VALIDOS = {"6.10", "5.50", "5.00", "4.60", "3.66"}
CLAVES_OMITIDAS = {"G-40", "G-28"}

def a_decimal(txt: str) -> Decimal:
    """Convierte texto a Decimal, o 0.00 si falla."""
    try:
        return Decimal(str(txt).replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return Decimal("0.00")

def iter_pdf_lines(pdf_path: str):
    """Generador que devuelve cada línea de texto de un PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                yield line.strip()

# =============================
# PARSER PDF MATECO (PRAGMÁTICO)
# =============================
def parse_pdf_mateco(pdf_path: str):
    registros = []

    for line in iter_pdf_lines(pdf_path):
        if not line or line.startswith("*"):
            continue
        if any(m in line.upper() for m in ["CLAVE", "DESCRIPCION", "LARGO"]):
            continue
        if any(m in line.upper() for m in ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
                                           "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]):
            continue

        tokens = line.split()
        if len(tokens) < 3:
            continue

        # Buscar el índice del largo
        largo_idx = None
        for i, tok in enumerate(tokens):
            if tok in LARGOS_VALIDOS:
                largo_idx = i
                break
        if largo_idx is None:
            continue

        clave = tokens[0]
        if clave in CLAVES_OMITIDAS or not clave[0].isdigit():
            continue

        try:
            largo = Decimal(tokens[largo_idx])
        except InvalidOperation:
            continue

        descripcion = " ".join(tokens[1:largo_idx])
        valores = tokens[largo_idx + 1 :]

        # Inicializar registro
        reg = {"clave": clave, "descripcion": descripcion, "largo": largo}
        for k in CAMPOS_PRECIO_BD:
            reg[k] = Decimal("0.00")

        # Asignar valores en orden fijo
        campos = ["sa", "nat", "bmo", "ele", "bco", "hue", "np", "gris", "madl", "madt"]
        for i, campo in enumerate(campos):
            if i >= len(valores):
                continue
            val = a_decimal(valores[i])
            if campo == "ele":
                reg["e100"] = max(reg["e100"], val)
                reg["e200"] = max(reg["e200"], val)
                reg["e400"] = max(reg["e400"], val)
            else:
                reg[campo] = max(reg[campo], val)

        registros.append(reg)

    return registros

# =============================
# IMPORTADOR PDF
# =============================
def importar_pdf_mateco(pdf_path: str, db_name: str = None):
    """
    ✅ Importa desde PDF Mateco.
    - Si db_name está definido:
        * Actualiza SOLO los precios (no clave, descripción, largo).
        * Consolida con valores ya existentes en la BD usando merge_max.
    - Si no: devuelve lista de registros parseados.
    """
    registros = parse_pdf_mateco(pdf_path)

    if db_name:
        total = 0
        for reg in registros:
            try:
                existente = get_material_by_clave(reg["clave"], db_name)
                if existente:
                    consolidado = merge_max(existente, reg, CAMPOS_PRECIO_BD)
                    precios = {k: consolidado[k] for k in CAMPOS_PRECIO_BD}
                    precios["clave"] = reg["clave"]
                else:
                    precios = {k: reg[k] for k in CAMPOS_PRECIO_BD}
                    precios["clave"] = reg["clave"]

                upsert_material(precios, db_name, update_only_precios=True)
                total += 1
            except Exception as e:
                log.error(f"❌ Error al actualizar precios de {reg['clave']}: {e}", exc_info=True)
        log.info(f"✅ Importados desde PDF (consolidando máximos): {total}")
        return total
    else:
        return registros


#
#
#