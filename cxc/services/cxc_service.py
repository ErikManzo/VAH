# -*- coding: utf-8 -*-
from datetime import date, datetime
from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
from common.logger_config import get_logger
from ..data.db import get_connection
from ..repositories.cxc_repository import CxcRepository
from ..repositories.pago_repository import PagoRepository
from ..repositories.configuracion_repository import ConfiguracionRepository
from ..models.pago_model import PagoModel
from .presupuesto_service import PresupuestoService

logger = get_logger("cxc.services.cxc_service")


class CxcService:
    @staticmethod
    def _normalizar_partidas_seleccionadas(partidas_seleccionadas: List[Dict]) -> List[Dict]:
        normalizadas = []
        for partida in partidas_seleccionadas:
            cantidad = int(float(partida.get('cantidad_facturada') or 1))
            if cantidad < 1:
                cantidad = 1
            precio_unitario = float(partida.get('precio_unitario') or 0.0)
            normalizadas.append({
                'partida_id': int(partida['partida_id']),
                'cantidad_facturada': cantidad,
                'precio_unitario': precio_unitario,
                'importe': float(partida.get('importe') or (cantidad * precio_unitario)),
            })
        return normalizadas

    @staticmethod
    def generar_folio_unico() -> str:
        """Genera un folio único verificando que no exista en la BD."""
        config = ConfiguracionRepository.get_config()
        if not config or config.siguiente_folio is None:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM configuracion_cxc)
                INSERT INTO configuracion_cxc (iva_default, descuento_default, prefijo_factura, siguiente_folio)
                VALUES (16.0, 0.0, 'CXC', 1)
                ELSE 
                UPDATE configuracion_cxc SET siguiente_folio = ISNULL(siguiente_folio, 1),
                prefijo_factura = REPLACE(ISNULL(prefijo_factura, 'CXC'), '-', '')
            """)
            conn.commit()
            conn.close()
            prefijo = "CXC"
            num = 1
        else:
            prefijo = (config.prefijo_factura or "CXC").rstrip('-')
            num = config.siguiente_folio if config.siguiente_folio is not None else 1

        conn = get_connection()
        cursor = conn.cursor()
        while True:
            folio = f"{prefijo}-{num}"
            cursor.execute("SELECT COUNT(*) FROM cuentas_por_cobrar WHERE folio = ?", (folio,))
            existe = cursor.fetchone()[0]
            if existe == 0:
                ConfiguracionRepository.update_siguiente_folio(num + 1)
                conn.close()
                return folio
            num += 1

    @staticmethod
    def crear_cxc_desde_presupuesto(presupuesto_id: int, tipo_operacion: str,
                                    partidas_seleccionadas: List[Dict],
                                    descuento_porcentaje: Optional[float] = None,
                                    descuento_monto: Optional[float] = None,
                                    notas: str = " ", aceptar_presupuesto: bool = True) -> int:
        conn = None
        try:
            partidas_seleccionadas = CxcService._normalizar_partidas_seleccionadas(partidas_seleccionadas)
            cliente_id = PresupuestoService.get_cliente_id_from_presupuesto(presupuesto_id)
            if not cliente_id:
                raise ValueError("PRESUPUESTO SIN CLIENTE ASIGNADO")

            subtotal = sum(p['cantidad_facturada'] * p['precio_unitario'] for p in partidas_seleccionadas)
            if descuento_monto and descuento_monto > 0:
                monto_descuento = float(descuento_monto)
                descuento_porcentaje = None
            elif descuento_porcentaje and descuento_porcentaje > 0:
                monto_descuento = subtotal * (float(descuento_porcentaje) / 100.0)
            else:
                monto_descuento = 0.0
            subtotal_con_descuento = subtotal - monto_descuento

            if tipo_operacion == 'FACTURADO':
                config = ConfiguracionRepository.get_config()
                iva_porcentaje = config.iva_default if config and config.iva_default is not None else 16.0
                iva_porcentaje = float(iva_porcentaje)
                iva_monto = subtotal_con_descuento * (iva_porcentaje / 100.0)
                total = subtotal_con_descuento + iva_monto
            else:
                iva_porcentaje = 0.0
                iva_monto = 0.0
                total = subtotal_con_descuento

            folio = CxcService.generar_folio_unico()
            hoy = date.today()

            conn = get_connection()
            cursor = conn.cursor()

            # SOLUCIÓN: Usar OUTPUT INSERTED.id en lugar de SCOPE_IDENTITY()
            insert_sql = """
                INSERT INTO cuentas_por_cobrar (
                    presupuesto_id, cliente_id, folio, tipo_operacion, numero_factura,
                    fecha_emision, subtotal, descuento_porcentaje,
                    descuento_monto, iva_porcentaje, iva_monto, total, saldo_pendiente,
                    estado, notas, presupuesto_aceptado, fecha_aceptacion
                ) 
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                int(presupuesto_id), int(cliente_id), folio, tipo_operacion, " ",
                hoy, float(subtotal),
                float(descuento_porcentaje) if descuento_porcentaje is not None else None,
                float(monto_descuento) if monto_descuento > 0 else None,
                float(iva_porcentaje), float(iva_monto),
                float(total), float(total), "PENDIENTE",
                notas or " ", 1 if aceptar_presupuesto else 0,
                datetime.now() if aceptar_presupuesto else None
            )

            # Esta consulta retorna el ID directamente
            cursor.execute(insert_sql, params)
            row = cursor.fetchone()

            if row is None or row[0] is None:
                conn.rollback()
                raise RuntimeError("NO SE PUDO OBTENER EL ID DEL CXC INSERTADO")

            cxc_id = int(row[0])

            # Insertar detalles
            for p in partidas_seleccionadas:
                importe = float(p['cantidad_facturada']) * float(p['precio_unitario'])
                cursor.execute("""
                    INSERT INTO cxc_detalle (cxc_id, presupuesto_id, partida_id, cantidad_facturada, precio_unitario, importe)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (cxc_id, int(presupuesto_id), int(p['partida_id']),
                      float(p['cantidad_facturada']), float(p['precio_unitario']), importe))

            conn.commit()
            return cxc_id

        except Exception as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"ERROR AL CREAR CXC: {str(e)}")
        finally:
            if conn:
                conn.close()

    @staticmethod
    def registrar_pago(cxc_id: int, monto: Decimal, fecha_pago: date, metodo_pago: str,
                       concepto: str, cuenta_destino: str, referencia: str = " ", notas: str = " ") -> int:
        cxc = CxcRepository.get_by_id(cxc_id)
        if not cxc:
            raise ValueError("CXC NO ENCONTRADO")
        if monto <= 0:
            raise ValueError("MONTO DEBE SER MAYOR A CERO")
        if monto > cxc.saldo_pendiente:
            raise ValueError("EL MONTO SUPERA EL SALDO PENDIENTE")

        monto_decimal = Decimal(str(monto)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        pago = PagoModel(
            id=None, cxc_id=cxc_id, fecha_pago=fecha_pago, monto=float(monto_decimal),
            metodo_pago=metodo_pago, concepto=concepto, cuenta_destino=cuenta_destino,
            referencia=referencia, notas=notas, created_at=None
        )

        pago_id = PagoRepository.create(pago)
        nuevo_saldo = (cxc.saldo_pendiente - monto_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        CxcRepository.update_saldo(cxc_id, nuevo_saldo)

        return pago_id

    @staticmethod
    def obtener_resumen_general() -> Dict:
        """Resumen basado exclusivamente en ESTADOS (EN CURSO / LIQUIDADO)."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Saldo total pendiente (Solo lo que está EN CURSO)
            cursor.execute("""
                SELECT ISNULL(SUM(saldo_pendiente), 0) 
                FROM cuentas_por_cobrar 
                WHERE estado NOT IN ('LIQUIDADO', 'PAGADO')
            """)
            saldo_total = float(cursor.fetchone()[0])

            # 2. Cantidad EN CURSO
            cursor.execute("""
                SELECT COUNT(*) 
                FROM cuentas_por_cobrar 
                WHERE estado NOT IN ('LIQUIDADO', 'PAGADO')
            """)
            en_curso = cursor.fetchone()[0]

            # 3. Cantidad LIQUIDADOS
            cursor.execute("""
                SELECT COUNT(*) 
                FROM cuentas_por_cobrar 
                WHERE estado IN ('LIQUIDADO', 'PAGADO')
            """)
            liquidados = cursor.fetchone()[0]

            # 4. Clientes Activos
            cursor.execute("""
                SELECT COUNT(DISTINCT cliente_id) 
                FROM cuentas_por_cobrar 
                WHERE saldo_pendiente > 0
            """)
            clientes_activos = cursor.fetchone()[0]

            return {
                'saldo_total': saldo_total,
                'en_curso': en_curso,
                'liquidados': liquidados,
                'clientes_activos': clientes_activos
            }
        finally:
            conn.close()
