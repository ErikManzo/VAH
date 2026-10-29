# -*- coding: utf-8 -*-
"""
Generador de Manual Operativo - Modulo CXC VAH.
"""

import datetime
import os
import re
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.frames import Frame

MODULO = "CXC"
TIPO_MANUAL = "Operativo"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "cxc")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_TXT = os.path.join(RUTA_BASE, "txt")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf", "operativo")
RUTA_LOGO = os.path.join(RUTA_COMUNES, "logo_vah.png")

COLOR_AZUL = HexColor("#1f6feb")
COLOR_AZUL_OSCURO = HexColor("#1557b0")
COLOR_GRIS_CLARO = HexColor("#f0f4f8")
COLOR_GRIS_TEXTO = HexColor("#374151")

estilos = getSampleStyleSheet()
estilo_titulo = ParagraphStyle(
    "Titulo",
    parent=estilos["Title"],
    fontName="Helvetica-Bold",
    fontSize=24,
    textColor=COLOR_AZUL,
    alignment=TA_LEFT,
    spaceAfter=5 * mm,
)
estilo_h1 = ParagraphStyle(
    "H1",
    parent=estilos["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    textColor=COLOR_AZUL,
    spaceBefore=7 * mm,
    spaceAfter=3 * mm,
)
estilo_h2 = ParagraphStyle(
    "H2",
    parent=estilos["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    textColor=COLOR_AZUL_OSCURO,
    spaceBefore=5 * mm,
    spaceAfter=2 * mm,
)
estilo_normal = ParagraphStyle(
    "NormalManual",
    parent=estilos["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    alignment=TA_JUSTIFY,
    textColor=COLOR_GRIS_TEXTO,
    spaceAfter=3 * mm,
)
estilo_pie = ParagraphStyle(
    "Pie",
    parent=estilos["Normal"],
    fontSize=7,
    alignment=TA_CENTER,
    textColor=HexColor("#9ca3af"),
)
estilo_codigo = ParagraphStyle(
    "Codigo",
    parent=estilos["Code"],
    fontName="Courier",
    fontSize=8,
    leading=10,
    backColor=COLOR_GRIS_CLARO,
    leftIndent=4 * mm,
    rightIndent=4 * mm,
)


def _leer(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().strip()


def _extraer_docstring(path: str) -> str:
    contenido = _leer(path)
    if not contenido:
        return ""
    match = re.search(r'^[ruRU]{0,2}("""|\'\'\')([\s\S]*?)\1', contenido, re.MULTILINE)
    return (match.group(2).strip() if match else "").strip()


def _placeholder(nombre: str):
    tabla = Table([[f"[Imagen pendiente: {nombre}]"]], colWidths=[160 * mm])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_GRIS_CLARO),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_AZUL_OSCURO),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_GRIS_TEXTO),
            ]
        )
    )
    return tabla


class PlantillaPagina(PageTemplate):
    def __init__(self, doc, tipo_manual, modulo, logo_path):
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
        self.tipo_manual = tipo_manual
        self.modulo = modulo
        self.logo_path = logo_path
        super().__init__(id="manual", frames=[frame], onPage=self._dibujar)

    def _dibujar(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(COLOR_AZUL)
        canvas.drawString(doc.leftMargin, doc.pagesize[1] - 12 * mm, f"VAH - Manual {self.tipo_manual} - {self.modulo}")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLOR_GRIS_TEXTO)
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 10 * mm, f"Pagina {canvas.getPageNumber()}")
        canvas.restoreState()


class DocManual(BaseDocTemplate):
    def __init__(self, filename, tipo_manual, modulo, logo_path):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
        )
        self.addPageTemplates([PlantillaPagina(self, tipo_manual, modulo, logo_path)])


