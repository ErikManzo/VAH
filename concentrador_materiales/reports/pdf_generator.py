# -*- coding: utf-8 -*-
"""
Generador de archivos PDF para el concentrador de materiales
"""
import os
from datetime import datetime
from typing import List


from common.logger_config import get_logger
logger = get_logger('concentrador.reports.pdf_generator')

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, KeepTogether
    )
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from concentrador_materiales.models.concentrado import ReporteConcentrado, MaterialConcentrado

class PDFGenerator:
    """
    Genera archivos PDF a partir de un ReporteConcentrado.
    """

    @classmethod
    def generar(cls, reporte: ReporteConcentrado, ruta_archivo: str) -> bool:
        """
        Genera un archivo PDF con el concentrador de materiales.

        Args:
            reporte: ReporteConcentrado con los datos
            ruta_archivo: Ruta donde guardar el archivo

        Returns:
            bool: True si se generó correctamente
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab no está instalado. Ejecute: pip install reportlab")

        doc = SimpleDocTemplate(
            ruta_archivo,
            pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch
        )

        story = []

        # Estilos
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=1,  # Centro
            spaceAfter=20
        )
        subtitulo_style = ParagraphStyle(
            'Subtitulo',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        normal_style = styles['Normal']

        # CORRECCIÓN: Estilo para celdas de tabla con ajuste automático de texto
        celda_style = ParagraphStyle(
            'Celda',
            parent=styles['Normal'],
            fontSize=8,
            leading=9,
            wordWrap='CJK'  # Permite ajuste de palabras
        )

        # Portada
        story.append(Paragraph("ERP VAH", titulo_style))
        story.append(Paragraph("CONCENTRADOR DE MATERIALES", titulo_style))
        story.append(Spacer(1, 20))
        story.append(
            Paragraph(f"Fecha de generación: {reporte.fecha_generacion.strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 30))

        # Resumen ejecutivo
        story.append(Paragraph("RESUMEN EJECUTIVO", subtitulo_style))
        story.append(Spacer(1, 10))

        resumen_data = [
            ["Presupuestos procesados:", str(reporte.total_presupuestos)],
            ["Partidas procesadas:", str(reporte.total_partidas)],
            ["Materiales concentrados:", str(reporte.total_materiales)],
        ]

        resumen_tabla = Table(resumen_data, colWidths=[3 * inch, 2 * inch])
        resumen_tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(resumen_tabla)
        story.append(Spacer(1, 20))

        # Tabla por almacén
        story.append(Paragraph("DETALLE POR ALMACÉN", subtitulo_style))
        story.append(Spacer(1, 10))

        for almacen, materiales in reporte.materiales_por_almacen.items():
            if not materiales:
                continue

            story.append(Paragraph(f"<b>{almacen}</b>", subtitulo_style))

            # CORRECCIÓN: Ajustar anchos para dar más espacio a descripción
            if almacen == "ALUMINIO":
                headers = ["Clave", "Descripción", "Metros (m)", "Largo (m)", "TRAMOS"]
                campos = ["clave", "descripcion", "metros_totales", "largo_tramo", "tramos_calculados"]
                anchos = [0.7 * inch, 3.0 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch]
            elif almacen == "VIDRIO":
                headers = ["Clave", "Descripción", "m²", "HOJAS"]
                campos = ["clave", "descripcion", "m2_totales", "hojas_calculadas"]
                anchos = [0.7 * inch, 3.5 * inch, 0.7 * inch, 0.7 * inch]
            elif almacen == "HERRERIA":
                headers = ["Clave", "Descripción", "Metros (m)", "TRAMOS 6m"]
                campos = ["clave", "descripcion", "metros_totales", "tramos_calculados"]
                anchos = [0.7 * inch, 3.3 * inch, 0.7 * inch, 0.7 * inch]
            elif almacen == "HERRAJES":
                headers = ["Clave", "Descripción", "PIEZAS"]
                campos = ["clave", "descripcion", "piezas_calculadas"]
                anchos = [0.7 * inch, 3.5 * inch, 0.7 * inch]
            else:
                # PLASTICOS y OTROS
                headers = ["Clave", "Descripción", "CANTIDAD"]
                campos = ["clave", "descripcion", "cantidad"]
                anchos = [0.7 * inch, 3.5 * inch, 0.7 * inch]

            # Construir datos de la tabla
            # CORRECCIÓN: Usar Paragraph para campos de texto largo (descripción)
            data = [headers]
            for material in materiales:
                row = []
                for campo in campos:
                    valor = cls._obtener_valor(material, campo)
                    if isinstance(valor, float):
                        valor = f"{valor:.2f}"
                    elif valor is None:
                        valor = ""

                    # CORRECCIÓN: Envolver descripción en Paragraph para ajuste automático
                    if campo == "descripcion":
                        row.append(Paragraph(str(valor), celda_style))
                    else:
                        row.append(str(valor))
                data.append(row)

            # Agregar totales - Ajustado a la nueva cantidad de columnas
            if almacen in ["ALUMINIO", "VIDRIO"]:
                total_row = ["TOTAL", "", "", "", ""]  # 5 columnas
            elif almacen in ["HERRERIA", "HERRAJES"]:
                total_row = ["TOTAL", "", "", ""]  # 4 columnas
            else:
                total_row = ["TOTAL", "", ""]  # 3 columnas

            if almacen == "ALUMINIO":
                total_metros = sum(m.metros_totales or 0 for m in materiales)
                total_tramos = sum(m.tramos_calculados or 0 for m in materiales)
                total_row[2] = f"{total_metros:.2f}"
                total_row[4] = str(total_tramos)
            elif almacen == "VIDRIO":
                total_m2 = sum(m.m2_totales or 0 for m in materiales)
                total_hojas = sum(m.hojas_calculadas or 0 for m in materiales)
                total_row[2] = f"{total_m2:.2f}"
                total_row[3] = str(total_hojas)
            elif almacen == "HERRERIA":
                total_metros = sum(m.metros_totales or 0 for m in materiales)
                total_tramos = sum(m.tramos_calculados or 0 for m in materiales)
                total_row[2] = f"{total_metros:.2f}"
                total_row[3] = str(total_tramos)
            elif almacen == "HERRAJES":
                total_piezas = sum(m.piezas_calculadas or 0 for m in materiales)
                total_row[2] = f"{total_piezas:.0f}"
            else:
                total_cantidad = sum(m.cantidad for m in materiales)
                total_row[2] = f"{total_cantidad:.0f}"

            data.append(total_row)

            # CORRECCIÓN: Tabla con ajuste automático de altura
            tabla = Table(data, colWidths=anchos, repeatRows=1)
            tabla.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f6feb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                # CORRECCIÓN: Permitir que las filas crezcan en altura
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))

            story.append(tabla)
            story.append(Spacer(1, 20))

        # Advertencias
        if reporte.advertencias:
            story.append(PageBreak())
            story.append(Paragraph("ADVERTENCIAS", subtitulo_style))
            story.append(Spacer(1, 10))

            warn_data = [["Código", "Mensaje"]]
            for adv in reporte.advertencias:
                warn_data.append([
                    adv.get("codigo", ""),
                    Paragraph(adv.get("mensaje", "")[:150], celda_style)
                ])

            warn_tabla = Table(warn_data, colWidths=[1.2 * inch, 5.3 * inch])
            warn_tabla.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(warn_tabla)

        # Errores
        if reporte.errores:
            story.append(Spacer(1, 10))
            story.append(Paragraph("ERRORES", subtitulo_style))
            story.append(Spacer(1, 10))

            err_data = [["Código", "Mensaje"]]
            for err in reporte.errores:
                err_data.append([
                    err.get("codigo", ""),
                    Paragraph(err.get("mensaje", "")[:150], celda_style)
                ])

            err_tabla = Table(err_data, colWidths=[1.2 * inch, 5.3 * inch])
            err_tabla.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(err_tabla)

        # Pie de página
        def footer(canvas_obj, doc):
            canvas_obj.saveState()
            canvas_obj.setFont('Helvetica', 8)
            canvas_obj.drawString(
                doc.leftMargin,
                doc.bottomMargin - 20,
                f"ERP VAH - Concentrador de Materiales - Página {canvas_obj.getPageNumber()}"
            )
            canvas_obj.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        return True

    @classmethod
    def _obtener_valor(cls, material: MaterialConcentrado, campo: str):
        """Obtiene el valor de un campo del material."""
        if campo == "dimensiones" and material.ancho_original and material.alto_original:
            return f"{material.ancho_original:.2f}×{material.alto_original:.2f}"
        if campo == "largo_tramo":
            return material.largo_tramo or 6.10

        valor = getattr(material, campo, None)

        # Fallback para campos calculados que puedan ser None
        if valor is None and campo in ["tramos_calculados", "hojas_calculadas", "piezas_calculadas"]:
            return 0

        return valor