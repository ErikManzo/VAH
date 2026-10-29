# -*- coding: utf-8 -*-
"""
Generador de Manual Tecnico - Modulo CXC VAH.
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
TIPO_MANUAL = "Tecnico"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUTA_BASE = os.path.join(PROJECT_ROOT, "manuales")
RUTA_TXT = os.path.join(RUTA_BASE, "txt")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf", "tecnico")

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


def _extraer_funciones(path: str):
    contenido = _leer(path)
    return re.findall(r"^def\s+([a-zA-Z0-9_]+)\(", contenido, re.MULTILINE)


def _placeholder(nombre: str):
    tabla = Table([[f"[Imagen pendiente: {nombre}]"]], colWidths=[160 * mm])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_GRIS_CLARO),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_AZUL_OSCURO),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    return tabla


class PlantillaPagina(PageTemplate):
    def __init__(self, doc, tipo_manual, modulo):
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
        self.tipo_manual = tipo_manual
        self.modulo = modulo
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
    def __init__(self, filename, tipo_manual, modulo):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
        )
        self.addPageTemplates([PlantillaPagina(self, tipo_manual, modulo)])


def construir_historia():
    historia = []
    fecha = datetime.datetime.now().strftime("%d/%m/%Y")
    pantalla_path = os.path.join(PROJECT_ROOT, "cxc", "art", "pantalla_cxc.py")
    dialogo_path = os.path.join(PROJECT_ROOT, "cxc", "art", "dialogs", "nuevo_cxc_dialog.py")
    service_path = os.path.join(PROJECT_ROOT, "cxc", "services", "cxc_service.py")
    repo_path = os.path.join(PROJECT_ROOT, "cxc", "repositories", "cxc_repository.py")
    estructura = _leer(os.path.join(RUTA_TXT, "estructura_final_cxc.txt"))
    notas = _leer(os.path.join(RUTA_TXT, "notas_cxc.txt"))

    historia.append(Paragraph("VAH", estilo_titulo))
    historia.append(Paragraph("Manual Tecnico - CXC", estilo_h1))
    historia.append(Paragraph(f"Version 1.0 | Generado el {fecha}", estilo_normal))

    historia.append(Paragraph("1. Arquitectura", estilo_h1))
    historia.append(Paragraph(
        "El modulo CXC sigue una arquitectura de capas: pantalla PyQt6, dialogos especializados, "
        "servicio de negocio y repositorios sobre SQL Server.",
        estilo_normal,
    ))
    historia.append(_placeholder("arquitectura_cxc.png"))

    historia.append(Paragraph("2. Componentes principales", estilo_h1))
    tabla = Table(
        [
            ["Componente", "Responsabilidad"],
            ["pantalla_cxc.py", "Ventana principal, filtros, tabs, reportes y menu."],
            ["nuevo_cxc_dialog.py", "Seleccion de presupuesto, partidas y cantidades facturadas."],
            ["cxc_service.py", "Calculo de subtotal, descuentos, IVA y persistencia del CXC."],
            ["cxc_repository.py", "Consultas de listado, detalle y resumen general."],
        ],
        colWidths=[55 * mm, 105 * mm],
    )
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_AZUL),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cfd8e3")),
                ("BACKGROUND", (0, 1), (-1, -1), COLOR_GRIS_CLARO),
            ]
        )
    )
    historia.append(tabla)
    historia.append(Spacer(1, 3 * mm))

    historia.append(Paragraph("3. Docstrings y contratos", estilo_h1))
    for titulo, path in [
        ("Ventana principal", pantalla_path),
        ("Dialogo nuevo CXC", dialogo_path),
        ("Servicio CXC", service_path),
    ]:
        historia.append(Paragraph(titulo, estilo_h2))
        historia.append(Paragraph(escape(_extraer_docstring(path) or "Sin docstring disponible."), estilo_normal))

    historia.append(PageBreak())
    historia.append(Paragraph("4. Funciones clave", estilo_h1))
    historia.append(Paragraph("Servicio de CXC:", estilo_h2))
    historia.append(Preformatted("\n".join(_extraer_funciones(service_path)[:25]) or "Sin funciones detectadas.", estilo_codigo))
    historia.append(Paragraph("Repositorio principal:", estilo_h2))
    historia.append(Preformatted("\n".join(_extraer_funciones(repo_path)[:25]) or "Sin funciones detectadas.", estilo_codigo))

    historia.append(Paragraph("5. Estructura tecnica", estilo_h1))
    historia.append(Preformatted(estructura or "Estructura tecnica pendiente de documentar.", estilo_codigo))

    historia.append(Paragraph("6. Notas de mantenimiento", estilo_h1))
    historia.append(Preformatted(notas or "Sin notas tecnicas adicionales.", estilo_codigo))

    historia.append(Paragraph("7. Riesgos y puntos de cuidado", estilo_h1))
    historia.append(Paragraph(
        "Validar siempre la consistencia entre subtotal, descuento, IVA y saldo pendiente. "
        "Las modificaciones en el dialogo de alta deben reflejarse en cxc_detalle y en reportes asociados.",
        estilo_normal,
    ))
    historia.append(Paragraph("— Fin del Manual Tecnico —", estilo_pie))
    return historia


def generar_manual():
    os.makedirs(RUTA_PDF, exist_ok=True)
    ruta_salida = os.path.join(RUTA_PDF, "VAH_Manual_Tecnico_CXC.pdf")
    doc = DocManual(ruta_salida, TIPO_MANUAL, MODULO)
    doc.build(construir_historia())
    print(f"Manual Tecnico de {MODULO} generado: {ruta_salida}")
    return ruta_salida


if __name__ == "__main__":
    generar_manual()
