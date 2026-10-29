# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/presupuesto_pdf_service.py
SERVICIO DE IMPRESIÓN DE PRESUPUESTOS - VERSIÓN DEFINITIVA
Esta versión utiliza los métodos EXISTENTES del Service.py para:
Obtener datos del presupuesto (obtener_presupuesto)
Obtener partidas (obtener_partidas)
Obtener nombre del cliente (ya viene incluido en obtener_presupuesto)
Obtener notas, forma de pago, descuento y plazo de entrega
NUEVO: soporte para modo_vista_previa (no dispara diálogo de notas)
REGLA CRÍTICA: El PDF SIEMPRE se guarda en disco, independientemente del modo.
"""
import os
import sys
import math
from datetime import datetime
from typing import Optional, List, Dict, Any
from presupuestos.reports.pdf_models import DatosPresupuesto, PartidaPresupuesto, TotalesPresupuesto
from presupuestos.reports.pdf_generator import generar_presupuesto_pdf
from presupuestos.core.constants import PRESUPUESTOS_PDF_DIR
from common.pdf_utils import get_pdf_path


def _redondear_peso_arriba(valor: float) -> float:
    """
    REGLA DE IMPRESIÓN: redondea al siguiente peso entero si el valor tiene
    centavos >= .01. Ejemplos: 2569.01 -> 2570.00; 2569.00 -> 2569.00.
    """
    v = round(float(valor or 0.0), 2)
    entero = math.floor(v)
    if v - entero >= 0.01:
        return float(entero + 1)
    return float(entero)


class PresupuestoPDFService:
    """
    Servicio para generar PDF de presupuestos desde la base de datos.
    Utiliza los métodos existentes de Service.py
    """

    def __init__(self, service):
        """
        Inicializa el servicio.
        Args:
            service: Instancia del Service de base de datos (desde service.py)
        """
        self.svc = service
        self.ruta_base_pdfs = PRESUPUESTOS_PDF_DIR
        # Crear directorio si no existe
        os.makedirs(self.ruta_base_pdfs, exist_ok=True)

    def generar_pdf_desde_id(self, presupuesto_id: int, parent=None,
                             modo_vista_previa: bool = False) -> Optional[str]:
        """
        Genera un PDF para el presupuesto con el ID especificado.

        Args:
            presupuesto_id: ID del presupuesto en la base de datos
            parent: Widget padre para diálogos (None en modo vista previa)
            modo_vista_previa: Si True, NO dispara el diálogo de notas/forma_pago/plazo
                              pero SÍ guarda el PDF en disco

        Returns:
            str: Ruta del PDF generado, o None si hay error

        REGLA CRÍTICA: El PDF SIEMPRE se guarda en disco, independientemente
        de si es modo vista previa o modo impresión normal.
        """
        print("=" * 60)
        print(f"[PDF Service] Generando PDF para presupuesto ID: {presupuesto_id}")
        print(f"[PDF Service] Modo vista previa: {modo_vista_previa}")
        print("=" * 60)

        try:
            # ====================================================================
            # 1. OBTENER DATOS DEL PRESUPUESTO
            # ====================================================================
            datos_presupuesto = self.svc.obtener_presupuesto(presupuesto_id)
            if not datos_presupuesto:
                print(f"[PDF Service] ERROR: No se encontró el presupuesto ID: {presupuesto_id}")
                return None
            print(f"[PDF Service] Presupuesto encontrado: Número {datos_presupuesto.get('presupuesto')}")
            print(f"[PDF Service] Cliente: {datos_presupuesto.get('cliente_nombre')}")

            # ====================================================================
            # 2. OBTENER TODAS LAS PARTIDAS
            # ====================================================================
            partidas_data = self.svc.obtener_partidas(presupuesto_id)
            if not partidas_data:
                print(f"[PDF Service] ADVERTENCIA: El presupuesto {presupuesto_id} no tiene partidas")
                return None
            print(f"[PDF Service] Partidas encontradas: {len(partidas_data)}")

            # ====================================================================
            # 3. OBTENER NOTAS, FORMA DE PAGO, DESCUENTO Y PLAZO DE ENTREGA
            # ====================================================================
            config = self.svc.obtener_configuracion_presupuesto(presupuesto_id)
            notas = config.get('notas', '')
            forma_pago = config.get('forma_pago', '60% AL ACEPTAR EL PRESUPUESTO / 40% AL TERMINAR')
            plazo_entrega = config.get('plazo_entrega', 'SERÁ DE COMÚN ACUERDO')
            try:
                descuento = float(config.get('descuento_porcentaje', 0.0) or 0.0)
            except (TypeError, ValueError):
                descuento = 0.0

            # CORREGIDO: Solo disparar diálogo de notas si hay parent Y NO es modo vista previa
            # En modo vista previa, usar la configuración guardada en BD
            if parent and not modo_vista_previa:
                from presupuestos.reports.pdf_notas_manager import NotasManager
                notas_manager = NotasManager(parent, self.svc)
                notas, forma_pago, plazo_entrega, descuento = notas_manager.preguntar_notas(presupuesto_id)

            # ====================================================================
            # 4. CONVERTIR LAS PARTIDAS AL FORMATO DEL GENERADOR
            #    REGLA DE IMPRESIÓN: P.U. redondeado al siguiente peso si tiene
            #    centavos >= .01; importe = P.U. redondeado × piezas.
            # ====================================================================
            partidas = []
            for p in partidas_data:
                piezas = int(p.get('piezas', 1))
                pu_redondeado = _redondear_peso_arriba(float(p.get('precio_unitario', 0)))
                importe_redondeado = round(pu_redondeado * piezas, 2)
                partida = PartidaPresupuesto(
                    numero=p.get('partida', 0),
                    titulo=p.get('titulo', ''),
                    descripcion=p.get('descripcion', ''),
                    precio_unitario=pu_redondeado,
                    piezas=piezas,
                    importe=importe_redondeado
                )
                partidas.append(partida)

            # ====================================================================
            # 5. CALCULAR TOTALES (con descuento)
            # ====================================================================
            totales = self._calcular_totales(partidas, descuento)

            # ====================================================================
            # 6. CONSTRUIR MODELO DE DATOS
            # ====================================================================
            fecha_raw = datos_presupuesto.get('fecha')
            if fecha_raw:
                if hasattr(fecha_raw, 'strftime'):
                    fecha_str = fecha_raw.strftime("%d/%m/%Y")
                else:
                    fecha_str = str(fecha_raw)
            else:
                fecha_str = datetime.now().strftime("%d/%m/%Y")

            modelo = DatosPresupuesto(
                cliente=datos_presupuesto.get('cliente_nombre', 'SIN CLIENTE'),
                num_presupuesto=datos_presupuesto.get('presupuesto', 0),
                obra=datos_presupuesto.get('obra', 'SIN OBRA'),
                fecha=fecha_str,
                anodizado=datos_presupuesto.get('color_global', 'VARIOS'),
                partidas=partidas,
                totales=totales,
                forma_pago=forma_pago,
                plazo_entrega=plazo_entrega,
                notas=notas,
                descuento_porcentaje=descuento
            )

            # ====================================================================
            # 7. GENERAR Y GUARDAR PDF (SIEMPRE, independientemente del modo)
            # ====================================================================
            nombre_archivo = f"{modelo.num_presupuesto}.pdf"
            ruta_pdf = get_pdf_path("Presupuestos", nombre_archivo)

            print(f"[PDF Service] Generando PDF en: {ruta_pdf}")
            print(f"[PDF Service] Cliente: {modelo.cliente}")
            print(f"[PDF Service] Presupuesto: {modelo.num_presupuesto}")
            print(f"[PDF Service] Descuento aplicado: {descuento:.2f}%")
            print(f"[PDF Service] Total de partidas a imprimir: {len(modelo.partidas)}")

            if generar_presupuesto_pdf(modelo, ruta_pdf, parent=parent):
                print(f"[PDF Service] PDF generado exitosamente")
                print(f"[PDF Service] Archivo guardado en: {ruta_pdf}")
                return ruta_pdf
            else:
                print(f"[PDF Service] ERROR: Falló la generación del PDF")
                return None

        except Exception as e:
            print(f"[PDF Service] Error inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _calcular_totales(self, partidas: List[PartidaPresupuesto],
                          descuento_porcentaje: float = 0.0) -> TotalesPresupuesto:
        """Calcula los totales a partir de las partidas, aplicando el descuento."""
        subtotal = sum(p.importe for p in partidas)
        return TotalesPresupuesto(
            subtotal=subtotal,
            iva_porcentaje=16.0,
            descuento_porcentaje=float(descuento_porcentaje or 0.0)
        )

    def imprimir_pdf(self, ruta_pdf: str) -> bool:
        """Envía el PDF a la impresora predeterminada."""
        try:
            import subprocess
            import sys
            if sys.platform == 'win32':
                os.startfile(ruta_pdf, "print")
            else:
                subprocess.run(['lp', ruta_pdf], check=True)
            print(f"[PDF Service] PDF enviado a impresión: {ruta_pdf}")
            return True
        except Exception as e:
            print(f"[PDF Service] Error imprimiendo: {e}")
            return False


def generar_pdf_presupuesto(service, presupuesto_id: int) -> Optional[str]:
    """Función de conveniencia para generar PDF de un presupuesto."""
    pdf_service = PresupuestoPDFService(service)
    return pdf_service.generar_pdf_desde_id(presupuesto_id)