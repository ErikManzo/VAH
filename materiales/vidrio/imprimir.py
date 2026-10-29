# D:\vah\materiales\vidrio\imprimir.py
"""
Generación de PDF para listado de materiales (Vidrio).
Requiere reportlab:  pip install reportlab
"""

import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from common.pdf_utils import get_pdf_path

def _draw_header(c: canvas.Canvas, title: str, y: float):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, title)
    y -= 6*mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.white)
    c.rect(20*mm, y-5*mm, 170*mm, 6*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(22*mm, y-4*mm, "CLAVE")
    c.drawString(70*mm, y-4*mm, "DESCRIPCIÓN")
    c.drawRightString(188*mm, y-4*mm, "PRECIO")
    c.setFillColor(colors.black)
    return y-2*mm

def _draw_footer(c: canvas.Canvas, page_num: int):
    c.setFont("Helvetica", 9)
    c.drawCentredString(105*mm, 10*mm, f"Pagina {page_num}")

def imprimir_pdf_guardar(registros, parent, filename: str,
                         title: str = "Materiales vidrio",
                         page_size: str = "LETTER",
                         orientation: str = "portrait",
                         repeat_header: bool = True,
                         footer_pattern: str = "Pagina {page}"):
    """
    Crea un PDF carta vertical con encabezado por página y pie "Pagina X".
    registros: lista de dicts con keys: clave, descripcion, precio
    """
    if not os.path.isabs(filename):
        filename = get_pdf_path("Vidrio", filename)
    page = letter  # carta
    c = canvas.Canvas(filename, pagesize=page)

    left_x = 20*mm
    y = 268*mm  # top margin
    line_h = 7*mm
    page_num = 1

    def header():
        nonlocal y
        y = _draw_header(c, title, 280*mm)

    header()
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)

    for r in registros:
        if y < 20*mm:  # nueva página
            _draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            header()
            c.setFont("Helvetica", 10)

        clave = str(r.get("clave", "") or "")
        desc  = str(r.get("descripcion", "") or "")
        precio = r.get("precio", 0)
        try:
            precio_str = f"{float(precio):,.2f}"
        except Exception:
            precio_str = "0.00"

        # líneas
        c.setFillColor(colors.black)
        c.drawString(22*mm, y, clave[:30])
        c.drawString(70*mm, y, desc[:75])
        c.drawRightString(188*mm, y, precio_str)
        y -= line_h

    _draw_footer(c, page_num)
    c.save()
#
#
#
