


# D:\vah\materiales\plasticos\utils.py
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, localcontext


from common.logger_config import get_logger
logger = get_logger('materiales.plasticos.utils')

_DEC2 = Decimal("0.01")

def dec2(x) -> Decimal:
    """
    Convierte x a Decimal con 2 decimales, redondeo HALF_UP.
    Acepta strings con $, comas de miles, coma decimal, etc.
    """
    if x is None:
        return Decimal("0.00")
    s = str(x).strip().replace("$", "").replace(" ", "")
    # normaliza coma decimal
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s and "." not in s:
        s = s.replace(".", "").replace(",", ".")
    # deja dígitos, signo y punto
    import re
    s = re.sub(r"[^0-9\.\-]", "", s)
    if s == "" or s in {".", "-", "-.", ".-"}:
        return Decimal("0.00")
    with localcontext() as ctx:
        ctx.traps[InvalidOperation] = False
        try:
            d = Decimal(s)
        except Exception:
            return Decimal("0.00")
        try:
            return d.quantize(_DEC2, rounding=ROUND_HALF_UP)
        except InvalidOperation:
            return Decimal("0.00")
#
#
#