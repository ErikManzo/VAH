"""
Parser de archivos CSV para importar herrajes
"""

import csv
from materiales.herrajes.utils import dec2


from common.logger_config import get_logger
logger = get_logger('materiales.herrajes.parsers.parse_csv')

def parse_csv_generico(path: str) -> list[dict]:
    """
    Lee un archivo CSV y lo convierte en lista de registros de herrajes.
    Se espera que el CSV tenga encabezados: clave, descripcion, precio
    """
    registros = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            registros.append({
                "clave": row.get("clave", "").strip().upper(),
                "descripcion": row.get("descripcion", "").strip(),
                "precio": dec2(row.get("precio", "0.00")),
            })
    return registros
#
#
#