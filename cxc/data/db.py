# -*- coding: utf-8 -*-
import pyodbc
from common.logger_config import get_logger

logger = get_logger("cxc.data.db")

_SERVER = r'DESKTOP-AE60PIU\SQLEXPRESS'
_DATABASE = 'cxc'
_DRIVER = '{ODBC Driver 17 for SQL Server}'

_CONNECTION_STRING = (
    f'DRIVER={_DRIVER};'
    f'SERVER={_SERVER};'
    f'DATABASE={_DATABASE};'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
)

def get_connection() -> pyodbc.Connection:
    """
    Crea y retorna una nueva conexión a la base de datos.
    Cada llamada crea una conexión independiente.
    """
    try:
        conn = pyodbc.connect(_CONNECTION_STRING, timeout=10)
        return conn
    except pyodbc.Error as e:
        logger.exception("Error de conexion a base de datos CXC")
        raise RuntimeError(f"ERROR DE CONEXIÓN A BASE DE DATOS:\n{str(e)}")
