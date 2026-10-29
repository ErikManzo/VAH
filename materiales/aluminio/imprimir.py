# D:\vah\materiales\aluminio\imprimir.py

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas
from .utils import CAMPOS_PRECIO_BD, ordenar_registros_asc, dec2
from PyQt6.QtWidgets import QMessageBox
from common.logger_config import get_logger
from common.pdf_utils import get_pdf_path

logger = get_logger("materiales.aluminio.imprimir")


def imprimir_pdf_guardar(registros: list[dict], parent=None, filename="Materiales aluminio.pdf"):
    """Genera PDF estructurado con todos los registros de aluminio."""
    try:
        if not os.path.isabs(filename):
            filename = get_pdf_path("Aluminio", filename)
        # Ordenar registros
        regs = ordenar_registros_asc(list(registros))

        # Crear PDF
        c = pdfcanvas.Canvas(filename, pagesize=landscape(letter))
        width, height = landscape(letter)

        # Márgenes y estilos
        MARG_L = 10 * mm
        MARG_R = 10 * mm
        MARG_T = 12 * mm
        MARG_B = 12 * mm
        LINE_H = 5.4 * mm

        FONT_TITLE = ("Helvetica-Bold", 12)
        FONT_HEADER = ("Helvetica-Bold", 7.0)
        FONT_DATA = ("Helvetica", 6.2)
        FONT_DATA_MIN = 5.5

        # Encabezados y anchos de columnas
        headers = ["CLAVE", "DESCRIPCIÓN", "LARGO"] + [c.upper() for c in CAMPOS_PRECIO_BD]
        widths_mm = [16, 75, 14] + [11] * len(CAMPOS_PRECIO_BD)
        widths_pt = [w * mm for w in widths_mm]

        col_x = [MARG_L]
        for wpt in widths_pt[:-1]:
            col_x.append(col_x[-1] + wpt)

        # Dibujar encabezado
        def draw_header(page_no):
            c.setFont(*FONT_TITLE)
            c.drawCentredString(width / 2, height - MARG_T + 3 * mm, "Perfiles de aluminio")
            c.setFont(*FONT_HEADER)
            yh = height - MARG_T - 2 * mm
            for i, htxt in enumerate(headers):
                x_left = col_x[i]
                wpt = widths_pt[i]
                if i == 1:  # descripción
                    c.drawString(x_left, yh, htxt)
                else:
                    c.drawRightString(x_left + wpt - 1.2 * mm, yh, htxt)
            return yh - LINE_H

        # Dibujar pie de página
        def draw_footer(page_no):
            c.setFont("Helvetica", 8)
            c.drawCentredString(width / 2, MARG_B - 2 * mm, f"Página {page_no}")

        # Inicializar
        page = 1
        y = draw_header(page)
        c.setFont(*FONT_DATA)

        # Filas
        for r in regs:
            fila = [
                str(r.get("clave", "")),
                str(r.get("descripcion", "")),
                f"{dec2(r.get('largo', 0)):.2f}",
                *(f"{dec2(r.get(k, 0)):.2f}" for k in CAMPOS_PRECIO_BD)
            ]

            if y < (MARG_B + LINE_H):
                draw_footer(page)
                c.showPage()
                page += 1
                y = draw_header(page)
                c.setFont(*FONT_DATA)

            for i, val in enumerate(fila):
                x_left = col_x[i]
                wpt = widths_pt[i]
                if i == 1:  # descripción
                    c.drawString(x_left, y, val[:50])  # recorta texto largo
                else:
                    # Ajusta la fuente si es demasiado ancho
                    fs = FONT_DATA[1]
                    while fs >= FONT_DATA_MIN and c.stringWidth(val, FONT_DATA[0], fs) > (wpt - 2):
                        fs -= 0.2
                    c.setFont(FONT_DATA[0], fs)
                    c.drawRightString(x_left + wpt - 1.2 * mm, y, val)
                    c.setFont(*FONT_DATA)

            y -= LINE_H

        # Cerrar documento
        draw_footer(page)
        c.save()

        # ✅ NO mostramos mensaje aquí para evitar duplicados.
        # El mensaje se maneja en _on_imprimir (pantalla_materiales_aluminio.py)

    except Exception as e:
        if parent:
            QMessageBox.critical(parent, "Error", f"No fue posible generar el PDF:\n{e}")
        else:
            print(f"Error PDF: {e}")
        logger.exception("Error generando PDF de materiales de aluminio")
