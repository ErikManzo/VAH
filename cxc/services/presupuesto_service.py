# -*- coding: utf-8 -*-
from typing import List, Dict, Any
from decimal import Decimal
from ..data.db import get_connection

class PresupuestoService:
    @staticmethod
    def buscar_presupuestos(filtro: str) -> List[Dict[str, Any]]:
        if not filtro.strip(): return []
        conn = get_connection()
        cursor = conn.cursor()
        filtro_num = None
        try:
            filtro_num = int(filtro)
        except ValueError:
            pass
        query = """
        SELECT p.id, p.presupuesto AS numero, ISNULL(c.Nombre, 'SIN CLIENTE') AS cliente_nombre,
               ISNULL(p.obra, 'SIN OBRA') AS obra, p.fecha
        FROM [presupuestos].[dbo].[presupuestos] p
        LEFT JOIN [clientes].[dbo].[Clientes] c ON p.cliente_id = c.id
        WHERE (c.Nombre LIKE ?) OR (p.obra LIKE ?)
        """
        params = [f'%{filtro}%', f'%{filtro}%']
        if filtro_num is not None:
            query += " OR p.presupuesto = ?"
            params.append(filtro_num)
        query += " ORDER BY p.fecha DESC"
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [{'id': r[0], 'numero': r[1], 'cliente_nombre': r[2], 'obra': r[3], 'fecha': r[4]} for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_partidas_presupuesto(presupuesto_id: int) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, titulo, descripcion, piezas, precio_unitario, total_partida
                FROM [presupuestos].[dbo].[partidas] WHERE presupuesto_id = ? ORDER BY partida
            """, (presupuesto_id,))
            rows = cursor.fetchall()
            return [{
                'id': r[0], 'titulo': r[1], 'descripcion': r[2],
                'piezas_original': Decimal(r[3]) if r[3] is not None else Decimal('0.00'),
                'precio_unitario': Decimal(r[4]) if r[4] is not None else Decimal('0.00'),
                'total_partida': Decimal(r[5]) if r[5] is not None else Decimal('0.00')
            } for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_cliente_id_from_presupuesto(presupuesto_id: int) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT cliente_id FROM [presupuestos].[dbo].[presupuestos] WHERE id = ?", (presupuesto_id,))
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            conn.close()