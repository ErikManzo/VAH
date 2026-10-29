# D:\vah\materiales\vidrio\db_manager.py
"""
Acceso a datos para el módulo Vidrio.

BD:      vidrio
Tabla:   dbo.materiales_vidrio  (Clave PK, Descripcion, Precio)
Driver:  ODBC Driver 18 for SQL Server
Auth:    Windows Authentication (Trusted_Connection=yes)
"""

import os
import pyodbc
from contextlib import contextmanager
from typing import Dict, List, Tuple

DEFAULT_SERVER = r"DESKTOP-AE60PIU\SQLEXPRESS"
DEFAULT_DATABASE = "vidrio"
DEFAULT_TABLE = "dbo.materiales_vidrio"

class DBManager:
    def __init__(self,
                 server: str = None,
                 database: str = DEFAULT_DATABASE,
                 table: str = DEFAULT_TABLE):
        self.server = server or DEFAULT_SERVER
        self.database = database
        self.table = table

    # ---------- conexión ----------
    @contextmanager
    def _get_conn(self):
        cs = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"Trusted_Connection=yes;"
            f"Encrypt=yes;TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(cs, timeout=10)
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ---------- helpers ----------
    def listar_todos(self) -> List[Dict]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT Clave, Descripcion, Precio FROM {self.table};")
            rows = cur.fetchall()
            return [
                {"clave": r[0] or "", "descripcion": r[1] or "", "precio": r[2] if r[2] is not None else 0}
                for r in rows
            ]

    def existe_clave(self, clave: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT 1 FROM {self.table} WHERE Clave = ?;", (clave,))
            return cur.fetchone() is not None

    def insertar(self, reg: Dict):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO {self.table} (Clave, Descripcion, Precio) VALUES (?,?,?);",
                (reg["clave"], reg.get("descripcion"), float(reg.get("precio", 0)))
            )
            conn.commit()

    def actualizar_por_clave(self, clave_original: str, reg: Dict):
        with self._get_conn() as conn:
            cur = conn.cursor()
            # Si cambia la clave, validar duplicidad
            if clave_original != reg["clave"]:
                cur.execute(f"SELECT 1 FROM {self.table} WHERE Clave = ?;", (reg["clave"],))
                if cur.fetchone():
                    raise ValueError(f"La clave '{reg['clave']}' ya existe.")
            cur.execute(
                f"UPDATE {self.table} "
                f"SET Clave = ?, Descripcion = ?, Precio = ? "
                f"WHERE Clave = ?;",
                (reg["clave"], reg.get("descripcion"), float(reg.get("precio", 0)), clave_original)
            )
            conn.commit()

    def eliminar_por_clave(self, clave: str):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self.table} WHERE Clave = ?;", (clave,))
            conn.commit()
#
#
#