# -*- coding: utf-8 -*-
"""
DBManager — acceso a aluminio.dbo.materiales_aluminio
Ruta sugerida:
    D:\vah\materiales\aluminio\db_manager.py

API:
    listar_todos() -> List[dict]
    insertar_o_actualizar(material: dict, use_merge: bool, reporte: dict) -> dict
    eliminar_por_clave(clave: str) -> None
    existe_clave(clave: str) -> bool
    obtener_por_clave(clave: str) -> dict | None

Reglas:
    - Guardado manual (use_merge=False) respeta exactamente lo capturado (0.00 permitido).
    - Importación (use_merge=True) usa merge_max para NO bajar precios ya existentes en BD.

Actualizaciones:
    - Se corrige la llamada a merge_max(): ahora recibe CAMPOS_PRECIO_BD como tercer argumento.
      (Elimina: TypeError: merge_max() missing 1 required positional argument: 'campos')
    - insertar_o_actualizar() acepta "reporte" para contar insertado/actualizado/sin_cambios.
    - No se ejecuta UPDATE si no hay cambios reales contra la BD.
    - En modo importación, si vienen descripción y largo válidos, se actualizan
      sin afectar la regla de no bajar precios existentes.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

import pyodbc

from materiales.aluminio.utils import CAMPOS_PRECIO_BD, merge_max


class DBManager:
    def __init__(self, db_name: str = "aluminio", conn_str: Optional[str] = None) -> None:
        self.conn_str = conn_str or (
            "Driver={ODBC Driver 18 for SQL Server}; "
            "Server=DESKTOP-AE60PIU\\SQLEXPRESS; "
            f"Database={db_name}; "
            "Trusted_Connection=yes; "
            "Encrypt=no; "
        )

    # ---------- utilidades ----------
    @staticmethod
    def _to_dec(v) -> Decimal:
        """
        Convierte un valor a Decimal con 2 decimales.
        Si viene vacío, None o inválido, devuelve 0.00.
        """
        if v is None or v == "":
            return Decimal("0.00")
        try:
            return Decimal(str(v)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        except Exception:
            return Decimal("0.00")

    @classmethod
    def _merge_importacion(cls, actual: Dict, nuevo: Dict, campos: List[str]) -> Dict:
        """
        Merge de respaldo para importación.
        Regla:
            - Solo sube precios si el precio nuevo es mayor al actual.
            - Conserva el precio actual si el nuevo es menor o igual.
            - Actualiza descripción y largo si vienen válidos.
        """
        combinado = dict(actual or {})

        clave_nueva = str(nuevo.get("clave") or "").strip().upper()
        if clave_nueva:
            combinado["clave"] = clave_nueva

        descripcion_nueva = str(nuevo.get("descripcion") or "").strip()
        if descripcion_nueva:
            combinado["descripcion"] = descripcion_nueva

        largo_nuevo = nuevo.get("largo")
        if largo_nuevo is not None:
            largo_dec = cls._to_dec(largo_nuevo)
            if largo_dec > Decimal("0.00"):
                combinado["largo"] = largo_dec

        for campo in campos:
            valor_nuevo = cls._to_dec(nuevo.get(campo))
            valor_actual = cls._to_dec((actual or {}).get(campo))
            if valor_nuevo > valor_actual:
                combinado[campo] = valor_nuevo
            else:
                combinado[campo] = valor_actual

        return combinado

    # ---------- utilitarias ----------
    def existe_clave(self, clave: str) -> bool:
        clave = (clave or "").strip().upper()
        if not clave:
            return False
        with pyodbc.connect(self.conn_str) as cn:
            cur = cn.cursor()
            cur.execute(
                "SELECT 1 FROM dbo.materiales_aluminio WITH (NOLOCK) WHERE clave = ?",
                (clave,)
            )
            return cur.fetchone() is not None

    def obtener_por_clave(self, clave: str) -> Optional[Dict]:
        clave = (clave or "").strip().upper()
        if not clave:
            return None
        sql = (
            "SELECT clave, descripcion, largo, " + ", ".join(CAMPOS_PRECIO_BD) +
            " FROM dbo.materiales_aluminio WITH (NOLOCK) WHERE clave = ?"
        )
        with pyodbc.connect(self.conn_str) as cn:
            cur = cn.cursor()
            cur.execute(sql, (clave,))
            row = cur.fetchone()
            if not row:
                return None
            d = {
                "clave": row[0],
                "descripcion": row[1],
                "largo": self._to_dec(row[2]),
            }
            for i, c in enumerate(CAMPOS_PRECIO_BD, start=3):
                d[c] = self._to_dec(row[i])
            return d

    # ---------- API principal ----------
    def listar_todos(self) -> List[Dict]:
        sql = (
            "SELECT clave, descripcion, largo, " + ", ".join(CAMPOS_PRECIO_BD) +
            " FROM dbo.materiales_aluminio WITH (NOLOCK)"
        )
        with pyodbc.connect(self.conn_str) as cn:
            cur = cn.cursor()
            cur.execute(sql)
            res = []
            for row in cur.fetchall():
                d = {
                    "clave": row[0],
                    "descripcion": row[1],
                    "largo": self._to_dec(row[2]),
                }
                for i, c in enumerate(CAMPOS_PRECIO_BD, start=3):
                    d[c] = self._to_dec(row[i])
                res.append(d)
            return res

    def eliminar_por_clave(self, clave: str) -> None:
        clave = (clave or "").strip().upper()
        if not clave:
            return
        with pyodbc.connect(self.conn_str) as cn:
            cur = cn.cursor()
            cur.execute("DELETE FROM dbo.materiales_aluminio WHERE clave = ?", (clave,))
            cn.commit()

    def insertar_o_actualizar(
        self,
        material: Dict,
        use_merge: bool = False,
        reporte: Optional[Dict] = None,
    ) -> Dict:
        """
        Inserta o actualiza un material.

        use_merge=True  → regla de importación: solo sube precios (merge_max).
        use_merge=False → guardado manual: respeta exactamente lo capturado.

        reporte (opcional) → dict que acumula:
            {"insertado": n, "actualizado": n, "sin_cambios": n}
        """
        clave = str(material.get("clave") or "").strip().upper()
        if not clave:
            raise ValueError("Clave requerida")

        limpio = {
            "clave": clave,
            "descripcion": (material.get("descripcion") or "").strip(),
            "largo": self._to_dec(material.get("largo")),
        }
        for c in CAMPOS_PRECIO_BD:
            limpio[c] = self._to_dec(material.get(c))

        with pyodbc.connect(self.conn_str) as cn:
            cur = cn.cursor()
            cur.execute(
                "SELECT clave, descripcion, largo, " + ", ".join(CAMPOS_PRECIO_BD) +
                " FROM dbo.materiales_aluminio WITH (UPDLOCK, ROWLOCK) WHERE clave = ?",
                (clave,)
            )
            row = cur.fetchone()

            actual = None
            if row:
                actual = {
                    "clave": row[0],
                    "descripcion": row[1],
                    "largo": self._to_dec(row[2]),
                }
                for i, c in enumerate(CAMPOS_PRECIO_BD, start=3):
                    actual[c] = self._to_dec(row[i])

            # ---- construir combinado ----
            if use_merge and actual:
                # Corrección principal: merge_max requiere la lista de campos.
                try:
                    combinado = merge_max(actual, limpio, CAMPOS_PRECIO_BD)
                except TypeError:
                    combinado = self._merge_importacion(actual, limpio, CAMPOS_PRECIO_BD)
                if not isinstance(combinado, dict):
                    combinado = self._merge_importacion(actual, limpio, CAMPOS_PRECIO_BD)

                # Asegurar clave y completar campos no monetarios.
                combinado = dict(actual, **combinado)
                combinado["clave"] = clave
                if limpio.get("descripcion"):
                    combinado["descripcion"] = limpio["descripcion"]
                if limpio.get("largo") is not None and limpio["largo"] > Decimal("0.00"):
                    combinado["largo"] = limpio["largo"]
                for c in CAMPOS_PRECIO_BD:
                    combinado[c] = self._to_dec(combinado.get(c, actual.get(c)))
            else:
                combinado = limpio

            # ---- detectar si hay cambio real contra la BD ----
            cambio = False
            if actual:
                if str(actual.get("descripcion", "")).strip() != str(combinado.get("descripcion", "")).strip():
                    cambio = True
                if self._to_dec(actual.get("largo")) != self._to_dec(combinado.get("largo")):
                    cambio = True
                if not cambio:
                    for c in CAMPOS_PRECIO_BD:
                        if self._to_dec(actual.get(c)) != self._to_dec(combinado.get(c)):
                            cambio = True
                            break

            # ---- ejecutar INSERT / UPDATE / omitir ----
            if actual:
                if cambio:
                    sql_up = (
                        "UPDATE dbo.materiales_aluminio SET "
                        + ", ".join([f"{c} = ?" for c in CAMPOS_PRECIO_BD])
                        + ", descripcion = ?, largo = ? WHERE clave = ?"
                    )
                    vals = [combinado[c] for c in CAMPOS_PRECIO_BD] + [
                        combinado["descripcion"],
                        combinado["largo"],
                        combinado["clave"],
                    ]
                    cur.execute(sql_up, vals)
                    accion = "actualizado"
                else:
                    accion = "sin_cambios"
            else:
                cols = ["clave", "descripcion", "largo"] + list(CAMPOS_PRECIO_BD)
                placeholders = ",".join(["?"] * len(cols))
                sql_in = (
                    f"INSERT INTO dbo.materiales_aluminio ({', '.join(cols)}) "
                    f"VALUES ({placeholders})"
                )
                vals = [combinado[c] for c in cols]
                cur.execute(sql_in, vals)
                accion = "insertado"

            cn.commit()

            if reporte is not None:
                reporte[accion] = reporte.get(accion, 0) + 1

            return combinado