# =========================================================
# Archivo: D:\vah\clientes\data\db.py
# Conexión a la base de datos SQL Server (Windows Auth)
# =========================================================
import pyodbc
from common.logger_config import get_logger

logger = get_logger("clientes.data.db")

def get_connection():
    """
    Retorna una conexión a la base de datos SQL Server usando autenticación de Windows.
    Si falla, lanza una excepción clara para depuración.
    """
    server = r'DESKTOP-AE60PIU\SQLEXPRESS'  # Servidor e instancia
    database = 'clientes'                   # Base de datos
    driver = '{ODBC Driver 17 for SQL Server}'  # Ajustar si tienes otra versión

    conn_str = (
        f'DRIVER={driver};'
        f'SERVER={server};'
        f'DATABASE={database};'
        'Trusted_Connection=yes;'            # Autenticación de Windows
        'TrustServerCertificate=yes;'
    )

    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        return conn
    except pyodbc.Error as e:
        logger.exception("Error al conectar con SQL Server para Clientes")
        raise RuntimeError(f"❌ Error al conectar con SQL Server: {e}")
