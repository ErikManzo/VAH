# =========================================================
# Archivo: D:\vah\proveedores\data\db.py
# Módulo : Conexión y utilidades SQL Server (pyodbc)
# CORREGIDO: Agregada función insert_and_get_id
# =========================================================
from __future__ import annotations

import os
import pyodbc
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from common.logger_config import get_logger

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
def _build_logger() -> logging.Logger:
    return get_logger("proveedores.data.db")


LOGGER = _build_logger()

# ---------------------------------------------------------
# Configuración
# ---------------------------------------------------------
DEFAULT_SERVER = os.getenv("DB_SERVER", r"DESKTOP-AE60PIU\SQLEXPRESS")
DEFAULT_DB = os.getenv("DB_NAME", "proveedores")
DEFAULT_USER = os.getenv("DB_USER")
DEFAULT_PASSWORD = os.getenv("DB_PASSWORD")

_POSSIBLE_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server Native Client 11.0",
]


def _pick_driver() -> Optional[str]:
    try:
        avail = [d for d in pyodbc.drivers()]
        for name in _POSSIBLE_DRIVERS:
            if name in avail:
                return name
        return avail[-1] if avail else None
    except Exception as e:
        LOGGER.error("Listando drivers ODBC: %s", e)
        return None


_ODBC_DRIVER = _pick_driver()


# ---------------------------------------------------------
# Conexión
# ---------------------------------------------------------
def get_connection(
        database: Optional[str] = None,
        server: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        *, autocommit: bool = False
) -> pyodbc.Connection:
    if not _ODBC_DRIVER:
        raise RuntimeError("No se encontró ningún Driver ODBC de SQL Server instalado.")

    db = database or DEFAULT_DB
    srv = server or DEFAULT_SERVER

    if user and password:
        conn_str = f"DRIVER={{{_ODBC_DRIVER}}};SERVER={srv};DATABASE={db};UID={user};PWD={password};TrustServerCertificate=yes;"
    else:
        conn_str = f"DRIVER={{{_ODBC_DRIVER}}};SERVER={srv};DATABASE={db};Trusted_Connection=yes;TrustServerCertificate=yes;"

    LOGGER.info("Conectando a SQL Server (%s -> %s)", srv, db)
    return pyodbc.connect(conn_str, autocommit=autocommit)


@contextmanager
def db_conn(database: Optional[str] = None, *, autocommit: bool = False):
    try:
        conn = get_connection(database=database, autocommit=autocommit)
        yield conn
        conn.close()
    except Exception as e:
        LOGGER.error("Error en conexión: %s", e)
        raise


# ---------------------------------------------------------
# Consultas
# ---------------------------------------------------------
def fetch_all(sql: str, params: Sequence[Any] | None = None, *, database: Optional[str] = None) -> List[Dict[str, Any]]:
    params = params or []
    with db_conn(database) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows


def fetch_one(sql: str, params: Sequence[Any] | None = None, *, database: Optional[str] = None) -> Optional[
    Dict[str, Any]]:
    params = params or []
    with db_conn(database) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description] if cur.description else []
        row = cur.fetchone()
        if not row:
            return None
        return dict(zip(cols, row))


def execute(sql: str, params: Sequence[Any] | None = None, *, database: Optional[str] = None,
            return_identity: bool = False) -> int | Optional[int]:
    """
    Ejecuta un comando DML.
    Si return_identity=True, intenta obtener el ID insertado.
    """
    params = params or []
    with db_conn(database, autocommit=False) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)

        identity = None
        if return_identity:
            try:
                # Intentar obtener SCOPE_IDENTITY()
                cur.execute("SELECT SCOPE_IDENTITY() as id")
                row = cur.fetchone()
                if row and row[0]:
                    identity = int(row[0])
            except Exception as e:
                LOGGER.warning("No se pudo obtener SCOPE_IDENTITY: %s", e)

        conn.commit()
        return identity if return_identity else cur.rowcount


# =========================================================
# NUEVA FUNCIÓN: insert_and_get_id
# =========================================================
def insert_and_get_id(sql: str, params: Sequence[Any] | None = None, *, database: Optional[str] = None) -> Optional[
    int]:
    """
    Inserta un registro y devuelve el ID generado.
    Usa SCOPE_IDENTITY() para obtener el ID.
    """
    params = params or []
    with db_conn(database, autocommit=False) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)

        # Obtener el ID generado
        cur.execute("SELECT SCOPE_IDENTITY() as id")
        row = cur.fetchone()
        identity = int(row[0]) if row and row[0] else None

        conn.commit()
        return identity
