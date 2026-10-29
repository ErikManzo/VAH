# -*- coding: utf-8 -*-
"""
Repositorio de Paquetes

Responsabilidades:
- Obtener componentes de paquetes de aluminio
- Obtener componentes de paquetes de herrajes
- Obtener información de cabecera de paquetes

Tablas involucradas:
- aluminio.dbo.paquetes_aluminio
- aluminio.dbo.paquete_aluminio_items
- herrajes.dbo.paquetes_herrajes
- herrajes.dbo.paquete_herraje_items
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
import sys
import os


from common.logger_config import get_logger
logger = get_logger('concentrador.repositories.paquetes_repository')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.conn import DbConfig

class PaquetesRepository:
    """
    Repositorio para acceso a datos de paquetes.
    Solo lectura - No modifica la base de datos.
    """

    # Configuraciones por base de datos
    _config_aluminio = DbConfig(
        server="DESKTOP-AE60PIU\\SQLEXPRESS",
        database="aluminio",
        trusted=True,
        driver="ODBC Driver 18 for SQL Server",
        encrypt=False,
        trust_server_certificate=True
    )

    _config_herrajes = DbConfig(
        server="DESKTOP-AE60PIU\\SQLEXPRESS",
        database="herrajes",
        trusted=True,
        driver="ODBC Driver 18 for SQL Server",
        encrypt=False,
        trust_server_certificate=True
    )

    def __init__(self):
        """Inicializa el repositorio."""
        self._connection_aluminio = None
        self._connection_herrajes = None

    def _get_cursor_aluminio(self):
        """Obtiene un cursor para la base de datos aluminio."""
        try:
            if self._connection_aluminio is None:
                self._connection_aluminio = self._config_aluminio.connect()
            return self._connection_aluminio.cursor()
        except Exception as e:
            raise RuntimeError(f"No fue posible conectar a SQL Server (aluminio): {str(e)}")

    def _get_cursor_herrajes(self):
        """Obtiene un cursor para la base de datos herrajes."""
        try:
            if self._connection_herrajes is None:
                self._connection_herrajes = self._config_herrajes.connect()
            return self._connection_herrajes.cursor()
        except Exception as e:
            raise RuntimeError(f"No fue posible conectar a SQL Server (herrajes): {str(e)}")

    def _commit_close(self):
        """Cierra todas las conexiones."""
        if self._connection_aluminio:
            try:
                self._connection_aluminio.close()
            except Exception:
                pass
            finally:
                self._connection_aluminio = None
        if self._connection_herrajes:
            try:
                self._connection_herrajes.close()
            except Exception:
                pass
            finally:
                self._connection_herrajes = None

    # ================================================================
    # PAQUETES DE ALUMINIO
    # ================================================================

    def obtener_paquete_aluminio(self, clave_paquete: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la cabecera de un paquete de aluminio.
        """
        cursor = None
        try:
            cursor = self._get_cursor_aluminio()

            query = """
                SELECT 
                    clave,
                    ISNULL(descripcion, '') AS descripcion
                FROM paquetes_aluminio
                WHERE clave = ?
            """

            cursor.execute(query, (clave_paquete,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "clave": row[0],
                "descripcion": row[1]
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener paquete aluminio {clave_paquete}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def obtener_componentes_paquete_aluminio(self, clave_paquete: str) -> List[Dict[str, Any]]:
        """
        Obtiene los componentes de un paquete de aluminio.
        """
        cursor = None
        try:
            cursor = self._get_cursor_aluminio()

            query = """
                SELECT 
                    pai.clv_item,
                    ISNULL(ma.descripcion, '') AS descripcion,
                    pai.horizontal,
                    pai.vertical,
                    pai.cantidad,
                    ma.largo
                FROM paquete_aluminio_items pai
                INNER JOIN materiales_aluminio ma 
                    ON ma.clave = pai.clv_item
                WHERE pai.clave_paquete = ?
                ORDER BY pai.clv_item
            """

            cursor.execute(query, (clave_paquete,))
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                largo = row[5]
                if largo is not None and isinstance(largo, Decimal):
                    largo = float(largo)

                resultados.append({
                    "clave_item": row[0],
                    "descripcion": row[1],
                    "horizontal": row[2],
                    "vertical": row[3],
                    "cantidad": row[4],
                    "largo_tramo": largo
                })

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener componentes del paquete aluminio {clave_paquete}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def obtener_paquete_aluminio_completo(self, clave_paquete: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un paquete de aluminio completo (cabecera + componentes).
        """
        cabecera = self.obtener_paquete_aluminio(clave_paquete)
        if not cabecera:
            return None

        componentes = self.obtener_componentes_paquete_aluminio(clave_paquete)

        return {
            "clave": cabecera["clave"],
            "descripcion": cabecera["descripcion"],
            "componentes": componentes
        }

    # ================================================================
    # PAQUETES DE HERRAJES
    # ================================================================

    def obtener_paquete_herrajes(self, clave_paquete: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la cabecera de un paquete de herrajes.
        """
        cursor = None
        try:
            cursor = self._get_cursor_herrajes()

            query = """
                SELECT 
                    clave,
                    ISNULL(descripcion, '') AS descripcion
                FROM paquetes_herrajes
                WHERE clave = ?
            """

            cursor.execute(query, (clave_paquete,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "clave": row[0],
                "descripcion": row[1]
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener paquete herrajes {clave_paquete}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def obtener_componentes_paquete_herrajes(self, clave_paquete: str) -> List[Dict[str, Any]]:
        """
        Obtiene los componentes de un paquete de herrajes.
        """
        cursor = None
        try:
            cursor = self._get_cursor_herrajes()

            query = """
                SELECT 
                    phi.clv_herraje,
                    ISNULL(mh.Descripcion, '') AS descripcion,
                    phi.cantidad
                FROM paquete_herraje_items phi
                INNER JOIN materiales_herraje mh 
                    ON mh.Clave = phi.clv_herraje
                WHERE phi.clave_paquete = ?
                ORDER BY phi.clv_herraje
            """

            cursor.execute(query, (clave_paquete,))
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                resultados.append({
                    "clave_herraje": row[0],
                    "descripcion": row[1],
                    "cantidad": row[2]
                })

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener componentes del paquete herrajes {clave_paquete}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def obtener_paquete_herrajes_completo(self, clave_paquete: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un paquete de herrajes completo (cabecera + componentes).
        """
        cabecera = self.obtener_paquete_herrajes(clave_paquete)
        if not cabecera:
            return None

        componentes = self.obtener_componentes_paquete_herrajes(clave_paquete)

        return {
            "clave": cabecera["clave"],
            "descripcion": cabecera["descripcion"],
            "componentes": componentes
        }
