# -*- coding: utf-8 -*-
"""
Repositorio Integrador del Concentrador
Responsabilidades:
- Obtener datos completos de partidas (items + paquetes)
- Integrar información de múltiples tablas en una sola consulta
- Preparar datos para la explosión de materiales

Tablas involucradas:
- presupuestos.dbo.partidas
- presupuestos.dbo.items_partida
- presupuestos.dbo.partida_paquetes
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
import sys
import os


from common.logger_config import get_logger
logger = get_logger('concentrador.repositories.concentrador_repository')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.conn import DbConfig

class ConcentradorRepository:
    """
    Repositorio integrador para obtener datos completos de partidas.
    Solo lectura - No modifica la base de datos.
    """

    # Configuración de conexión a la base de datos presupuestos
    _db_config = DbConfig(
        server="DESKTOP-AE60PIU\\SQLEXPRESS",
        database="presupuestos",
        trusted=True,
        driver="ODBC Driver 18 for SQL Server",
        encrypt=False,
        trust_server_certificate=True
    )

    def __init__(self):
        """Inicializa el repositorio."""
        self._connection = None

    def _get_cursor(self):
        """Obtiene un cursor de la conexión existente."""
        try:
            if self._connection is None:
                self._connection = self._db_config.connect()
            return self._connection.cursor()
        except Exception as e:
            raise RuntimeError(f"No fue posible conectar a SQL Server (presupuestos): {str(e)}")

    def _commit_close(self):
        """Cierra la conexión."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            finally:
                self._connection = None

    def obtener_items_por_partida(self, partida_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los items de una partida específica.
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            query = """
                SELECT 
                    ISNULL(ip.tipo, '') AS tipo,
                    ISNULL(ip.clave, '') AS clave,
                    ISNULL(ip.descripcion, '') AS descripcion,
                    ISNULL(ip.ca, 1.00) AS ca,
                    ISNULL(ip.ancho, 0.00) AS ancho,
                    ISNULL(ip.ch, 1.00) AS ch,
                    ISNULL(ip.alto, 0.00) AS alto,
                    ISNULL(ip.piezas, 1) AS piezas,
                    ip.metros,
                    ip.kg_m,
                    ip.kgs
                FROM items_partida ip
                WHERE ip.partida_id = ?
                ORDER BY ip.id
            """

            cursor.execute(query, (partida_id,))
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                item = {
                    "tipo": row[0],
                    "clave": row[1],
                    "descripcion": row[2],
                    "ca": self._to_float(row[3]),
                    "ancho": self._to_float(row[4]),
                    "ch": self._to_float(row[5]),
                    "alto": self._to_float(row[6]),
                    "piezas": int(row[7]) if row[7] is not None else 1,
                    "metros": self._to_float_or_none(row[8]),
                    "kg_m": self._to_float_or_none(row[9]),
                    "kgs": self._to_float_or_none(row[10])
                }
                resultados.append(item)

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener items de partida {partida_id}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def obtener_paquetes_por_partida(self, partida_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los paquetes de una partida específica.
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            query = """
                SELECT 
                    ISNULL(pp.tipo_paquete, '') AS tipo_paquete,
                    ISNULL(pp.clave_paquete, '') AS clave_paquete,
                    ISNULL(pp.ancho, 0.00) AS ancho,
                    ISNULL(pp.alto, 0.00) AS alto,
                    ISNULL(pp.piezas, 1) AS cantidad_paquetes
                FROM partida_paquetes pp
                WHERE pp.partida_id = ?
                ORDER BY pp.id
            """

            cursor.execute(query, (partida_id,))
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                resultados.append({
                    "tipo_paquete": row[0],
                    "clave_paquete": row[1],
                    "ancho": self._to_float(row[2]),
                    "alto": self._to_float(row[3]),
                    "cantidad_paquetes": row[4]
                })

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener paquetes de partida {partida_id}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def obtener_partida_completa(self, partida_id: int) -> Dict[str, Any]:
        """
        Obtiene todos los datos de una partida (items + paquetes).
        """
        return {
            "partida_id": partida_id,
            "items": self.obtener_items_por_partida(partida_id),
            "paquetes": self.obtener_paquetes_por_partida(partida_id)
        }

    def obtener_todas_partidas_completas(self, partida_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Obtiene datos completos de múltiples partidas.
        """
        resultados = {}
        for partida_id in partida_ids:
            resultados[partida_id] = self.obtener_partida_completa(partida_id)
        return resultados

    def validar_existencia_partida(self, partida_id: int) -> bool:
        """
        Valida si una partida existe en la base de datos.
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            query = """
                SELECT COUNT(1)
                FROM partidas
                WHERE id = ?
            """

            cursor.execute(query, (partida_id,))
            count = cursor.fetchone()[0]

            return count > 0

        except Exception:
            return False
        finally:
            if cursor:
                cursor.close()

    def _to_float(self, value) -> float:
        """Convierte Decimal o str a float."""
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return float(value)

    def _to_float_or_none(self, value) -> Optional[float]:
        """Convierte a float o retorna None."""
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return float(value)
