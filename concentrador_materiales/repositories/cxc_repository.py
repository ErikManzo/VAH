# -*- coding: utf-8 -*-
"""
Repositorio CXC - Cuentas por Cobrar
Responsabilidades:
- Obtener presupuestos aceptados (presupuesto_aceptado = 1)
- Obtener cantidades por partida desde cxc_detalle
- Obtener instancias CXC por presupuesto (para selección en Concentrador)
- Validar consistencia de datos CXC
Tablas involucradas:
- cxc.dbo.cuentas_por_cobrar
- cxc.dbo.cxc_detalle
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
import sys
import os


from common.logger_config import get_logger
logger = get_logger('concentrador.repositories.cxc_repository')

# Agregar raíz del proyecto al path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.conn import DbConfig

class CXCRepository:
    """
    Repositorio para acceso a datos de CXC.
    Solo lectura - No modifica la base de datos.
    """

    # Configuración de conexión a la base de datos CXC
    _db_config = DbConfig(
        server="DESKTOP-AE60PIU\\SQLEXPRESS",
        database="cxc",
        trusted=True,
        driver="ODBC Driver 18 for SQL Server",
        encrypt=False,
        trust_server_certificate=True
    )

    def __init__(self):
        """Inicializa el repositorio con la conexión existente."""
        self._connection = None

    def _get_cursor(self):
        """
        Obtiene un cursor de la conexión a SQL Server.
        Reutiliza la conexión existente del ERP.
        """
        try:
            self._connection = self._db_config.connect()
            return self._connection.cursor()
        except Exception as e:
            raise RuntimeError(f"No fue posible conectar a SQL Server: {str(e)}")

    def _commit_close(self):
        """Cierra la conexión (no commit porque solo es lectura)."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            finally:
                self._connection = None

    # ========================================================================
    # MÉTODOS EXISTENTES (SIN MODIFICAR)
    # ========================================================================

    def obtener_presupuestos_aceptados(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los presupuestos aceptados en CXC.
        Condición: presupuesto_aceptado = 1 (True)
        Returns:
            List[Dict]: Lista de presupuestos con estructura:
                {
                    "cxc_id": int,
                    "presupuesto_id": int,
                    "folio": str,
                    "fecha_aceptacion": datetime
                }
        Raises:
            RuntimeError: Si hay error en la consulta SQL
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            query = """
                SELECT 
                    cxc.id AS cxc_id,
                    cxc.presupuesto_id,
                    ISNULL(cxc.folio, '') AS folio,
                    cxc.fecha_aceptacion
                FROM cuentas_por_cobrar cxc
                WHERE cxc.presupuesto_aceptado = 1
                ORDER BY cxc.fecha_aceptacion DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                resultados.append({
                    "cxc_id": row[0],
                    "presupuesto_id": row[1],
                    "folio": row[2],
                    "fecha_aceptacion": row[3]
                })

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener presupuestos aceptados: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            self._commit_close()

    def obtener_cantidades_por_cxc(self, cxc_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene las cantidades por partida para un CXC específico.
        Args:
            cxc_id: ID del registro en cuentas_por_cobrar
        Returns:
            List[Dict]: Lista de partidas con estructura:
                {
                    "partida_id": int,
                    "cantidad_cxc": float,
                    "presupuesto_id": int
                }
        Raises:
            RuntimeError: Si hay error en la consulta SQL
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            query = """
                SELECT 
                    det.partida_id,
                    COALESCE(
                        det.cantidad_facturada,
                        CAST(NULLIF(pa.piezas, 0) AS DECIMAL(18, 4)),
                        1
                    ) AS cantidad_cxc,
                    det.presupuesto_id
                FROM cxc_detalle det
                LEFT JOIN [presupuestos].[dbo].[partidas] pa
                    ON pa.id = det.partida_id
                WHERE det.cxc_id = ?
            """

            cursor.execute(query, (cxc_id,))
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                cantidad = row[1]
                if isinstance(cantidad, Decimal):
                    cantidad = float(cantidad)

                resultados.append({
                    "partida_id": row[0],
                    "cantidad_cxc": cantidad,
                    "presupuesto_id": row[2]
                })

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener cantidades para CXC {cxc_id}: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            self._commit_close()

    def obtener_todas_partidas_con_cantidad(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las partidas con su cantidad CXC,
        solo de presupuestos aceptados.
        Returns:
            List[Dict]: Lista de partidas con estructura:
                {
                    "partida_id": int,
                    "cantidad_cxc": float,
                    "cxc_id": int,
                    "presupuesto_id": int
                }
        Raises:
            RuntimeError: Si hay error en la consulta SQL
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            query = """
                SELECT 
                    det.partida_id,
                    COALESCE(
                        det.cantidad_facturada,
                        CAST(NULLIF(pa.piezas, 0) AS DECIMAL(18, 4)),
                        1
                    ) AS cantidad_cxc,
                    det.cxc_id,
                    det.presupuesto_id
                FROM cxc_detalle det
                INNER JOIN cuentas_por_cobrar cxc 
                    ON cxc.id = det.cxc_id
                LEFT JOIN [presupuestos].[dbo].[partidas] pa
                    ON pa.id = det.partida_id
                WHERE cxc.presupuesto_aceptado = 1
                ORDER BY det.cxc_id, det.partida_id
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                cantidad = row[1]
                if isinstance(cantidad, Decimal):
                    cantidad = float(cantidad)

                resultados.append({
                    "partida_id": row[0],
                    "cantidad_cxc": cantidad,
                    "cxc_id": row[2],
                    "presupuesto_id": row[3]
                })

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener todas las partidas con cantidad: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            self._commit_close()

    def validar_presupuesto_aceptado(self, presupuesto_id: int) -> bool:
        """
        Valida si un presupuesto está aceptado en CXC.
        Args:
            presupuesto_id: ID del presupuesto a validar
        Returns:
            bool: True si está aceptado, False en caso contrario
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            query = """
                SELECT COUNT(1)
                FROM cuentas_por_cobrar cxc
                WHERE cxc.presupuesto_id = ?
                AND cxc.presupuesto_aceptado = 1
            """

            cursor.execute(query, (presupuesto_id,))
            count = cursor.fetchone()[0]

            return count > 0

        except Exception:
            return False
        finally:
            if cursor:
                cursor.close()
            self._commit_close()

    # ========================================================================
    # NUEVO MÉTODO: OBTENER INSTANCIAS CXC POR PRESUPUESTO
    # ========================================================================

    def obtener_instancias_cxc_por_presupuesto(
            self, presupuesto_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las instancias CXC activas (presupuesto_aceptado = 1),
        opcionalmente filtradas por presupuesto_id.

        Este método es utilizado por el Concentrador de Materiales para permitir
        al usuario seleccionar qué instancia específica de CXC desea explotar,
        ya que un mismo presupuesto puede tener múltiples CXC activos.

        Args:
            presupuesto_id: ID del presupuesto para filtrar (opcional).
                           Si es None, retorna TODAS las instancias activas.

        Returns:
            List[Dict]: Lista de instancias con estructura:
                {
                    "cxc_id": int,
                    "folio": str,
                    "fecha_aceptacion": datetime,
                    "presupuesto_id": int,
                    "num_partidas": int,
                    "total_cxc": float
                }

        Raises:
            RuntimeError: Si hay error en la consulta SQL
        """
        cursor = None
        try:
            cursor = self._get_cursor()

            if presupuesto_id is not None:
                # Filtrar por presupuesto específico
                query = """
                    SELECT 
                        cxc.id AS cxc_id,
                        ISNULL(cxc.folio, '') AS folio,
                        cxc.fecha_aceptacion,
                        cxc.presupuesto_id,
                        COUNT(det.id) AS num_partidas,
                        ISNULL(cxc.total, 0) AS total_cxc
                    FROM cuentas_por_cobrar cxc
                    LEFT JOIN cxc_detalle det ON det.cxc_id = cxc.id
                    WHERE cxc.presupuesto_id = ?
                      AND cxc.presupuesto_aceptado = 1
                    GROUP BY cxc.id, cxc.folio, cxc.fecha_aceptacion, 
                             cxc.presupuesto_id, cxc.total
                    ORDER BY cxc.fecha_aceptacion DESC
                """
                cursor.execute(query, (presupuesto_id,))
            else:
                # Todas las instancias activas
                query = """
                    SELECT 
                        cxc.id AS cxc_id,
                        ISNULL(cxc.folio, '') AS folio,
                        cxc.fecha_aceptacion,
                        cxc.presupuesto_id,
                        COUNT(det.id) AS num_partidas,
                        ISNULL(cxc.total, 0) AS total_cxc
                    FROM cuentas_por_cobrar cxc
                    LEFT JOIN cxc_detalle det ON det.cxc_id = cxc.id
                    WHERE cxc.presupuesto_aceptado = 1
                    GROUP BY cxc.id, cxc.folio, cxc.fecha_aceptacion, 
                             cxc.presupuesto_id, cxc.total
                    ORDER BY cxc.fecha_aceptacion DESC
                """
                cursor.execute(query)

            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                fecha_aceptacion = row[2]
                total_cxc = row[5]

                if isinstance(total_cxc, Decimal):
                    total_cxc = float(total_cxc)

                resultados.append({
                    "cxc_id": row[0],
                    "folio": row[1],
                    "fecha_aceptacion": fecha_aceptacion,
                    "presupuesto_id": row[3],
                    "num_partidas": row[4],
                    "total_cxc": total_cxc if total_cxc is not None else 0.0
                })

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener instancias CXC: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            self._commit_close()
