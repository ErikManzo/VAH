# d:\vah\materiales\aluminio\restricciones.py
"""
Contiene las validaciones comunes: is_title_like, desc_bloqueada, registro_todo_ceros, CLAVES_IGNORADAS, etc.

Los parsers importan estas funciones, así mantienes consistencia entre Excel y PDF.
"""


import re
from decimal import Decimal
from .utils import dec2, CAMPOS_PRECIO_BD   # ⬅️ cambio aquí

# =====================================================
# === RESTRICCIONES / VALIDACIONES DE NEGOCIO
# =====================================================

# Palabras/etiquetas que indican títulos o grupos (no artículos)
PALABRAS_TITULO = {
    "FINESTRA","RAGAZZA","SERIE 1400 ABATIBLE","MOSQUITERO UNIVERSAL",
    "SERIE EUROPEA","PERFILES DE ALUMINIO","LISTA DE PRECIOS","FISARMONICA",
    "GRIGLIAS","CUADRICULA","BAÑOS","ANGULOS, TEES Y SOLERA","DUELAS Y BOLSAS",
    "TUBOS CUADRADOS","SERIE 3500 CORREDIZA","SERIE 4600 ","SERIE 10000 ",
    "SERIE 6000","SERIE 10500 ELEVABLE","TUBOS RECTANGULARES","MOSQUITERO COLGANTE",
    "CANCEL DE BAÑO TORINO","SOLAR",'BOLSA 2"','BOLSA 3"', 'CORREDIZA 1.5"', 'CORREDIZA 2"',
    'CORREDIZA 3"',"BATIENTES","PUERTA","PORTA VIDRIOS","ANGULOS Y TEES","MOSQUITEROS","MOLDURAS",
    "LOUVER Y REPIZONES","ZOCLO HERCULITE","VENTILA DE PROYECCION","PASAMANOS","TUBOS REDONDOS",
    "CANALES PARA DOMO3","VITRINAS","VARIOS"
}

# Patrones de descripciones que deben ignorarse (líneas de bolsa, títulos varios)
PATRONES_DESC_BLOQUEADAS = [
    r'\bBOLSA\s*DE\s*2["”]?\b',
    r'\bBOLSA\s*2["”]?\b',
]

# Claves que deben ignorarse siempre
CLAVES_IGNORADAS = {"XXX", "YYY"}  # ⚠️ Ajusta según tus reglas reales

def is_title_like(txt: str) -> bool:
    """Detecta títulos/separadores de lista (no artículos)."""
    if not txt:
        return False
    t = str(txt).strip().upper()
    return t in PALABRAS_TITULO or t.startswith("SERIE ")

def desc_bloqueada(desc: str) -> bool:
    """Detecta descripciones que deben ignorarse (ej. BOLSA DE 2")."""
    if not desc:
        return False
    d = str(desc).strip().upper()
    for pat in PATRONES_DESC_BLOQUEADAS:
        if re.search(pat, d, flags=re.IGNORECASE):
            return True
    return False

def registro_todo_ceros(reg: dict) -> bool:
    """True si todos los campos de precio resultaron 0.00 (es grupo/corte)."""
    for k in CAMPOS_PRECIO_BD:
        if dec2(reg.get(k, 0)) != Decimal("0.00"):
            return False
    return True

#
#
#