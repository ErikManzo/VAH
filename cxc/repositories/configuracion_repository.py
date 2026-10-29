# -*- coding: utf-8 -*-
from typing import Optional
from decimal import Decimal
from ..data.db import get_connection
from ..models.configuracion_model import ConfiguracionCxcModel

class ConfiguracionRepository:
    @staticmethod
    def get_config() -> Optional[ConfiguracionCxcModel]:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, iva_default, descuento_default, prefijo_factura, siguiente_folio FROM configuracion_cxc")
            row = cursor.fetchone()
            if row:
                return ConfiguracionCxcModel(
                    id=row[0],
                    iva_default=Decimal(row[1]) if row[1] is not None else Decimal('16.00'),
                    descuento_default=Decimal(row[2]) if row[2] is not None else Decimal('0.00'),
                    prefijo_factura=row[3] if row[3] else "CXC",
                    siguiente_folio=int(row[4]) if row[4] is not None else 1
                )
            return None
        finally:
            conn.close()

    @staticmethod
    def update_siguiente_folio(nuevo_folio: int) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE configuracion_cxc SET siguiente_folio = ?", (nuevo_folio,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Error al actualizar folio: {e}")
        finally:
            conn.close()