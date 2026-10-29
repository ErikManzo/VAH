# -*- coding: utf-8 -*-
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

from common.pdf_utils import get_pdf_path

def generar_estado_cuenta_pdf(cxc_data, pagos_data, cliente_nombre: str) -> str:
    """Genera PDF alineado al flujo VAH. Recibe datos ya cargados."""
    filename = f"estado_cuenta_{cxc_data.folio}.pdf"
    pdf_path = get_pdf_path("CXC", filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=16)

    content = []
    content.append(Paragraph(f"ESTADO DE CUENTA - {cxc_data.folio}", title_style))
    content.append(Paragraph(f"CLIENTE: {cliente_nombre}", styles['Normal']))
    content.append(Spacer(1, 0.2 * inch))

    fecha_ref = cxc_data.fecha_acuerdo.strftime("%d/%m/%Y") if cxc_data.fecha_acuerdo else "POR DEFINIR"
    data = [
        ["FECHA EMISIÓN", cxc_data.fecha_emision.strftime("%d/%m/%Y")],
        ["FECHA ACUERDO / REF.", fecha_ref],
        ["SUBTOTAL", f"${cxc_data.subtotal:,.2f}"],
        ["DESCUENTO", f"${cxc_data.descuento_monto or 0:,.2f}"],
        ["IVA", f"${cxc_data.iva_monto or 0:,.2f}"],
        ["TOTAL", f"${cxc_data.total:,.2f}"],
        ["SALDO PENDIENTE", f"${cxc_data.saldo_pendiente:,.2f}"],
    ]
    table = Table(data, colWidths=[2 * inch, 3 * inch])
    table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    content.append(table)
    content.append(Spacer(1, 0.2 * inch))
    content.append(Paragraph("REGISTRO DE PAGOS", styles['Heading3']))

    if pagos_data:
        pdata = [["FECHA", "MONTO", "MÉTODO", "CONCEPTO", "CUENTA"]]
        for p in pagos_data:
            pdata.append(
                [p.fecha_pago.strftime("%d/%m/%Y"), f"${p.monto:,.2f}", p.metodo_pago, p.concepto, p.cuenta_destino])
        ptable = Table(pdata)
        ptable.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
        content.append(ptable)
    else:
        content.append(Paragraph("NO HAY PAGOS REGISTRADOS", styles['Normal']))

    doc.build(content)
    return pdf_path
