


# D:\vah\materiales\herrajes\db_manager.py
# -*- coding: utf-8 -*-
r"""
DB Manager para módulo Herrajes (SQL Server).
Uso típico:
  Servidor: DESKTOP-AE60PIU\SQLEXPRESS
  Autenticación: Windows (Trusted_Connection=yes)
  Cifrado: Encrypt=yes; TrustServerCertificate=yes
"""

from __future__ import annotations
from typing import List, Dict, Tuple
from decimal import Decimal
import pyodbc


from common.logger_config import get_logger
logger = get_logger('materiales.herrajes.db_manager')

class DBManager:
    def __init__(
            self,
            server: str = r"DESKTOP-AE60PIU\SQLEXPRESS",
            database: str = "herrajes",
            table: str = "dbo.materiales_herraje",
    ):
        self.server = server
        self.database = database
        self.table = table if "." in table else f"dbo.{table}"

    def _get_conn(self):
        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            "Trusted_Connection=yes;"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str, timeout=5)

    # ================ Lecturas =================
    def listar_todos(self) -> List[Dict]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT Clave, Descripcion, Precio FROM {self.table} ORDER BY Clave;")
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def buscar(self, texto: str) -> List[Dict]:
        like = f"%{texto}%"
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT Clave, Descripcion, Precio
                FROM {self.table}
                WHERE Clave LIKE ? OR Descripcion LIKE ?
                ORDER BY Clave;
                """,
                (like, like),
            )
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def existe_clave(self, clave: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT 1 FROM {self.table} WHERE Clave = ?;", (clave,))
            return cur.fetchone() is not None

    def insertar(self, reg: Dict):
        with self._get_conn() as conn:
            cur = conn.cursor()
            precio = float(reg["precio"]) if reg.get("precio") is not None else 0.0
            cur.execute(
                f"INSERT INTO {self.table} (Clave, Descripcion, Precio) VALUES (?,?,?);",
                (reg["clave"], reg["descripcion"], precio),
            )
            conn.commit()

    def actualizar_por_clave(self, clave_anterior: str, reg: Dict):
        with self._get_conn() as conn:
            cur = conn.cursor()
            precio = float(reg["precio"]) if reg.get("precio") is not None else 0.0
            cur.execute(
                f"UPDATE {self.table} "
                f"SET Clave=?, Descripcion=?, Precio=? "
                f"WHERE Clave=?;",
                (reg["clave"], reg["descripcion"], precio, clave_anterior),
            )
            conn.commit()

    def eliminar_por_clave(self, clave: str):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self.table} WHERE Clave = ?;", (clave,))
            conn.commit()

    def insertar_o_actualizar(self, reg: Dict):
        with self._get_conn() as conn:
            cur = conn.cursor()
            precio = float(reg["precio"]) if reg.get("precio") is not None else 0.0
            cur.execute(f"SELECT 1 FROM {self.table} WHERE Clave = ?;", (reg["clave"],))
            if cur.fetchone():
                cur.execute(
                    f"UPDATE {self.table} SET Descripcion=?, Precio=? WHERE Clave=?;",
                    (reg["descripcion"], precio, reg["clave"]),
                )
            else:
                cur.execute(
                    f"INSERT INTO {self.table} (Clave, Descripcion, Precio) VALUES (?,?,?);",
                    (reg["clave"], reg["descripcion"], precio),
                )
            conn.commit()

    # ======== Upsert masivo con MERGE (CORREGIDO - maneja NULL) ========
    def bulk_upsert_max_precio(self, registros: list[dict]) -> tuple[int, int]:
        """
        Upsert masivo con deduplicación de origen.
        - Precio = MAX(S.Precio) por clave
        - MERGE: MATCHED -> Precio = MAX(T.Precio, S.Precio) manejando NULL
                 NOT MATCHED -> INSERT

        CORREGIDO: Si T.Precio es NULL, se actualiza con S.Precio.
        """
        if not registros:
            return (0, 0)

        rows = []
        for r in registros:
            clave = str(r["clave"]).strip().upper()
            desc = (str(r["descripcion"]).strip() if r.get("descripcion") is not None else None)
            precio_raw = r.get("precio")
            if precio_raw is None:
                precio = 0.0
            elif isinstance(precio_raw, Decimal):
                precio = float(precio_raw)
            else:
                precio = float(precio_raw)
            rows.append((clave, desc, precio))

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.fast_executemany = True

            cur.execute("""
                IF OBJECT_ID('tempdb..#imp') IS NOT NULL DROP TABLE #imp;
                CREATE TABLE #imp (
                    Clave       varchar(20)  NOT NULL,
                    Descripcion varchar(100) NULL,
                    Precio      decimal(10,2) NULL
                );
            """)
            cur.executemany("INSERT INTO #imp (Clave,Descripcion,Precio) VALUES (?,?,?);", rows)

            cur.execute(r"""
                IF OBJECT_ID('tempdb..#imp2') IS NOT NULL DROP TABLE #imp2;
                ;WITH C AS (
                    SELECT
                        i.Clave,
                        i.Descripcion,
                        MAX(i.Precio) OVER (PARTITION BY i.Clave) AS PrecioMax,
                        ROW_NUMBER() OVER (
                            PARTITION BY i.Clave
                            ORDER BY
                                CASE
                                    WHEN i.Descripcion IS NULL OR LTRIM(RTRIM(i.Descripcion)) = '' THEN 1
                                    ELSE 0
                                END ASC,
                                LEN(i.Descripcion) DESC
                        ) AS rn
                    FROM #imp AS i
                )
                SELECT
                    Clave,
                    Descripcion = CASE WHEN rn = 1 THEN Descripcion END,
                    Precio      = PrecioMax
                INTO #imp2
                FROM C
                WHERE rn = 1;
            """)

            # CORREGIDO: Manejar NULL en T.Precio
            merge_sql = f"""
                MERGE {self.table} AS T
                USING #imp2 AS S
                  ON T.Clave = S.Clave
                WHEN MATCHED THEN
                  UPDATE SET
                      T.Descripcion = CASE
                          WHEN S.Descripcion IS NOT NULL AND LTRIM(RTRIM(S.Descripcion)) <> ''
                               THEN S.Descripcion ELSE T.Descripcion END,
                      T.Precio = CASE 
                          WHEN T.Precio IS NULL THEN S.Precio
                          WHEN S.Precio > T.Precio THEN S.Precio 
                          ELSE T.Precio 
                      END
                WHEN NOT MATCHED BY TARGET THEN
                  INSERT (Clave, Descripcion, Precio)
                  VALUES (S.Clave, S.Descripcion, S.Precio)
                OUTPUT $action AS accion;
            """
            cur.execute(merge_sql)
            actions = [row[0] for row in cur.fetchall()]

            inserted = sum(1 for a in actions if a == 'INSERT')
            updated = sum(1 for a in actions if a == 'UPDATE')
            conn.commit()
            return (inserted, updated)