def construir_historia():
    historia = []
    fecha = datetime.datetime.now().strftime("%d/%m/%Y")
    pantalla_doc = _extraer_docstring(r"D:\vah\cxc\art\pantalla_cxc.py")
    dialogo_doc = _extraer_docstring(r"D:\vah\cxc\art\dialogs\nuevo_cxc_dialog.py")
    notas = _leer(os.path.join(RUTA_TXT, "notas_cxc.txt"))
    instructivo = _leer(os.path.join(RUTA_TXT, "instructivo_imagenes_cxc.txt"))

    historia.append(Paragraph("VAH", estilo_titulo))
    historia.append(Paragraph("Manual Operativo - CXC", estilo_h1))
    historia.append(Paragraph(f"Version 1.0 | Generado el {fecha}", estilo_normal))
    historia.append(Paragraph(
        "Este manual describe el uso operativo del modulo de Cuentas por Cobrar (CXC), "
        "incluyendo apertura de registros, generacion de CXC desde presupuesto, registro de abonos y consulta de reportes.",
        estilo_normal,
    ))

    historia.append(Paragraph("1. Panorama del modulo", estilo_h1))
    historia.append(Paragraph(escape(pantalla_doc or "Modulo de CXC sin docstring disponible."), estilo_normal))
    historia.append(_placeholder("cxc_ventana_principal.png"))
    historia.append(Spacer(1, 4 * mm))

    historia.append(Paragraph("2. Crear CXC desde presupuesto", estilo_h1))
    historia.append(Paragraph(
        "El flujo inicia desde Archivo > Nuevo CXC (desde presupuesto). El dialogo permite seleccionar el presupuesto, "
        "marcar partidas, editar cantidades facturadas y verificar el total estimado antes de guardar.",
        estilo_normal,
    ))
    historia.append(Paragraph(escape(dialogo_doc or "Dialogo sin docstring disponible."), estilo_normal))
    historia.append(_placeholder("nuevo_cxc_dialog.png"))
    historia.append(Spacer(1, 4 * mm))

    historia.append(Paragraph("3. Operaciones principales", estilo_h1))
    for texto in [
        "Filtrar por cliente, obra, folio y fechas.",
        "Registrar abonos o finiquitos desde menu y dialogo dedicado.",
        "Consultar listados generales, estados de cuenta y exportaciones a PDF/Excel.",
        "Ver saldos por cliente y detalle historico en pestañas.",
    ]:
        historia.append(Paragraph(f"• {escape(texto)}", estilo_normal))

    historia.append(Paragraph("4. Capturas requeridas", estilo_h1))
    historia.append(Paragraph(
        "Las siguientes imagenes deben capturarse para enriquecer la version final del manual.",
        estilo_normal,
    ))
    historia.append(Preformatted(instructivo or "[Imagen pendiente]", estilo_codigo))

    historia.append(PageBreak())
    historia.append(Paragraph("5. Notas operativas", estilo_h1))
    historia.append(Preformatted(notas or "No hay notas operativas adicionales para CXC.", estilo_codigo))

    historia.append(Paragraph("6. Validacion diaria", estilo_h1))
    historia.append(Paragraph(
        "Antes de cerrar la jornada operativa se recomienda revisar saldos pendientes, validar que los CXC nuevos "
        "se hayan generado con el cliente y presupuesto correctos, y verificar que los reportes PDF/Excel se abran sin errores.",
        estilo_normal,
    ))
    historia.append(Paragraph("— Fin del Manual Operativo —", estilo_pie))
    return historia


def generar_manual():
    os.makedirs(RUTA_PDF, exist_ok=True)
    ruta_salida = os.path.join(RUTA_PDF, "VAH_Manual_Operativo_CXC.pdf")
    doc = DocManual(ruta_salida, TIPO_MANUAL, MODULO, RUTA_LOGO)
    doc.build(construir_historia())
    print(f"Manual Operativo de {MODULO} generado: {ruta_salida}")
    return ruta_salida


if __name__ == "__main__":
    generar_manual()
