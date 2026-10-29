


# D:\vah\materiales\herrajes\imprimir.py
r"""
Generación de PDF para Materiales Herrajes.

- Tamaño carta (LETTER), orientación vertical por defecto.
- Encabezado principal (title).
- Títulos de columnas en TODAS las hojas.
- Pie de página centrado "Pagina X".
"""

import os
from decimal import Decimal
from typing import List, Dict, Optional

from common.pdf_utils import get_pdf_path

from common.logger_config import get_logger
logger = get_logger('materiales.herrajes.imprimir')

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.units import mm
except Exception as e:
    # Si falta reportlab, da un error claro al intentar usar la función
    raise ImportError(
        "Falta la dependencia 'reportlab'. Instala con: pip install reportlab"
    ) from e

def _page_size(size_name: str, orientation: str):
    size_name = (size_name or "LETTER").upper()
    orientation = (orientation or "portrait").lower()
    base = letter  # único tamaño requerido
    if orientation == "landscape":
        base = landscape(base)
    return base

def _to_decimal2(val) -> Decimal:
    try:
        if isinstance(val, Decimal):
            d = val
        else:
            d = Decimal(str(val))
        return d.quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")

def imprimir_pdf_guardar(
    registros: List[Dict],
    parent=None,
    filename: str = "Materiales herrajes.pdf",
    title: str = "Materiales herrajes",
    page_size: str = "LETTER",
    orientation: str = "portrait",
    repeat_header: bool = True,
    footer_pattern: Optional[str] = "Pagina {page}",
):
    """
    Genera un PDF con columnas: CLAVE, DESCRIPCIÓN, PRECIO.
    - filename: ruta destino (se crea/reescribe).
    - title: encabezado principal en cada página.
    - page_size: "LETTER".
    - orientation: "portrait" | "landscape".
    - repeat_header: True -> pinta encabezado/títulos en cada página.
    - footer_pattern: ej. "Pagina {page}".
    """
    pagesize = _page_size(page_size, orientation)
    if not os.path.isabs(filename):
        filename = get_pdf_path("Herrajes", filename)
    c = canvas.Canvas(filename, pagesize=pagesize)

    # Márgenes
    left = 18 * mm
    right = 18 * mm
    top = 18 * mm
    bottom = 18 * mm
    width, height = pagesize

    # Columnas
    x_clave = left
    x_desc = left + 45 * mm
    x_prec_right = width - right  # drawRightString usará este borde derecho
    desc_max_width = (x_prec_right - 30 * mm) - x_desc  # espacio útil para descripción

    # Estilo
    c.setTitle(title)

    def draw_header():
        # Encabezado principal
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left, height - top, title)

        # Línea bajo encabezado
        c.setLineWidth(0.6)
        c.line(left, height - top - 4 * mm, width - right, height - top - 4 * mm)

        # Títulos de columnas
        c.setFont("Helvetica-Bold", 10)
        y = height - top - 10 * mm
        c.drawString(x_clave, y, "CLAVE")
        c.drawString(x_desc, y, "DESCRIPCIÓN")
        c.drawRightString(x_prec_right, y, "PRECIO")

        # Línea bajo títulos
        c.setLineWidth(0.4)
        c.line(left, y - 2 * mm, width - right, y - 2 * mm)
        return y - 5 * mm

    def draw_footer():
        if footer_pattern:
            c.setFont("Helvetica", 9)
            page_num = c.getPageNumber()
            txt = footer_pattern.format(page=page_num)
            tw = c.stringWidth(txt, "Helvetica", 9)
            c.drawString((width - tw) / 2.0, bottom / 2.0, txt)

    # Ordena por clave ascendente
    registros = sorted(registros, key=lambda r: (str(r.get("clave", "")).upper()))

    y = draw_header()
    line_h = 6.5 * mm
    c.setFont("Helvetica", 10)

    for r in registros:
        # Salto de página si no hay espacio
        if y < bottom + 15 * mm:
            draw_footer()
            c.showPage()
            if repeat_header:
                y = draw_header()
                c.setFont("Helvetica", 10)
            else:
                y = height - top

        clave = str(r.get("clave", "") or "")
        desc = str(r.get("descripcion", "") or "")
        precio = f"{_to_decimal2(r.get('precio', '0.00')):.2f}"

        # Recorte simple de descripción para evitar desbordes
        # (si quieres multilínea, aquí podríamos envolver por palabras)
        while c.stringWidth(desc, "Helvetica", 10) > desc_max_width and len(desc) > 0:
            desc = desc[:-1]

        # Dibujo
        c.drawString(x_clave, y, clave)
        c.drawString(x_desc, y, desc)
        c.drawRightString(x_prec_right, y, precio)

        y -= line_h

    draw_footer()
    c.save()
    return filename

#
#
#
