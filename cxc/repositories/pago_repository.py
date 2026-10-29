# -*- coding: utf-8 -*-
from typing import List
from decimal import Decimal
from ..data.db import get_connection
from ..models.pago_model import PagoModel


class PagoRepository:
    @staticmethod
    def create(pago: PagoModel) -> int:
        """
        Inserta un nuevo pago y retorna su ID generado.
        CORRECCIÓN: Usa OUTPUT INSERTED.id para evitar error pyodbc
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # CORRECCIÓN: OUTPUT INSERTED.id en el mismo INSERT
            cursor.execute("""
                INSERT INTO pagos_recibidos (cxc_id, fecha_pago, monto, metodo_pago, concepto, cuenta_destino, referencia, notas)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pago.cxc_id,
                pago.fecha_pago,
                float(pago.monto) if isinstance(pago.monto, Decimal) else pago.monto,
                pago.metodo_pago,
                pago.concepto,
                pago.cuenta_destino,
                pago.referencia,
                pago.notas
            ))

            # Recuperar ID inmediatamente
            row = cursor.fetchone()
            if row is None or row[0] is None:
                raise RuntimeError("NO SE PUDO OBTENER EL ID DEL PAGO INSERTADO")

            new_id = int(row[0])
            conn.commit()
            return new_id

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"ERROR AL CREAR PAGO: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_by_cxc_id(cxc_id: int) -> List[PagoModel]:
        """Obtiene todos los pagos de un CXC ordenados por fecha descendente"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, cxc_id, fecha_pago, monto, metodo_pago, concepto, cuenta_destino, referencia, notas, created_at 
                FROM pagos_recibidos 
                WHERE cxc_id = ? 
                ORDER BY fecha_pago DESC
            """, (cxc_id,))
            rows = cursor.fetchall()

            return [
                PagoModel(
                    id=r[0],
                    cxc_id=r[1],
                    fecha_pago=r[2],
                    monto=Decimal(str(r[3])) if r[3] is not None else Decimal('0.00'),
                    metodo_pago=r[4],
                    concepto=r[5],
                    cuenta_destino=r[6],
                    referencia=r[7],
                    notas=r[8],
                    created_at=r[9]
                ) for r in rows
            ]
        finally:
            conn.close()