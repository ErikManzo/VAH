# -*- coding: utf-8 -*-
"""
Repositorio de Materiales por Almacén

Responsabilidades:
- Obtener información de materiales según su tipo/almacén
- Acceso a tablas: materiales_aluminio, materiales_herraje, etc.
- Obtener largo de tramo para perfiles de aluminio
- Obtener kg/m para perfiles de herrería

Tablas involucradas:
- aluminio.dbo.materiales_aluminio
- herrajes.dbo.materiales_herraje
- herreria.dbo.materiales_herreria
- vidrio.dbo.materiales_vidrio
- plasticos.dbo.materiales_plasticos
- otros.dbo.materiales_otros
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
import sys
import os


from common.logger_config import get_logger
logger = get_logger('concentrador.repositories.materiales_repository')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.conn import DbConfig

class MaterialesRepository:
    """
    Repositorio para acceso a catálogos de materiales.
    Solo lectura - No modifica la base de datos.
    """

    # Configuraciones por base de datos
    _configs = {
        "aluminio": DbConfig(
            server="DESKTOP-AE60PIU\\SQLEXPRESS",
            database="aluminio",
            trusted=True,
            driver="ODBC Driver 18 for SQL Server",
            encrypt=False,
            trust_server_certificate=True
        ),
        "herrajes": DbConfig(
            server="DESKTOP-AE60PIU\\SQLEXPRESS",
            database="herrajes",
            trusted=True,
            driver="ODBC Driver 18 for SQL Server",
            encrypt=False,
            trust_server_certificate=True
        ),
        "herreria": DbConfig(
            server="DESKTOP-AE60PIU\\SQLEXPRESS",
            database="herreria",
            trusted=True,
            driver="ODBC Driver 18 for SQL Server",
            encrypt=False,
            trust_server_certificate=True
        ),
        "vidrio": DbConfig(
            server="DESKTOP-AE60PIU\\SQLEXPRESS",
            database="vidrio",
            trusted=True,
            driver="ODBC Driver 18 for SQL Server",
            encrypt=False,
            trust_server_certificate=True
        ),
        "plasticos": DbConfig(
            server="DESKTOP-AE60PIU\\SQLEXPRESS",
            database="plasticos",
            trusted=True,
            driver="ODBC Driver 18 for SQL Server",
            encrypt=False,
            trust_server_certificate=True
        ),
        "otros": DbConfig(
            server="DESKTOP-AE60PIU\\SQLEXPRESS",
            database="otros",
            trusted=True,
            driver="ODBC Driver 18 for SQL Server",
            encrypt=False,
            trust_server_certificate=True
        ),
    }

    def __init__(self):
        """Inicializa el repositorio."""
        self._connections = {}

    def _get_cursor(self, db_name: str):
        """Obtiene un cursor para la base de datos especificada."""
        try:
            if db_name not in self._connections:
                self._connections[db_name] = self._configs[db_name].connect()
            return self._connections[db_name].cursor()
        except Exception as e:
            raise RuntimeError(f"No fue posible conectar a SQL Server ({db_name}): {str(e)}")

    def _commit_close_all(self):
        """Cierra todas las conexiones."""
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()

    # ================================================================
    # ALUMINIO
    # ================================================================

    def obtener_material_aluminio(self, clave: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un perfil de aluminio por su clave.
        """
        cursor = None
        try:
            cursor = self._get_cursor("aluminio")

            query = """
                SELECT 
                    clave,
                    ISNULL(descripcion, '') AS descripcion,
                    largo
                FROM materiales_aluminio
                WHERE clave = ?
            """

            cursor.execute(query, (clave,))
            row = cursor.fetchone()

            if not row:
                return None

            largo = row[2]
            if largo is not None and isinstance(largo, Decimal):
                largo = float(largo)

            return {
                "clave": row[0],
                "descripcion": row[1],
                "largo": largo
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener material aluminio {clave}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    def obtener_multiples_materiales_aluminio(self, claves: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene múltiples perfiles de aluminio de una sola consulta.
        """
        if not claves:
            return {}

        cursor = None
        try:
            cursor = self._get_cursor("aluminio")

            placeholders = ','.join(['?' for _ in claves])

            query = f"""
                SELECT 
                    clave,
                    ISNULL(descripcion, '') AS descripcion,
                    largo
                FROM materiales_aluminio
                WHERE clave IN ({placeholders})
            """

            cursor.execute(query, claves)
            rows = cursor.fetchall()

            resultados = {}
            for row in rows:
                largo = row[2]
                if largo is not None and isinstance(largo, Decimal):
                    largo = float(largo)

                resultados[row[0]] = {
                    "clave": row[0],
                    "descripcion": row[1],
                    "largo": largo
                }

            return resultados

        except Exception as e:
            raise RuntimeError(f"Error al obtener múltiples materiales aluminio: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    # ================================================================
    # HERRERÍA
    # ================================================================

    def obtener_material_herreria(self, clave: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un perfil de herrería por su clave.
        """
        cursor = None
        try:
            cursor = self._get_cursor("herreria")

            query = """
                SELECT 
                    Clave,
                    ISNULL(Descripcion, '') AS Descripcion,
                    ISNULL(kilogramos, 0.00) AS kilogramos_por_metro
                FROM materiales_herreria
                WHERE Clave = ?
            """

            cursor.execute(query, (clave,))
            row = cursor.fetchone()

            if not row:
                return None

            kg_m = row[2]
            if isinstance(kg_m, Decimal):
                kg_m = float(kg_m)

            return {
                "clave": row[0],
                "descripcion": row[1],
                "kilogramos_por_metro": kg_m
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener material herreria {clave}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    # ================================================================
    # HERRAJES
    # ================================================================

    def obtener_material_herraje(self, clave: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un herraje por su clave.
        """
        cursor = None
        try:
            cursor = self._get_cursor("herrajes")

            query = """
                SELECT 
                    Clave,
                    ISNULL(Descripcion, '') AS Descripcion
                FROM materiales_herraje
                WHERE Clave = ?
            """

            cursor.execute(query, (clave,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "clave": row[0],
                "descripcion": row[1]
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener material herraje {clave}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    # ================================================================
    # VIDRIO
    # ================================================================

    def obtener_material_vidrio(self, clave: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un vidrio por su clave.
        """
        cursor = None
        try:
            cursor = self._get_cursor("vidrio")

            query = """
                SELECT 
                    Clave,
                    ISNULL(Descripcion, '') AS Descripcion
                FROM materiales_vidrio
                WHERE Clave = ?
            """

            cursor.execute(query, (clave,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "clave": row[0],
                "descripcion": row[1]
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener material vidrio {clave}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    # ================================================================
    # PLÁSTICOS
    # ================================================================

    def obtener_material_plastico(self, clave: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un plástico por su clave.
        """
        cursor = None
        try:
            cursor = self._get_cursor("plasticos")

            query = """
                SELECT 
                    Clave,
                    ISNULL(Descripcion, '') AS Descripcion
                FROM materiales_plasticos
                WHERE Clave = ?
            """

            cursor.execute(query, (clave,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "clave": row[0],
                "descripcion": row[1]
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener material plástico {clave}: {str(e)}")
        finally:
            if cursor:
                cursor.close()

    # ================================================================
    # OTROS
    # ================================================================

    def obtener_material_otro(self, clave: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un material de otros por su clave.
        """
        cursor = None
        try:
            cursor = self._get_cursor("otros")

            query = """
                SELECT 
                    Clave,
                    ISNULL(Descripcion, '') AS Descripcion
                FROM materiales_otros
                WHERE Clave = ?
            """

            cursor.execute(query, (clave,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "clave": row[0],
                "descripcion": row[1]
            }

        except Exception as e:
            raise RuntimeError(f"Error al obtener material otros {clave}: {str(e)}")
        finally:
            if cursor:
                cursor.close()
