# =========================================================
# Archivo: D:\vah\proveedores\repositories\proveedor_repository.py
# SIMPLIFICADO: Sin imports problemáticos
# =========================================================
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from common.logger_config import get_logger
from proveedores.data.db import fetch_all, fetch_one, execute, insert_and_get_id


# ---------------------------------------------------------
# Logger
# ---------------------------------------------------------
def _build_logger() -> logging.Logger:
    return get_logger("proveedores.repositories.proveedor_repository")


LOGGER = _build_logger()

# ---------------------------------------------------------
# Columnas para INSERT (excluyendo id)
# ---------------------------------------------------------
_COLS_INSERT = [
    "empresa",
    "tipo_proveedor",
    "nombre_agente",
    "direccion",
    "num_exterior",
    "num_interior",
    "cp",
    "colonia",
    "municipio",
    "estado",
    "rfc",
    "telefono",
    "correo",
    "tipo"
]


class ProveedorRepository:
    """
    Acceso a datos para [dbo].[Proveedores] en SQL Server.
    """

    # =========================================
    # Lecturas
    # =========================================
    @staticmethod
    def listar_todos() -> List[Dict[str, Any]]:
        """Devuelve todos los proveedores ordenados por empresa."""
        sql = """
            SELECT id, empresa, tipo_proveedor, nombre_agente, direccion,
                   num_exterior, num_interior, cp, colonia, municipio, estado,
                   rfc, telefono, correo, tipo
            FROM dbo.Proveedores
            ORDER BY empresa ASC, id ASC;
        """
        rows = fetch_all(sql)
        return rows

    @staticmethod
    def buscar_por_empresa(prefix: str) -> List[Dict[str, Any]]:
        """Búsqueda incremental por EMPRESA (prefijo)."""
        prefix = (prefix or "").strip()
        sql = """
            SELECT id, empresa, tipo_proveedor, nombre_agente, direccion,
                   num_exterior, num_interior, cp, colonia, municipio, estado,
                   rfc, telefono, correo, tipo
            FROM dbo.Proveedores
            WHERE UPPER(empresa) LIKE UPPER(?)
            ORDER BY empresa DESC, id DESC;
        """
        rows = fetch_all(sql, [f"{prefix}%"])
        return rows

    @staticmethod
    def obtener_por_id(pid: int) -> Optional[Dict[str, Any]]:
        """Obtiene un proveedor por su ID."""
        sql = """
            SELECT id, empresa, tipo_proveedor, nombre_agente, direccion,
                   num_exterior, num_interior, cp, colonia, municipio, estado,
                   rfc, telefono, correo, tipo
            FROM dbo.Proveedores
            WHERE id = ?;
        """
        return fetch_one(sql, [pid])

    # =========================================
    # Insertar (VERSIÓN SIMPLIFICADA)
    # =========================================
    @staticmethod
    def insertar(proveedor: Any) -> bool:
        """
        Inserta un proveedor. Devuelve True si se insertó correctamente.
        Evita reintentar el INSERT cuando ya se ejecutó correctamente.
        """
        # Convertir a diccionario
        if hasattr(proveedor, "to_dict"):
            p = proveedor.to_dict()
        elif isinstance(proveedor, dict):
            p = dict(proveedor)
        else:
            p = {"empresa": str(proveedor)} if proveedor else {}

        # Construir SQL
        sql = f"""
            INSERT INTO dbo.Proveedores 
            ({", ".join(_COLS_INSERT)})
            VALUES ({", ".join(["?"] * len(_COLS_INSERT))});
        """

        params = [p.get(col) for col in _COLS_INSERT]
        LOGGER.info("Insertando proveedor: empresa=%s", p.get("empresa"))

        try:
            new_id = insert_and_get_id(sql, params)

            if new_id is not None:
                LOGGER.info("✅ Insertado proveedor id=%s", new_id)
                return True

            LOGGER.error("❌ Error al insertar proveedor: insert_and_get_id no devolvió ID")
            return False

        except Exception as e:
            LOGGER.error("❌ Excepción al insertar: %s", e)
            return False

    # =========================================
    # Actualizar
    # =========================================
    @staticmethod
    def actualizar(proveedor: Any) -> bool:
        """Actualiza un proveedor existente."""
        if hasattr(proveedor, "to_dict"):
            p = proveedor.to_dict()
        elif isinstance(proveedor, dict):
            p = dict(proveedor)
        else:
            return False

        pid = p.get("id")
        if not pid:
            LOGGER.error("Actualizar: ID no proporcionado")
            return False

        sql = """
            UPDATE dbo.Proveedores
            SET empresa = ?,
                tipo_proveedor = ?,
                nombre_agente = ?,
                direccion = ?,
                num_exterior = ?,
                num_interior = ?,
                cp = ?,
                colonia = ?,
                municipio = ?,
                estado = ?,
                rfc = ?,
                telefono = ?,
                correo = ?,
                tipo = ?
            WHERE id = ?;
        """

        params = [
            p.get("empresa"),
            p.get("tipo_proveedor"),
            p.get("nombre_agente"),
            p.get("direccion"),
            p.get("num_exterior"),
            p.get("num_interior"),
            p.get("cp"),
            p.get("colonia"),
            p.get("municipio"),
            p.get("estado"),
            p.get("rfc"),
            p.get("telefono"),
            p.get("correo"),
            p.get("tipo"),
            pid
        ]

        try:
            rc = execute(sql, params)
            success = rc == 1
            if success:
                LOGGER.info("✅ Actualizado proveedor id=%s", pid)
            else:
                LOGGER.warning("⚠️ No se actualizó proveedor id=%s (rc=%s)", pid, rc)
            return success
        except Exception as e:
            LOGGER.error("❌ Error al actualizar: %s", e)
            return False

    # =========================================
    # Eliminar
    # =========================================
    @staticmethod
    def eliminar(pid: int) -> bool:
        """Elimina un proveedor por su ID."""
        sql = "DELETE FROM dbo.Proveedores WHERE id = ?;"
        try:
            rc = execute(sql, [pid])
            success = rc == 1
            LOGGER.info("Eliminado proveedor id=%s -> %s", pid, success)
            return success
        except Exception as e:
            LOGGER.error("❌ Error al eliminar: %s", e)
            return False

    # =========================================
    # Unificación
    # =========================================
    @staticmethod
    def agrupar_coincidencias_por_id(ids: Sequence[int]) -> Optional[Dict[str, Any]]:
        """Une varios registros en uno solo."""
        if not ids or len(ids) < 2:
            return None

        placeholders = ", ".join(["?"] * len(ids))
        sql = f"""
            SELECT id, empresa, tipo_proveedor, nombre_agente, direccion,
                   num_exterior, num_interior, cp, colonia, municipio, estado,
                   rfc, telefono, correo, tipo
            FROM dbo.Proveedores
            WHERE id IN ({placeholders});
        """
        rows = fetch_all(sql, list(ids))

        if len(rows) < 2:
            return None

        def score(d: Dict[str, Any]) -> int:
            keys = ["empresa", "tipo_proveedor", "nombre_agente", "direccion",
                    "num_exterior", "num_interior", "cp", "colonia", "municipio",
                    "estado", "rfc", "telefono", "correo", "tipo"]
            return sum(1 for k in keys if (str(d.get(k) or "").strip() != ""))

        rows.sort(key=score, reverse=True)
        ganador = dict(rows[0])
        perdedores = rows[1:]

        for perdedor in perdedores:
            for k in ganador.keys():
                if k != "id":
                    if (ganador.get(k) is None) or (str(ganador.get(k)).strip() == ""):
                        if perdedor.get(k) not in (None, ""):
                            ganador[k] = perdedor[k]

        ProveedorRepository.actualizar(ganador)
        for perdedor in perdedores:
            ProveedorRepository.eliminar(perdedor["id"])

        LOGGER.info("Agrupados %s en id=%s", ids, ganador["id"])
        return ganador
