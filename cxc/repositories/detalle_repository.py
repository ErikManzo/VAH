# -*- coding: utf-8 -*-
from typing import List
from decimal import Decimal
from ..data.db import get_connection
from ..models.detalle_model import CxcDetalleModel

class DetalleRepository:
    @staticmethod
    def create(detalle: CxcDetalleModel) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO cxc_detalle (cxc_id, presupuesto_id, partida_id, cantidad_facturada, precio_unitario, importe)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (detalle.cxc_id, detalle.presupuesto_id, detalle.partida_id,
                  detalle.cantidad_facturada, detalle.precio_unitario, detalle.importe))
            cursor.execute("SELECT SCOPE_IDENTITY()")
            new_id = int(cursor.fetchone()[0])
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"ERROR AL INSERTAR DETALLE: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_by_cxc_id(cxc_id: int) -> List[CxcDetalleModel]:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM cxc_detalle WHERE cxc_id = ?", (cxc_id,))
            rows = cursor.fetchall()
            return [CxcDetalleModel(id=r[0], cxc_id=r[1], presupuesto_id=r[2], partida_id=r[3],
                                    cantidad_facturada=Decimal(r[4]), precio_unitario=Decimal(r[5]),
                                    importe=Decimal(r[6]), created_at=r[7]) for r in rows]
        finally:
            conn.close()