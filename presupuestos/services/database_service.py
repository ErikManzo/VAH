# -*- coding: utf-8 -*-
import os
import json
import contextlib
from typing import Optional, List, TYPE_CHECKING

# Import para type checking únicamente
if TYPE_CHECKING:
    import pyodbc

try:
    import pyodbc
except ImportError:
    pyodbc = None

# Cargar configuración desde archivo externo (D:\VAH\config.json)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')

def cargar_configuracion():
    """Carga la configuración desde config.json"""
    config_default = {
        "sql_server": "DESKTOP-AE60PIU\SQLEXPRESS",
        "database": "presupuestos",
        "timeout": 10
    }
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Mezclar con valores por defecto
                for key, value in config_default.items():
                    if key not in config:
                        config[key] = value
                return config
    except Exception as e:
        print(f"[Config] Error leyendo config.json: {e}")
    return config_default

# Cargar configuración al iniciar
CONFIG = cargar_configuracion()
SQL_SERVER = os.environ.get("VAH_SQLSERVER", CONFIG.get("sql_server", ""))
DB_TIMEOUT = CONFIG.get("timeout", 10)
DB_NAME = CONFIG.get("database", "presupuestos")

CANDIDATE_SERVERS = [
    SQL_SERVER,
    r"(local)\SQLEXPRESS",
    r".\SQLEXPRESS",
    r"localhost\SQLEXPRESS",
    r"127.0.0.1,1433",
]

class DatabaseService:
    def __init__(self) -> None:
        self._cnx: Optional["pyodbc.Connection"] = None

    def connect(self):
        if self._cnx:
            return self._cnx
        if pyodbc is None:
            raise RuntimeError("pyodbc no disponible. Instala ODBC Driver 17/18 for SQL Server.")
        errors: List[str] = []
        for driver in ("{ODBC Driver 18 for SQL Server}", "{ODBC Driver 17 for SQL Server}"):
            for server in [s for s in CANDIDATE_SERVERS if s]:
                try:
                    cnx_str = (
                        f"DRIVER={driver};"
                        f"SERVER={server};"
                        f"DATABASE={DB_NAME};"
                        "Encrypt=no;"
                        "TrustServerCertificate=yes;"
                        "Trusted_Connection=yes;"
                        f"Connection Timeout={DB_TIMEOUT};"
                    )
                    self._cnx = pyodbc.connect(cnx_str)
                    return self._cnx
                except Exception as e:
                    errors.append(f"{driver}@{server}: {e}")
        raise RuntimeError("No se pudo conectar a SQL Server. Intentos: " + " | ".join(errors))

    @contextlib.contextmanager
    def cursor(self):
        cnx = self.connect()
        cur = cnx.cursor()
        try:
            yield cur
            cnx.commit()  # ← Commit automático si no hay excepción
        except Exception:
            cnx.rollback()  # ← Rollback si hay error
            raise
        finally:
            cur.close()

    def fetchone(self, sql: str, params: list) -> Optional[tuple]:
        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def fetchall(self, sql: str, params: list) -> List[tuple]:
        with self.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())