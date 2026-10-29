# -*- coding: utf-8 -*-
"""
Módulo de Reportes CXC - Generación de PDF y Excel
Encapsula toda la lógica de generación de archivos
Sin dependencias de UI
MODO: ARCHIVO VIGENTE (Sobrescritura sin timestamp)
"""
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from common.pdf_utils import get_pdf_dir, get_pdf_path
from ...repositories.cxc_repository import CxcRepository
from ...repositories.pago_repository import PagoRepository
from ...data.db import get_connection


class CxcReportes:
    """Generador de reportes CXC - PDF y Excel"""

    # Corregido: eliminados espacios en blanco que causaban rutas inválidas
    RUTA_BASE = get_pdf_dir("CXC")

    @staticmethod
    def _crear_carpetas():
        """Crea automáticamente las carpetas necesarias"""
        carpetas = [
            os.path.join(CxcReportes.RUTA_BASE, "Excel", "ListadoGeneral"),
            os.path.join(CxcReportes.RUTA_BASE, "Excel", "EstadoCliente"),
            os.path.join(CxcReportes.RUTA_BASE, "Excel", "Movimientos"),
        ]
        for carpeta in carpetas:
            os.makedirs(carpeta, exist_ok=True)

    @staticmethod
    def _sanitizar_nombre_archivo(nombre: str) -> str:
        """
        Limpia el nombre del cliente para que sea válido como nombre de archivo en Windows.
        Elimina caracteres prohibidos y normaliza a mayúsculas con guiones bajos.
        """
        if not nombre:
            return "CLIENTE_DESCONOCIDO"

        nombre_limpio = re.sub(r'[\\/*?:"<>|]', "_", str(nombre))
        return nombre_limpio.strip().upper().replace(" ", "_")

    @staticmethod
    def _obtener_nombre_archivo(tipo: str, formato: str) -> str:
        """Genera nombre de archivo VIGENTE (sin timestamp)"""
        return f"{tipo}.{formato}"

    # ========================================================================
    # REPORTE 1: LISTADO GENERAL (CONCENTRADO POR CLIENTE)
    # ========================================================================

    @staticmethod
    def generar_listado_general_pdf() -> Optional[str]:
        """Genera PDF del listado general concentrado por cliente"""
        try:
            CxcReportes._crear_carpetas()
            datos = CxcRepository.get_saldos_por_cliente()

            if not datos:
                return None

            ruta = get_pdf_path("CXC", CxcReportes._obtener_nombre_archivo("ListadoGeneral", "pdf"))

            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            content = []
            content.append(Paragraph("CUENTAS POR COBRAR - LISTADO GENERAL", title_style))
            content.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                     styles['Normal']))
            content.append(Spacer(1, 0.2 * inch))

            table_data = [['CLIENTE', 'IMPORTE TOTAL', 'ENTREGAS', 'SALDO']]
            total_importe = Decimal('0.00')
            total_entregas = Decimal('0.00')
            total_saldo = Decimal('0.00')

            for row in datos:
                importe = Decimal(str(row['total_facturado']))
                entregas = Decimal(str(row['total_abonado']))
                saldo = Decimal(str(row['saldo']))

                table_data.append([
                    row['cliente_nombre'].upper(),
                    f"${importe:,.2f}",
                    f"${entregas:,.2f}",
                    f"${saldo:,.2f}"
                ])

                total_importe += importe
                total_entregas += entregas
                total_saldo += saldo

            table_data.append([
                'TOTALES',
                f"${total_importe:,.2f}",
                f"${total_entregas:,.2f}",
                f"${total_saldo:,.2f}"
            ])

            table = Table(table_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))

            content.append(table)
            doc.build(content)
            return ruta

        except PermissionError:
            raise RuntimeError(
                "El archivo 'ListadoGeneral.pdf' está abierto en otro programa. Por favor, ciérrelo e intente nuevamente.")
        except Exception as e:
            raise RuntimeError(f"Error generando PDF de listado general: {str(e)}")

    @staticmethod
    def generar_listado_general_excel() -> Optional[str]:
        """Genera Excel del listado general concentrado por cliente"""
        try:
            CxcReportes._crear_carpetas()
            datos = CxcRepository.get_saldos_por_cliente()

            if not datos:
                return None

            ruta = os.path.join(
                CxcReportes.RUTA_BASE, "Excel", "ListadoGeneral",
                CxcReportes._obtener_nombre_archivo("ListadoGeneral", "xlsx")
            )

            wb = Workbook()
            ws = wb.active
            ws.title = "Listado General"

            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            border = Border(
                left=Side(style='thin', color='444444'),
                right=Side(style='thin', color='444444'),
                top=Side(style='thin', color='444444'),
                bottom=Side(style='thin', color='444444')
            )

            headers = ['CLIENTE', 'IMPORTE TOTAL', 'ENTREGAS', 'SALDO']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = border

            total_importe = Decimal('0.00')
            total_entregas = Decimal('0.00')
            total_saldo = Decimal('0.00')

            for row_idx, row in enumerate(datos, 2):
                importe = Decimal(str(row['total_facturado']))
                entregas = Decimal(str(row['total_abonado']))
                saldo = Decimal(str(row['saldo']))

                ws.cell(row=row_idx, column=1, value=row['cliente_nombre'].upper()).border = border
                ws.cell(row=row_idx, column=2, value=importe).border = border
                ws.cell(row=row_idx, column=3, value=entregas).border = border
                ws.cell(row=row_idx, column=4, value=saldo).border = border

                total_importe += importe
                total_entregas += entregas
                total_saldo += saldo

            row_idx = len(datos) + 2
            ws.cell(row=row_idx, column=1, value="TOTALES").font = Font(bold=True)
            ws.cell(row=row_idx, column=2, value=total_importe).font = Font(bold=True)
            ws.cell(row=row_idx, column=3, value=total_entregas).font = Font(bold=True)
            ws.cell(row=row_idx, column=4, value=total_saldo).font = Font(bold=True)

            for row in range(2, row_idx + 1):
                for col in range(2, 5):
                    ws.cell(row=row, column=col).number_format = '$#,##0.00'

            ws.column_dimensions['A'].width = 40
            ws.column_dimensions['B'].width = 18
            ws.column_dimensions['C'].width = 18
            ws.column_dimensions['D'].width = 18

            ws.freeze_panes = 'A2'
            wb.save(ruta)
            return ruta

        except PermissionError:
            raise RuntimeError(
                "El archivo 'ListadoGeneral.xlsx' está abierto en otro programa. Por favor, ciérrelo e intente nuevamente.")
        except Exception as e:
            raise RuntimeError(f"Error generando Excel de listado general: {str(e)}")

    # ========================================================================
    # REPORTE 2: ESTADO DE CUENTA POR CLIENTE
    # ========================================================================

    @staticmethod
    def generar_estado_cliente_pdf(cliente_id: int, cliente_nombre: str) -> Optional[str]:
        """Genera PDF del estado de cuenta de un cliente específico"""
        try:
            CxcReportes._crear_carpetas()
            datos = CxcRepository.get_detalle_por_cliente(cliente_id)

            if not datos:
                return None

            nombre_cliente_limpio = CxcReportes._sanitizar_nombre_archivo(cliente_nombre)
            ruta = get_pdf_path("CXC", f"EstadoCliente_{nombre_cliente_limpio}.pdf")

            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=20,
                alignment=TA_CENTER
            )

            content = []
            content.append(Paragraph("ESTADO DE CUENTA", title_style))
            content.append(Paragraph(f"Cliente: {cliente_nombre.upper()}", styles['Normal']))
            content.append(Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
            content.append(Spacer(1, 0.2 * inch))

            table_data = [['FOLIO', 'PRESUPUESTO', 'FECHA', 'TOTAL', 'ABONADO', 'SALDO']]
            total_general = Decimal('0.00')
            abonado_general = Decimal('0.00')
            saldo_general = Decimal('0.00')

            for row in datos:
                total = Decimal(str(row['total']))
                abonado = Decimal(str(row['abonado']))
                saldo = Decimal(str(row['saldo']))

                table_data.append([
                    row['folio'],
                    str(row['presupuesto_numero']) if row['presupuesto_numero'] else 'N/A',
                    row['fecha_emision'].strftime('%d/%m/%Y'),
                    f"${total:,.2f}",
                    f"${abonado:,.2f}",
                    f"${saldo:,.2f}"
                ])

                total_general += total
                abonado_general += abonado
                saldo_general += saldo

            table_data.append([
                'TOTALES',
                '',
                '',
                f"${total_general:,.2f}",
                f"${abonado_general:,.2f}",
                f"${saldo_general:,.2f}"
            ])

            table = Table(table_data, colWidths=[1.2 * inch, 1 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))

            content.append(table)
            doc.build(content)
            return ruta

        except PermissionError:
            raise RuntimeError(
                f"El archivo '{CxcReportes._sanitizar_nombre_archivo(cliente_nombre)}.pdf' está abierto en otro programa. Por favor, ciérrelo e intente nuevamente.")
        except Exception as e:
            raise RuntimeError(f"Error generando PDF de estado de cliente: {str(e)}")

    @staticmethod
    def generar_estado_cliente_excel(cliente_id: int, cliente_nombre: str) -> Optional[str]:
        """Genera Excel del estado de cuenta de un cliente específico"""
        try:
            CxcReportes._crear_carpetas()
            datos = CxcRepository.get_detalle_por_cliente(cliente_id)

            if not datos:
                return None

            nombre_cliente_limpio = CxcReportes._sanitizar_nombre_archivo(cliente_nombre)
            ruta = os.path.join(CxcReportes.RUTA_BASE, "Excel", "EstadoCliente", f"{nombre_cliente_limpio}.xlsx")

            wb = Workbook()
            ws = wb.active
            ws.title = "Estado de Cuenta"

            header_font = Font(bold=True, color="FFFFFF", size=10)
            header_fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            border = Border(
                left=Side(style='thin', color='444444'),
                right=Side(style='thin', color='444444'),
                top=Side(style='thin', color='444444'),
                bottom=Side(style='thin', color='444444')
            )

            headers = ['FOLIO', 'PRESUPUESTO', 'FECHA', 'TOTAL', 'ABONADO', 'SALDO']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = border

            total_general = Decimal('0.00')
            abonado_general = Decimal('0.00')
            saldo_general = Decimal('0.00')

            for row_idx, row in enumerate(datos, 2):
                total = Decimal(str(row['total']))
                abonado = Decimal(str(row['abonado']))
                saldo = Decimal(str(row['saldo']))

                ws.cell(row=row_idx, column=1, value=row['folio']).border = border
                ws.cell(row=row_idx, column=2,
                        value=row['presupuesto_numero'] if row['presupuesto_numero'] else '').border = border
                ws.cell(row=row_idx, column=3, value=row['fecha_emision'].strftime('%d/%m/%Y')).border = border
                ws.cell(row=row_idx, column=4, value=total).border = border
                ws.cell(row=row_idx, column=5, value=abonado).border = border
                ws.cell(row=row_idx, column=6, value=saldo).border = border

                total_general += total
                abonado_general += abonado
                saldo_general += saldo

            row_idx = len(datos) + 2
            ws.cell(row=row_idx, column=1, value="TOTALES").font = Font(bold=True)
            ws.cell(row=row_idx, column=4, value=total_general).font = Font(bold=True)
            ws.cell(row=row_idx, column=5, value=abonado_general).font = Font(bold=True)
            ws.cell(row=row_idx, column=6, value=saldo_general).font = Font(bold=True)

            for row in range(2, row_idx + 1):
                for col in range(4, 7):
                    ws.cell(row=row, column=col).number_format = '$#,##0.00'

            for col, width in enumerate(['A', 'B', 'C', 'D', 'E', 'F'], 1):
                ws.column_dimensions[get_column_letter(col)].width = 15

            ws.freeze_panes = 'A2'
            wb.save(ruta)
            return ruta

        except PermissionError:
            raise RuntimeError(
                f"El archivo '{CxcReportes._sanitizar_nombre_archivo(cliente_nombre)}.xlsx' está abierto en otro programa. Por favor, ciérrelo e intente nuevamente.")
        except Exception as e:
            raise RuntimeError(f"Error generando Excel de estado de cliente: {str(e)}")

    # ========================================================================
    # REPORTE 3: TODOS LOS MOVIMIENTOS
    # ========================================================================

    @staticmethod
    def generar_movimientos_pdf(filtros: Optional[Dict] = None) -> Optional[str]:
        """Genera PDF de todos los movimientos CXC"""
        try:
            CxcReportes._crear_carpetas()
            datos = CxcRepository.get_all_for_export(filtros or {})

            if not datos:
                return None

            ruta = get_pdf_path("CXC", CxcReportes._obtener_nombre_archivo("Movimientos", "pdf"))

            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=20,
                alignment=TA_CENTER
            )

            content = []
            content.append(Paragraph("CUENTAS POR COBRAR - TODOS LOS MOVIMIENTOS", title_style))
            content.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                     styles['Normal']))
            content.append(Spacer(1, 0.2 * inch))

            table_data = [['FOLIO', 'CLIENTE', 'FECHA', 'TOTAL', 'SALDO', 'ESTADO']]
            total_general = Decimal('0.00')
            saldo_general = Decimal('0.00')

            for row in datos:
                total = Decimal(str(row['total']))
                saldo = Decimal(str(row['saldo_pendiente']))

                table_data.append([
                    row['folio'],
                    row['cliente_nombre'][:30].upper(),
                    row['fecha_emision'].strftime('%d/%m/%Y'),
                    f"${total:,.2f}",
                    f"${saldo:,.2f}",
                    row['estado']
                ])

                total_general += total
                saldo_general += saldo

            table_data.append([
                'TOTALES',
                '',
                '',
                f"${total_general:,.2f}",
                f"${saldo_general:,.2f}",
                ''
            ])

            table = Table(table_data, colWidths=[1 * inch, 2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
                ('FONTSIZE', (0, 1), (-1, -2), 8),
            ]))

            content.append(table)
            doc.build(content)
            return ruta

        except PermissionError:
            raise RuntimeError(
                "El archivo 'Movimientos.pdf' está abierto en otro programa. Por favor, ciérrelo e intente nuevamente.")
        except Exception as e:
            raise RuntimeError(f"Error generando PDF de movimientos: {str(e)}")

    @staticmethod
    def generar_movimientos_excel(filtros: Optional[Dict] = None) -> Optional[str]:
        """Genera Excel de todos los movimientos CXC"""
        try:
            CxcReportes._crear_carpetas()
            datos = CxcRepository.get_all_for_export(filtros or {})

            if not datos:
                return None

            ruta = os.path.join(
                CxcReportes.RUTA_BASE, "Excel", "Movimientos",
                CxcReportes._obtener_nombre_archivo("Movimientos", "xlsx")
            )

            wb = Workbook()
            ws = wb.active
            ws.title = "Movimientos CXC"

            header_font = Font(bold=True, color="FFFFFF", size=10)
            header_fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            border = Border(
                left=Side(style='thin', color='444444'),
                right=Side(style='thin', color='444444'),
                top=Side(style='thin', color='444444'),
                bottom=Side(style='thin', color='444444')
            )

            headers = ['FOLIO', 'CLIENTE', 'FECHA', 'TOTAL', 'SALDO', 'ESTADO']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = border

            total_general = Decimal('0.00')
            saldo_general = Decimal('0.00')

            for row_idx, row in enumerate(datos, 2):
                total = Decimal(str(row['total']))
                saldo = Decimal(str(row['saldo_pendiente']))

                ws.cell(row=row_idx, column=1, value=row['folio']).border = border
                ws.cell(row=row_idx, column=2, value=row['cliente_nombre'][:50].upper()).border = border
                ws.cell(row=row_idx, column=3, value=row['fecha_emision'].strftime('%d/%m/%Y')).border = border
                ws.cell(row=row_idx, column=4, value=total).border = border
                ws.cell(row=row_idx, column=5, value=saldo).border = border
                ws.cell(row=row_idx, column=6, value=row['estado']).border = border

                total_general += total
                saldo_general += saldo

            row_idx = len(datos) + 2
            ws.cell(row=row_idx, column=1, value="TOTALES").font = Font(bold=True)
            ws.cell(row=row_idx, column=4, value=total_general).font = Font(bold=True)
            ws.cell(row=row_idx, column=5, value=saldo_general).font = Font(bold=True)

            for row in range(2, row_idx + 1):
                for col in [4, 5]:
                    ws.cell(row=row, column=col).number_format = '$#,##0.00'

            column_widths = {'A': 12, 'B': 35, 'C': 12, 'D': 15, 'E': 15, 'F': 12}
            for col_letter, width in column_widths.items():
                ws.column_dimensions[col_letter].width = width

            ws.freeze_panes = 'A2'
            wb.save(ruta)
            return ruta

        except PermissionError:
            raise RuntimeError(
                "El archivo 'Movimientos.xlsx' está abierto en otro programa. Por favor, ciérrelo e intente nuevamente.")
        except Exception as e:
            raise RuntimeError(f"Error generando Excel de movimientos: {str(e)}")
