# D:\vah\materiales\aluminio\db.py
import pyodbc
import logging
from logging.handlers import RotatingFileHandler
from materiales.aluminio.utils import CAMPOS_PRECIO_BD
from decimal import Decimal

# =============================
# CONFIGURACIÓN DE LOGGING
# =============================
logger = logging.getLogger("aluminio_db")
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(
    "aluminio_db.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# =============================
# CONEXIÓN A SQL SERVER
# =============================
def get_connection(db_name: str = "aluminio"):
    """
    Abre una conexión a SQL Server Express.
    Ajusta DRIVER y SERVER según tu configuración.
    """
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=localhost\\SQLEXPRESS;"
            f"DATABASE={db_name};"
            f"Trusted_Connection=yes;"
        )
        return conn
    except Exception:
        logger.exception("❌ Error al conectar a la base de datos")
        raise

# =============================
# UPSERT DE MATERIALES
# =============================
def upsert_material(data: dict, db_name: str, update_only_precios: bool = False):
    """
    Inserta o actualiza un material.
    - Si update_only_precios=True, solo actualiza columnas de precios.
    """
    conn = get_connection(db_name)
    cursor = conn.cursor()

    if update_only_precios:
        # Solo actualizar precios
        set_clause = ", ".join([f"{k} = ?" for k in CAMPOS_PRECIO_BD])
        values = [data[k] for k in CAMPOS_PRECIO_BD]
        values.append(data["clave"])
        cursor.execute(
            f"UPDATE materiales_aluminio SET {set_clause} WHERE clave = ?",
            values
        )
    else:
        # Inserción o actualización completa (clave, descripcion, largo, precios)
        columnas = ["clave", "descripcion", "largo"] + CAMPOS_PRECIO_BD
        placeholders = ",".join("?" for _ in columnas)
        values = [data.get(c) for c in columnas]
        cursor.execute(f"""
            MERGE materiales_aluminio AS t
            USING (SELECT ? AS clave) AS s
            ON t.clave = s.clave
            WHEN MATCHED THEN
                UPDATE SET {",".join(f"{c}=?" for c in columnas[1:])}
            WHEN NOT MATCHED THEN
                INSERT ({",".join(columnas)}) VALUES ({placeholders});
        """, values * 2)  # se duplica la lista para el MERGE
    conn.commit()
    conn.close()

# =============================
# OBTENER MATERIAL POR CLAVE
# =============================
def get_material_by_clave(clave: str, db_name: str):
    """
    Devuelve un dict con los datos de un material identificado por clave.
    Incluye clave, descripcion, largo y todos los campos de precio definidos en CAMPOS_PRECIO_BD.
    Si no existe, retorna None.
    """
    def to_dec(v):
        try:
            return Decimal(str(v).replace(",", "").strip())
        except Exception:
            return Decimal("0.00")

    conn = get_connection(db_name)
    cursor = conn.cursor()
    try:
        columnas = ["clave", "descripcion", "largo"] + CAMPOS_PRECIO_BD
        cols_sql = ", ".join(columnas)
        row = cursor.execute(
            f"SELECT {cols_sql} FROM materiales_aluminio WHERE clave = ?",
            (clave,)
        ).fetchone()

        if not row:
            return None

        reg = {}
        for i, c in enumerate(columnas):
            val = row[i]
            if c in CAMPOS_PRECIO_BD or c == "largo":
                reg[c] = to_dec(val)
            else:
                reg[c] = str(val).strip() if val is not None else ""

        return reg
    except Exception:
        logger.exception(f"❌ Error al obtener material con clave {clave}")
        return None
    finally:
        conn.close()



#
#
#