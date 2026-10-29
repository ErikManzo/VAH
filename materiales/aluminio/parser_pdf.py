# d:\vah\materiales\aluminio\parser_pdf.py

import re
from decimal import Decimal
import pdfplumber

from common.logger_config import get_logger
from .db_manager import DBManager
from .utils import dec2  # helper para convertir a Decimal

logger = get_logger("materiales.aluminio.parser_pdf")

# Largos válidos en el PDF
LARGOS_VALIDOS = {"6.10", "5.50", "5.00", "4.60", "3.66"}

# Clave = primer token numérico a la izquierda
RE_CLAVE = re.compile(r"^\s*(\d{3,6})\b")

def _registro_base(clave: str, descripcion: str, largo: Decimal) -> dict:
    """Crea el esqueleto del registro con todos los campos que exige la BD."""
    z = Decimal("0.00")
    return {
        "clave": clave,
        "descripcion": descripcion,
        "largo": largo,
        "sa": z, "nat": z, "bmo": z,
        "e100": z, "e200": z, "e400": z,   # se llenan desde ELE
        "bco": z, "hue": z, "np": z, "gris": z,
        "cho": z, "ace": z,                # en PDF no vienen; quedan en 0.00
        "madl": z, "madt": z,
    }

def parse_pdf_mateco(path_pdf: str) -> list[dict]:
    """
    Parser robusto para PDF Mateco:
    - Ignora encabezados (* ...) y títulos de columnas
    - Busca largo válido en la línea
    - Asigna precios en orden: SA, NAT, BMO, ELE, BCO, HUESO, NP, GRIS, MADL, MADT
      (ELE se copia a e100, e200, e400)
    """
    regs: list[dict] = []

    with pdfplumber.open(path_pdf) as pdf:
        for page in pdf.pages:
            texto = page.extract_text() or ""
            for raw in texto.splitlines():
                line = raw.strip()

                if not line or line.startswith("*") or line.upper().startswith("CLAVE "):
                    continue

                m = RE_CLAVE.match(line)
                if not m:
                    continue
                clave = m.group(1)

                m_largo = re.search(r"(6\.10|5\.50|5\.00|4\.60|3\.66)", line)
                if not m_largo:
                    continue
                largo = Decimal(m_largo.group(1))

                idx_clave_fin = line.find(clave) + len(clave)
                idx_largo_ini = m_largo.start()
                descripcion = " ".join(line[idx_clave_fin:idx_largo_ini].split())

                resto = line[m_largo.end():].strip()
                valores = [dec2(tok) for tok in resto.split()]

                reg = _registro_base(clave, descripcion, largo)

                orden_pdf = ["sa", "nat", "bmo", "ele", "bco", "hue", "np", "gris", "madl", "madt"]
                for i, val in enumerate(valores[:len(orden_pdf)]):
                    campo = orden_pdf[i]
                    if campo == "ele":
                        reg["e100"] = val
                        reg["e200"] = val
                        reg["e400"] = val
                    else:
                        reg[campo] = val

                regs.append(reg)

    return regs


def importar_pdf_mateco(path_pdf: str, db_name: str = "aluminio") -> int:
    """
    Inserta/actualiza en BD usando DBManager.insertar_o_actualizar.
    ✅ SOLO actualiza precios; no modifica clave, descripción ni largo.
    """
    db = DBManager(db_name=db_name)
    regs = parse_pdf_mateco(path_pdf)
    ok = 0
    for r in regs:
        try:
            precios = {k: r[k] for k in r.keys() if k not in ("clave", "descripcion", "largo")}
            precios["clave"] = r["clave"]
            db.insertar_o_actualizar(precios, update_only_precios=True)
            ok += 1
        except Exception as e:
            print(f"⚠️ Error con clave {r.get('clave')}: {e}")
            logger.exception("Error importando PDF de aluminio para clave=%s", r.get("clave"))
    return ok


#
#
#
