# D:\vah\manuales\scripts_generadores\generar_manual_tecnico_clientes.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Técnico - Módulo Clientes VAH
==================================================
"""

import os
import datetime
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak, Table, TableStyle, ListFlowable, ListItem

# ==================== CONFIGURACIÓN ====================
MODULO = "Clientes"
TIPO_MANUAL = "Técnico"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "clientes")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf", "tecnico")
RUTA_LOGO = os.path.join(RUTA_COMUNES, "logo_vah.png")

COLOR_AZUL = HexColor("#1f6feb")
COLOR_AZUL_OSCURO = HexColor("#1557b0")
COLOR_GRIS_CLARO = HexColor("#f0f4f8")
COLOR_GRIS_TEXTO = HexColor("#374151")

TAMANO_PAGINA = letter
ANCHO, ALTO = TAMANO_PAGINA
MARGEN_IZQ = 20 * mm
MARGEN_DER = 20 * mm
MARGEN_SUP = 25 * mm
MARGEN_INF = 25 * mm

FECHA_GENERACION = datetime.datetime.now().strftime("%d/%m/%Y")
VERSION = "1.0"

# ==================== ESTILOS ====================
estilos = getSampleStyleSheet()

estilo_normal = ParagraphStyle(
    'Normal',
    parent=estilos['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=COLOR_GRIS_TEXTO,
    alignment=TA_JUSTIFY,
    spaceAfter=4 * mm,
)

estilo_heading1 = ParagraphStyle(
    'Heading1',
    parent=estilos['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=20,
    textColor=COLOR_AZUL,
    spaceBefore=12 * mm,
    spaceAfter=6 * mm,
)

estilo_heading2 = ParagraphStyle(
    'Heading2',
    parent=estilos['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=COLOR_AZUL_OSCURO,
    spaceBefore=10 * mm,
    spaceAfter=4 * mm,
)

estilo_heading3 = ParagraphStyle(
    'Heading3',
    parent=estilos['Heading3'],
    fontName='Helvetica-Bold',
    fontSize=13,
    textColor=COLOR_GRIS_TEXTO,
    spaceBefore=8 * mm,
    spaceAfter=3 * mm,
)

estilo_codigo = ParagraphStyle(
    'Code',
    parent=estilos['Code'],
    fontName='Courier',
    fontSize=8,
    leading=10,
    backColor=COLOR_GRIS_CLARO,
    borderColor=HexColor("#cfd8e3"),
    borderWidth=0.5,
    borderPadding=6,
    leftIndent=5 * mm,
    rightIndent=5 * mm,
)

estilo_pie = ParagraphStyle(
    'Pie',
    fontName='Helvetica',
    fontSize=7,
    textColor=HexColor("#9ca3af"),
    alignment=TA_CENTER,
)

estilo_indice_link = ParagraphStyle(
    'IndiceLink',
    parent=estilo_normal,
    textColor=COLOR_AZUL,
    underline=True,
)

estilo_bullet = ParagraphStyle(
    'Bullet',
    parent=estilo_normal,
    bulletIndent=10 * mm,
    leftIndent=20 * mm,
    spaceBefore=1 * mm,
    spaceAfter=1 * mm,
)

estilo_ancla = ParagraphStyle('Ancla', fontSize=0, leading=0)


# ==================== FUNCIONES AUXILIARES ====================

def _imagen(nombre_archivo, ancho=None, alto=None):
    ruta = os.path.join(RUTA_IMAGENES, nombre_archivo)
    if os.path.exists(ruta):
        if ancho and alto:
            return Image(ruta, width=ancho, height=alto)
        elif ancho:
            return Image(ruta, width=ancho, height=ancho * 0.5625)
        else:
            return Image(ruta, width=150 * mm, height=100 * mm)
    else:
        return Paragraph(f"<i>[Imagen pendiente: {nombre_archivo}]</i>", estilo_normal)


def _tabla(datos, anchos=None, encabezado=True):
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_AZUL if encabezado else (1, 1, 1)),
        ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1) if encabezado else (0, 0, 0)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cfd8e3")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#ffffff"), COLOR_GRIS_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ])
    t = Table(datos, colWidths=anchos)
    t.setStyle(estilo_tabla)
    return t


def _lista(items):
    return ListFlowable(
        [ListItem(Paragraph(item, estilo_bullet)) for item in items],
        bulletType='bullet',
        start='•',
        bulletFontName='Helvetica',
        bulletFontSize=10,
        bulletOffsetY=-1,
    )


def _codigo(texto):
    return Paragraph(texto.replace('\n', '<br/>').replace(' ', '&nbsp;'), estilo_codigo)


def _ancla(nombre):
    return Paragraph(f'<a name="{nombre}"/>', estilo_ancla)


# ==================== PLANTILLA DE PÁGINA ====================

class PlantillaPagina:
    def __init__(self, parent_doc, tipo_manual, modulo, logo_path):
        self.tipo_manual = tipo_manual
        self.modulo = modulo
        self.logo_path = logo_path

    def beforeDrawPage(self, canv, doc):
        canv.saveState()
        if os.path.exists(self.logo_path):
            try:
                logo_w = 120 * mm
                logo_h = 120 * mm
                x_centro = (ANCHO - logo_w) / 2
                y_centro = (ALTO - logo_h) / 2
                canv.setFillAlpha(0.07)
                canv.drawImage(self.logo_path, x_centro, y_centro, width=logo_w, height=logo_h, mask='auto')
                canv.setFillAlpha(1.0)
            except Exception:
                pass
        canv.setFont('Helvetica-Bold', 8)
        canv.setFillColor(COLOR_AZUL)
        canv.drawString(MARGEN_IZQ, ALTO - 12 * mm, f"VAH - Manual {self.tipo_manual} - {self.modulo}")
        canv.setStrokeColor(COLOR_AZUL)
        canv.setLineWidth(1)
        canv.line(MARGEN_IZQ, ALTO - 14 * mm, ANCHO - MARGEN_DER, ALTO - 14 * mm)
        canv.setFont('Helvetica', 7)
        canv.setFillColor(HexColor("#9ca3af"))
        n_pagina = canv.getPageNumber()
        canv.drawCentredString(ANCHO / 2, 12 * mm, f"Página {n_pagina}")
        canv.drawString(MARGEN_IZQ, 12 * mm, f"Versión {VERSION}")
        canv.drawRightString(ANCHO - MARGEN_DER, 12 * mm, FECHA_GENERACION)
        canv.setStrokeColor(HexColor("#cfd8e3"))
        canv.setLineWidth(0.5)
        canv.line(MARGEN_IZQ, 18 * mm, ANCHO - MARGEN_DER, 18 * mm)
        canv.restoreState()


# ==================== DOCUMENTO PRINCIPAL ====================

class DocManual:
    def __init__(self, filename, tipo_manual, modulo, logo_path):
        self.filename = filename
        self.tipo_manual = tipo_manual
        self.modulo = modulo
        self.logo_path = logo_path

    def build(self, story):
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.platypus.doctemplate import PageTemplate
        from reportlab.platypus.frames import Frame

        doc = SimpleDocTemplate(
            self.filename,
            pagesize=TAMANO_PAGINA,
            title=f"VAH Manual {self.tipo_manual} - {self.modulo}",
            author="VAH ERP",
            subject=f"Manual {self.tipo_manual} del módulo {self.modulo}",
        )

        frame = Frame(MARGEN_IZQ, MARGEN_INF, ANCHO - MARGEN_IZQ - MARGEN_DER, ALTO - MARGEN_SUP - MARGEN_INF,
                      id='normal')

        def _beforeDraw(canv, _):
            plantilla = PlantillaPagina(doc, self.tipo_manual, self.modulo, self.logo_path)
            plantilla.beforeDrawPage(canv, doc)

        doc.build(story, onFirstPage=_beforeDraw, onLaterPages=_beforeDraw)


# ==================== CONTENIDO ====================

def generar_manual_tecnico():
    os.makedirs(RUTA_PDF, exist_ok=True)
    ruta_salida = os.path.join(RUTA_PDF, f"VAH_Manual_Tecnico_{MODULO}.pdf")
    doc = DocManual(ruta_salida, TIPO_MANUAL, MODULO, RUTA_LOGO)
    historia = []

    # PORTADA
    historia.append(Spacer(1, 40 * mm))
    if os.path.exists(RUTA_LOGO):
        historia.append(Image(RUTA_LOGO, width=60 * mm, height=60 * mm))
        historia.append(Spacer(1, 10 * mm))
    historia.append(Paragraph(f"Manual {TIPO_MANUAL}<br/>Módulo {MODULO}",
                              ParagraphStyle('TituloPortada', parent=estilos['Title'], fontSize=26,
                                             textColor=COLOR_AZUL, alignment=TA_CENTER)))
    historia.append(Spacer(1, 8 * mm))
    historia.append(Paragraph(f"Versión {VERSION} | {FECHA_GENERACION}",
                              ParagraphStyle('InfoPortada', parent=estilo_normal, fontSize=12,
                                             textColor=COLOR_GRIS_TEXTO, alignment=TA_CENTER)))
    historia.append(Spacer(1, 10 * mm))
    historia.append(
        Paragraph("Documentación técnica para desarrolladores y administradores del sistema.", estilo_normal))
    historia.append(PageBreak())

    # ÍNDICE
    historia.append(Paragraph("Índice de Contenido", estilo_heading1))
    historia.append(Spacer(1, 5 * mm))

    secciones = [
        ("1.", "Arquitectura del Sistema", "arquitectura"),
        ("2.", "Estructura de Archivos", "estructura"),
        ("3.", "Base de Datos", "basedatos"),
        ("  3.1", "Esquema de la Tabla", "bd-esquema"),
        ("  3.2", "Procedimientos SQL", "bd-sql"),
        ("4.", "Dependencias", "dependencias"),
        ("5.", "Módulos y Clases Principales", "modulos"),
        ("6.", "Flujo de Datos", "flujo"),
        ("7.", "Manejo de Errores", "errores"),
        ("8.", "Logging y Depuración", "logging"),
        ("9.", "Configuración", "configuracion"),
    ]

    datos_indice = [["#", "Sección"]]
    for num, titulo, ancla in secciones:
        datos_indice.append([num, Paragraph(f'<a href="#{ancla}" color="#1f6feb">{titulo}</a>', estilo_indice_link)])
    historia.append(_tabla(datos_indice, anchos=[15 * mm, 141 * mm]))
    historia.append(PageBreak())

    # 1. ARQUITECTURA
    historia.append(_ancla("arquitectura"))
    historia.append(Paragraph("1. Arquitectura del Sistema", estilo_heading1))
    historia.append(Paragraph("El Módulo de Clientes sigue una arquitectura de tres capas:", estilo_normal))
    datos_arq = [["Capa", "Tecnología", "Responsabilidad"],
                 ["Presentación", "PyQt6", "Interfaz gráfica, validación de entrada"],
                 ["Lógica de Negocio", "Python 3.12", "ClienteService, validaciones"],
                 ["Acceso a Datos", "pyodbc + SQL Server", "ClienteRepository, CRUD"],
                 ["Almacenamiento", "SQL Server", "Tabla Clientes"]]
    historia.append(_tabla(datos_arq, anchos=[35 * mm, 35 * mm, 86 * mm]))
    historia.append(PageBreak())

    # 2. ESTRUCTURA DE ARCHIVOS
    historia.append(_ancla("estructura"))
    historia.append(Paragraph("2. Estructura de Archivos", estilo_heading1))
    datos_files = [["Archivo", "Descripción"],
                   ["pantalla_clientes.py", "UI principal, modos de operación"],
                   ["cliente_repository.py", "CRUD, consultas SQL, agrupación"],
                   ["cliente_service.py", "Lógica de negocio"],
                   ["cliente.py", "Modelo Cliente (dataclass)"],
                   ["db.py", "Conexión a SQL Server"]]
    historia.append(_tabla(datos_files, anchos=[60 * mm, 96 * mm]))
    historia.append(PageBreak())

    # 3. BASE DE DATOS
    historia.append(_ancla("basedatos"))
    historia.append(Paragraph("3. Base de Datos", estilo_heading1))
    historia.append(_ancla("bd-esquema"))
    historia.append(Paragraph("3.1 Esquema de la Tabla", estilo_heading2))
    datos_esq = [["Columna", "Tipo", "Descripción"],
                 ["id", "INT", "PK, IDENTITY"],
                 ["nombre", "NVARCHAR(200)", "NOT NULL"],
                 ["Email", "NVARCHAR(200)", "Correo electrónico"],
                 ["telefono", "NVARCHAR(50)", "Teléfono"],
                 ["rfc", "NVARCHAR(20)", "RFC formateado"]]
    historia.append(_tabla(datos_esq, anchos=[40 * mm, 40 * mm, 76 * mm]))

    historia.append(_ancla("bd-sql"))
    historia.append(Paragraph("3.2 Procedimientos SQL", estilo_heading2))
    historia.append(_codigo(
        "INSERT INTO Clientes (nombre, Email, telefono, rfc)\n"
        "VALUES (?, ?, ?, ?);\n\n"
        "UPDATE Clientes SET nombre=?, Email=?, telefono=?, rfc=? WHERE id=?;\n\n"
        "DELETE FROM Clientes WHERE id=?;"
    ))
    historia.append(PageBreak())

    # 4. DEPENDENCIAS
    historia.append(_ancla("dependencias"))
    historia.append(Paragraph("4. Dependencias", estilo_heading1))
    datos_deps = [["Librería", "Versión", "Uso"],
                  ["PyQt6", "6.5+", "Interfaz gráfica"],
                  ["pyodbc", "4.0+", "Conexión ODBC"],
                  ["Python", "3.10+", "Lenguaje base"]]
    historia.append(_tabla(datos_deps, anchos=[40 * mm, 30 * mm, 86 * mm]))
    historia.append(_codigo("pip install PyQt6 pyodbc"))
    historia.append(PageBreak())

    # 5. MÓDULOS PRINCIPALES
    historia.append(_ancla("modulos"))
    historia.append(Paragraph("5. Módulos y Clases Principales", estilo_heading1))
    historia.append(Paragraph("<b>pantalla_clientes.py</b>", estilo_heading2))
    historia.append(
        _lista(["_modo_inicio()", "_modo_editar()", "_modo_eliminar()", "_modo_pantalla()", "_guardar_click()"]))
    historia.append(Paragraph("<b>cliente_repository.py</b>", estilo_heading2))
    historia.append(_lista(["get_all()", "buscar_por_nombre()", "insert()", "update()", "delete()"]))
    historia.append(PageBreak())

    # 6. FLUJO DE DATOS
    historia.append(_ancla("flujo"))
    historia.append(Paragraph("6. Flujo de Datos", estilo_heading1))
    historia.append(_lista([
        "1. Usuario completa formulario",
        "2. UI valida campos obligatorios",
        "3. UI llama a ClienteService.guardar()",
        "4. Service llama a ClienteRepository.insert()",
        "5. Repository ejecuta INSERT en SQL Server",
        "6. UI muestra mensaje de éxito"
    ]))
    historia.append(PageBreak())

    # 7. MANEJO DE ERRORES
    historia.append(_ancla("errores"))
    historia.append(Paragraph("7. Manejo de Errores", estilo_heading1))
    datos_err = [["Nivel", "Mecanismo"],
                 ["Validación UI", "Comprobaciones en _guardar_click()"],
                 ["Repositorio", "try/except en operaciones SQL"],
                 ["Logs", "Archivo rotativo clientes.log"]]
    historia.append(_tabla(datos_err, anchos=[50 * mm, 106 * mm]))
    historia.append(PageBreak())

    # 8. LOGGING
    historia.append(_ancla("logging"))
    historia.append(Paragraph("8. Logging y Depuración", estilo_heading1))
    historia.append(_codigo("D:\\vah\\clientes\\clientes.log"))
    historia.append(_lista(["Tamaño máximo: 1 MB", "Backup: 3 archivos", "Encoding: UTF-8"]))
    historia.append(PageBreak())

    # 9. CONFIGURACIÓN
    historia.append(_ancla("configuracion"))
    historia.append(Paragraph("9. Configuración", estilo_heading1))
    historia.append(_codigo(
        "server = r'DESKTOP-AE60PIU\\SQLEXPRESS'\n"
        "database = 'clientes'\n"
        "driver = '{ODBC Driver 17 for SQL Server}'"
    ))
    historia.append(Spacer(1, 10 * mm))

    # CIERRE
    historia.append(Paragraph("— Fin del Manual Técnico —",
                              ParagraphStyle('Cierre', parent=estilo_normal, alignment=TA_CENTER, textColor=COLOR_AZUL,
                                             fontSize=12)))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph(f"Documento generado el {FECHA_GENERACION} | Versión {VERSION}", estilo_pie))
    historia.append(Paragraph("VAH ERP © Todos los derechos reservados", estilo_pie))

    doc.build(historia)
    print(f"Manual Tecnico de {MODULO} generado: {ruta_salida}")


if __name__ == "__main__":
    generar_manual_tecnico()
