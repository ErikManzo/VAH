# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Tuple
from datetime import date
from decimal import Decimal
from common.logger_config import get_logger
from common.search_utils import format_key_description
from ..data.db import get_connection
from ..models.cxc_model import CxcModel

logger = get_logger("cxc.repositories.cxc_repository")


class CxcRepository:
    """Repositorio para operaciones CRUD de la tabla cuentas_por_cobrar"""

    @staticmethod
    def _row_to_model(row) -> CxcModel:
        """Convierte una fila de la base de datos en un objeto CxcModel"""
        estado_raw = row.estado or "EN CURSO"
        if estado_raw in ("PENDIENTE", "VENCIDO"):
            estado_raw = "EN CURSO"
        elif estado_raw == "PAGADO":
            estado_raw = "LIQUIDADO"

        return CxcModel(
            id=row.id, presupuesto_id=row.presupuesto_id, cliente_id=row.cliente_id,
            folio=row.folio, tipo_operacion=row.tipo_operacion, numero_factura=row.numero_factura,
            fecha_emision=row.fecha_emision,
            subtotal=Decimal(row.subtotal) if row.subtotal is not None else Decimal('0.00'),
            descuento_porcentaje=Decimal(row.descuento_porcentaje) if row.descuento_porcentaje is not None else None,
            descuento_monto=Decimal(row.descuento_monto) if row.descuento_monto is not None else None,
            iva_porcentaje=Decimal(row.iva_porcentaje) if row.iva_porcentaje is not None else None,
            iva_monto=Decimal(row.iva_monto) if row.iva_monto is not None else None,
            total=Decimal(row.total) if row.total is not None else Decimal('0.00'),
            saldo_pendiente=Decimal(row.saldo_pendiente) if row.saldo_pendiente is not None else Decimal('0.00'),
            estado=estado_raw, notas=row.notas, presupuesto_aceptado=row.presupuesto_aceptado,
            fecha_aceptacion=row.fecha_aceptacion, created_at=row.created_at, updated_at=row.updated_at
        )

    @staticmethod
    def create(cxc: CxcModel) -> int:
        """Inserta un nuevo registro en cuentas_por_cobrar"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO cuentas_por_cobrar (presupuesto_id, cliente_id, folio, tipo_operacion, numero_factura,
                    fecha_emision, subtotal, descuento_porcentaje, descuento_monto,
                    iva_porcentaje, iva_monto, total, saldo_pendiente, estado, notas, presupuesto_aceptado, fecha_aceptacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cxc.presupuesto_id, cxc.cliente_id, cxc.folio, cxc.tipo_operacion, cxc.numero_factura,
                  cxc.fecha_emision, cxc.subtotal, cxc.descuento_porcentaje,
                  cxc.descuento_monto, cxc.iva_porcentaje, cxc.iva_monto, cxc.total, cxc.saldo_pendiente,
                  cxc.estado, cxc.notas, cxc.presupuesto_aceptado, cxc.fecha_aceptacion))
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Error al insertar CXC: {e}")
        finally:
            conn.close()

    @staticmethod
    def update_saldo(cxc_id: int, nuevo_saldo: Decimal) -> None:
        """Actualiza el saldo pendiente y cambia estado"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE cuentas_por_cobrar SET saldo_pendiente = ?,
                estado = CASE WHEN ? <= 0 THEN 'LIQUIDADO' ELSE 'EN CURSO' END WHERE id = ?
            """, (nuevo_saldo, nuevo_saldo, cxc_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Error al actualizar saldo: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_by_id(cxc_id: int) -> Optional[CxcModel]:
        """Obtiene un CXC por su ID"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM cuentas_por_cobrar WHERE id = ?", (cxc_id,))
            row = cursor.fetchone()
            return CxcRepository._row_to_model(row) if row else None
        finally:
            conn.close()

    # ========================================================================
    # NUEVOS MÉTODOS: BÚSQUEDA INTELIGENTE (SMART SEARCH)
    # ========================================================================

    @staticmethod
    def buscar_clientes(texto: str) -> List[Dict]:
        if not texto or len(texto) < 1:
            return []
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT TOP 20 id, Nombre 
                FROM [clientes].[dbo].[Clientes] 
                WHERE Nombre COLLATE Latin1_General_CI_AI LIKE ?
                ORDER BY Nombre
            """, (f"%{texto}%",))
            return [
                {
                    'id': r[0],
                    'nombre': r[1],
                    'display': format_key_description(r[0], r[1]),
                }
                for r in cursor.fetchall()
            ]
        finally:
            conn.close()

    @staticmethod
    def buscar_obras(texto: str, cliente_id: Optional[int] = None) -> List[Dict]:
        if not texto or len(texto) < 1:
            return []
        conn = get_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT DISTINCT TOP 20 p.obra, p.cliente_id, c.Nombre as cliente_nombre
                FROM [presupuestos].[dbo].[presupuestos] p
                LEFT JOIN [clientes].[dbo].[Clientes] c ON p.cliente_id = c.id
                WHERE (
                    p.obra COLLATE Latin1_General_CI_AI LIKE ?
                    OR c.Nombre COLLATE Latin1_General_CI_AI LIKE ?
                )
            """
            like = f"%{texto}%"
            params = [like, like]
            if cliente_id:
                query += " AND p.cliente_id = ?"
                params.append(cliente_id)
            query += " ORDER BY p.obra"

            cursor.execute(query, params)
            return [
                {
                    'obra': r[0],
                    'cliente_id': r[1],
                    'cliente_nombre': r[2] or '',
                    'display': format_key_description(r[0] or 'SIN OBRA', r[2] or 'SIN CLIENTE'),
                }
                for r in cursor.fetchall()
            ]
        finally:
            conn.close()

    @staticmethod
    def buscar_presupuestos(texto: str, cliente_id: Optional[int] = None, obra: Optional[str] = None) -> List[Dict]:
        if not texto or len(texto) < 1:
            return []
        conn = get_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT TOP 20 p.id, p.presupuesto, p.obra, p.cliente_id, c.Nombre as cliente_nombre
                FROM [presupuestos].[dbo].[presupuestos] p
                LEFT JOIN [clientes].[dbo].[Clientes] c ON p.cliente_id = c.id
                WHERE (
                    CAST(p.presupuesto AS VARCHAR) COLLATE Latin1_General_CI_AI LIKE ?
                    OR c.Nombre COLLATE Latin1_General_CI_AI LIKE ?
                    OR p.obra COLLATE Latin1_General_CI_AI LIKE ?
                )
            """
            like = f"%{texto}%"
            params = [like, like, like]

            if cliente_id:
                query += " AND p.cliente_id = ?"
                params.append(cliente_id)
            if obra:
                query += " AND p.obra = ?"
                params.append(obra)

            query += " ORDER BY p.presupuesto DESC"

            cursor.execute(query, params)
            return [
                {
                    'id': r[0],
                    'presupuesto': str(r[1]),
                    'obra': r[2] or '',
                    'cliente_id': r[3],
                    'cliente_nombre': r[4] or '',
                    'display': format_key_description(
                        r[1],
                        f"{r[4] or 'SIN CLIENTE'} | {r[2] or 'SIN OBRA'}",
                    ),
                }
                for r in cursor.fetchall()
            ]
        finally:
            conn.close()

    # ========================================================================
    # MÉTODOS EXISTENTES (MANTENIDOS)
    # ========================================================================

    @staticmethod
    def _build_where_clause(filtros: Dict) -> Tuple[str, list]:
        """Construye cláusula WHERE dinámica y parámetros"""
        query = """
            FROM cuentas_por_cobrar cxc
            LEFT JOIN [clientes].[dbo].[Clientes] cli ON cxc.cliente_id = cli.id
            LEFT JOIN [presupuestos].[dbo].[presupuestos] pre ON cxc.presupuesto_id = pre.id
            WHERE 1=1
        """
        params = []
        if filtros.get('cliente_nombre'):
            query += " AND cli.Nombre LIKE ? "
            params.append(f'%{filtros["cliente_nombre"]}%')
        if filtros.get('obra'):
            query += " AND pre.obra LIKE ? "
            params.append(f'%{filtros["obra"]}%')
        if filtros.get('presupuesto_id'):
            query += " AND cxc.presupuesto_id = ? "
            params.append(filtros['presupuesto_id'])
        if filtros.get('presupuesto_numero'):
            query += " AND pre.presupuesto = ? "
            params.append(filtros['presupuesto_numero'])
        if filtros.get('fecha_desde'):
            query += " AND cxc.fecha_emision >= ? "
            params.append(filtros['fecha_desde'])
        if filtros.get('fecha_hasta'):
            query += " AND cxc.fecha_emision <= ? "
            params.append(filtros['fecha_hasta'])
        if filtros.get('estado') and filtros['estado'] != 'TODOS':
            estado_busqueda = 'PAGADO' if filtros['estado'] == 'LIQUIDADO' else filtros['estado']
            if estado_busqueda in ('EN CURSO',):
                query += " AND cxc.estado NOT IN ('LIQUIDADO', 'PAGADO') "
            else:
                query += " AND cxc.estado = ? "
                params.append(estado_busqueda)
        if filtros.get('tipo_operacion') and filtros['tipo_operacion'] != 'AMBOS':
            query += " AND cxc.tipo_operacion = ? "
            params.append(filtros['tipo_operacion'])
        return query, params

    @staticmethod
    def get_total_registros(filtros: Dict) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        where_sql, params = CxcRepository._build_where_clause(filtros)
        try:
            cursor.execute(f"SELECT COUNT(cxc.id) {where_sql}", params)
            return int(cursor.fetchone()[0] or 0)
        finally:
            conn.close()

    @staticmethod
    def get_all_with_client_and_presupuesto(filtros: Dict, page: int = 1, page_size: int = 50) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        where_sql, params = CxcRepository._build_where_clause(filtros)
        offset_val = (page - 1) * page_size

        query = f"""
            SELECT cxc.id, cxc.folio, cxc.fecha_emision,
                cxc.total, cxc.saldo_pendiente, cxc.estado, cxc.tipo_operacion,
                cxc.presupuesto_id, ISNULL(cli.Nombre, 'SIN CLIENTE') AS cliente_nombre,
                cli.id AS cliente_id, ISNULL(pre.obra, '') AS obra, pre.presupuesto AS presupuesto_numero
            {where_sql} 
            ORDER BY cxc.fecha_emision DESC, cxc.id DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        try:
            cursor.execute(query, params + [offset_val, page_size])
            rows = cursor.fetchall()
            result = []
            for r in rows:
                estado = r[5] or 'EN CURSO'
                if estado in ('PENDIENTE', 'VENCIDO'):
                    estado = 'EN CURSO'
                elif estado == 'PAGADO':
                    estado = 'LIQUIDADO'
                result.append({
                    'id': r[0], 'folio': r[1] or '', 'fecha_emision': r[2],
                    'total': Decimal(r[3]) if r[3] is not None else Decimal('0.00'),
                    'saldo_pendiente': Decimal(r[4]) if r[4] is not None else Decimal('0.00'),
                    'estado': estado, 'tipo_operacion': r[6] or 'FACTURADO',
                    'presupuesto_id': r[7], 'cliente_nombre': r[8], 'cliente_id': r[9],
                    'obra': r[10] or '', 'presupuesto_numero': r[11]
                })
            return result
        finally:
            conn.close()

    @staticmethod
    def get_all_for_export(filtros: Dict) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        where_sql, params = CxcRepository._build_where_clause(filtros)

        query = f"""
            SELECT cxc.id, cxc.folio, cxc.fecha_emision,
                cxc.total, cxc.saldo_pendiente, cxc.estado, cxc.tipo_operacion,
                cxc.presupuesto_id, ISNULL(cli.Nombre, 'SIN CLIENTE') AS cliente_nombre,
                cli.id AS cliente_id, ISNULL(pre.obra, '') AS obra, pre.presupuesto AS presupuesto_numero
            {where_sql} 
            ORDER BY cxc.fecha_emision DESC, cxc.id DESC
        """
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            result = []
            for r in rows:
                estado = r[5] or 'EN CURSO'
                if estado in ('PENDIENTE', 'VENCIDO'):
                    estado = 'EN CURSO'
                elif estado == 'PAGADO':
                    estado = 'LIQUIDADO'
                result.append({
                    'id': r[0], 'folio': r[1] or '', 'fecha_emision': r[2],
                    'total': Decimal(r[3]) if r[3] is not None else Decimal('0.00'),
                    'saldo_pendiente': Decimal(r[4]) if r[4] is not None else Decimal('0.00'),
                    'estado': estado, 'tipo_operacion': r[6] or 'FACTURADO',
                    'presupuesto_id': r[7], 'cliente_nombre': r[8], 'cliente_id': r[9],
                    'obra': r[10] or '', 'presupuesto_numero': r[11]
                })
            return result
        finally:
            conn.close()

    @staticmethod
    def get_saldos_por_cliente() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT cli.id AS cliente_id, cli.Nombre AS cliente_nombre,
                    ISNULL(SUM(cxc.total), 0) AS total_facturado,
                    ISNULL(SUM(cxc.total - cxc.saldo_pendiente), 0) AS total_abonado,
                    ISNULL(SUM(cxc.saldo_pendiente), 0) AS saldo
                FROM cuentas_por_cobrar cxc
                INNER JOIN [clientes].[dbo].[Clientes] cli ON cxc.cliente_id = cli.id
                WHERE cxc.estado NOT IN ('LIQUIDADO', 'PAGADO')
                GROUP BY cli.id, cli.Nombre
                HAVING ISNULL(SUM(cxc.saldo_pendiente), 0) > 0
                ORDER BY cli.Nombre
            """)
            rows = cursor.fetchall()
            return [{
                'cliente_id': r[0], 'cliente_nombre': r[1],
                'total_facturado': Decimal(r[2]), 'total_abonado': Decimal(r[3]),
                'saldo': Decimal(r[4])
            } for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_detalle_por_cliente(cliente_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT cxc.id, cxc.folio, pre.presupuesto AS presupuesto_numero,
                    ISNULL(pre.obra, '') AS obra, cxc.fecha_emision, cxc.total,
                    (cxc.total - cxc.saldo_pendiente) AS abonado, cxc.saldo_pendiente, cxc.estado
                FROM cuentas_por_cobrar cxc
                LEFT JOIN [presupuestos].[dbo].[presupuestos] pre ON cxc.presupuesto_id = pre.id
                WHERE cxc.cliente_id = ? AND cxc.saldo_pendiente > 0
                ORDER BY cxc.fecha_emision DESC, cxc.id DESC
            """, (cliente_id,))
            rows = cursor.fetchall()
            return [{
                'id': r[0], 'folio': r[1] or '', 'presupuesto_numero': r[2], 'obra': r[3],
                'fecha_emision': r[4], 'total': Decimal(r[5]), 'abonado': Decimal(r[6]),
                'saldo': Decimal(r[7]), 'estado': r[8]
            } for r in rows]
        finally:
            conn.close()

    @staticmethod
    def delete(cxc_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM cuentas_por_cobrar WHERE id = ?", (cxc_id,))
            if cursor.rowcount == 0:
                raise ValueError("NO SE ENCONTRÓ EL REGISTRO PARA ELIMINAR")
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Error al eliminar CXC {cxc_id}: {e}")
        finally:
            conn.close()
