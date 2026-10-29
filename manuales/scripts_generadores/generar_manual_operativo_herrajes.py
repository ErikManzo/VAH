# D:\vah\manuales\scripts_generadores\generar_manual_operativo_herrajes.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Operativo - Módulo Herrajes VAH
====================================================
Genera un PDF profesional con:
  - Índice clickeable (navegación interna)
  - Buscador de palabras (PDF searchable)
  - Marca de agua: logo VAH al 7%
  - Numeración: "Página X de Y"
  - Encabezado: "VAH - Manual Operativo - Herrajes"
  - Color corporativo: #1f6feb
"""

import os
import datetime
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, ListFlowable, ListItem, KeepTogether,
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.pdfbase import pdfmetrics

# ==================== CONFIGURACIÓN ====================
MODULO = "Herrajes"
TIPO_MANUAL = "Operativo"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "herrajes")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf")
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

estilo_titulo_principal = ParagraphStyle(
    'TituloPrincipal',
    parent=estilos['Title'],
    fontName='Helvetica-Bold',
    fontSize=26,
    textColor=COLOR_AZUL,
    spaceAfter=6 * mm,
    alignment=TA_LEFT,
)

estilo_heading1 = ParagraphStyle(
    'Heading1Personalizado',
    parent=estilos['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=20,
    textColor=COLOR_AZUL,
    spaceBefore=12 * mm,
    spaceAfter=6 * mm,
)

estilo_heading2 = ParagraphStyle(
    'Heading2Personalizado',
    parent=estilos['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=COLOR_AZUL_OSCURO,
    spaceBefore=10 * mm,
    spaceAfter=4 * mm,
)

estilo_heading3 = ParagraphStyle(
    'Heading3Personalizado',
    parent=estilos['Heading3'],
    fontName='Helvetica-Bold',
    fontSize=13,
    textColor=COLOR_GRIS_TEXTO,
    spaceBefore=8 * mm,
    spaceAfter=3 * mm,
)

estilo_normal = ParagraphStyle(
    'NormalPersonalizado',
    parent=estilos['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=COLOR_GRIS_TEXTO,
    alignment=TA_JUSTIFY,
    spaceAfter=4 * mm,
)

estilo_bullet = ParagraphStyle(
    'BulletPersonalizado',
    parent=estilo_normal,
    bulletIndent=10 * mm,
    leftIndent=20 * mm,
    spaceBefore=1 * mm,
    spaceAfter=1 * mm,
)

estilo_codigo = ParagraphStyle(
    'Codigo',
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

estilo_nota = ParagraphStyle(
    'Nota',
    parent=estilo_normal,
    fontName='Helvetica-Oblique',
    fontSize=9,
    textColor=HexColor("#6b7280"),
    leftIndent=5 * mm,
    rightIndent=5 * mm,
    borderColor=HexColor("#cfd8e3"),
    borderWidth=0.5,
    borderPadding=8,
    backColor=COLOR_GRIS_CLARO,
)

estilo_pie = ParagraphStyle(
    'PiePagina',
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


# ==================== FUNCIONES AUXILIARES ====================

def _imagen(nombre_archivo, ancho=None, alto=None):
    """Carga una imagen desde la carpeta de imágenes del módulo."""
    ruta = os.path.join(RUTA_IMAGENES, nombre_archivo)
    if os.path.exists(ruta):
        if ancho and alto:
            return Image(ruta, width=ancho, height=alto)
        elif ancho:
            return Image(ruta, width=ancho, height=ancho * 0.5625)
        else:
            return Image(ruta, width=150 * mm, height=100 * mm)
    else:
        return Paragraph(
            f"<i>[Imagen pendiente: {nombre_archivo}]</i>",
            estilo_nota
        )


def _tabla(datos, anchos=None, encabezado=True):
    """Crea una tabla formateada."""
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_AZUL if encabezado else white),
        ('TEXTCOLOR', (0, 0), (-1, 0), white if encabezado else black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cfd8e3")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COLOR_GRIS_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ])
    t = Table(datos, colWidths=anchos)
    t.setStyle(estilo_tabla)
    return t


def _lista(items):
    """Crea una lista con viñetas."""
    return ListFlowable(
        [ListItem(Paragraph(item, estilo_bullet)) for item in items],
        bulletType='bullet',
        start='•',
        bulletFontName='Helvetica',
        bulletFontSize=10,
        bulletOffsetY=-1,
    )


def _nota(texto):
    """Crea un párrafo de nota."""
    return Paragraph(f'💡 <b>Nota:</b> {texto}', estilo_nota)


def _codigo(texto):
    """Crea un bloque de código."""
    return Paragraph(texto.replace('\n', '<br/>').replace(' ', '&nbsp;'), estilo_codigo)


def _ancla(nombre):
    """Crea un marcador de destino para enlaces internos."""
    return Paragraph(f'<a name="{nombre}"/>', ParagraphStyle('Ancla', fontSize=0, leading=0))


# ==================== PLANTILLA DE PÁGINA ====================

class PlantillaPagina(PageTemplate):
    """Plantilla personalizada con marca de agua, encabezado y pie de página."""

    def __init__(self, parent_doc, tipo_manual, modulo, logo_path):
        frame = Frame(
            MARGEN_IZQ, MARGEN_INF,
            ANCHO - MARGEN_IZQ - MARGEN_DER,
            ALTO - MARGEN_SUP - MARGEN_INF,
            id='normal'
        )
        super().__init__(id='Principal', frames=[frame])
        self.tipo_manual = tipo_manual
        self.modulo = modulo
        self.logo_path = logo_path

    def beforeDrawPage(self, canv, doc):
        """Dibuja marca de agua, encabezado y pie."""
        canv.saveState()

        # Marca de agua (logo al 7% de opacidad)
        if os.path.exists(self.logo_path):
            try:
                logo_w = 120 * mm
                logo_h = 120 * mm
                x_centro = (ANCHO - logo_w) / 2
                y_centro = (ALTO - logo_h) / 2

                canv.setFillAlpha(0.07)
                canv.drawImage(
                    self.logo_path,
                    x_centro, y_centro,
                    width=logo_w,
                    height=logo_h,
                    mask='auto'
                )
                canv.setFillAlpha(1.0)
            except Exception:
                pass

        # Encabezado
        canv.setFont('Helvetica-Bold', 8)
        canv.setFillColor(COLOR_AZUL)
        canv.drawString(
            MARGEN_IZQ, ALTO - 12 * mm,
            f"VAH - Manual {self.tipo_manual} - {self.modulo}"
        )

        # Línea bajo encabezado
        canv.setStrokeColor(COLOR_AZUL)
        canv.setLineWidth(1)
        canv.line(
            MARGEN_IZQ, ALTO - 14 * mm,
                        ANCHO - MARGEN_DER, ALTO - 14 * mm
        )

        # Pie de página
        canv.setFont('Helvetica', 7)
        canv.setFillColor(HexColor("#9ca3af"))
        n_pagina = canv.getPageNumber()
        canv.drawCentredString(ANCHO / 2, 12 * mm, f"Página {n_pagina}")
        canv.drawString(MARGEN_IZQ, 12 * mm, f"Versión {VERSION}")
        canv.drawRightString(ANCHO - MARGEN_DER, 12 * mm, FECHA_GENERACION)

        # Línea sobre pie
        canv.setStrokeColor(HexColor("#cfd8e3"))
        canv.setLineWidth(0.5)
        canv.line(MARGEN_IZQ, 18 * mm, ANCHO - MARGEN_DER, 18 * mm)

        canv.restoreState()


# ==================== DOCUMENTO PRINCIPAL ====================

class DocManual(BaseDocTemplate):
    """Documento base para manuales con soporte de bookmarks."""

    def __init__(self, filename, tipo_manual, modulo, logo_path):
        super().__init__(
            filename,
            pagesize=TAMANO_PAGINA,
            title=f"VAH Manual {tipo_manual} - {modulo}",
            author="VAH ERP",
            subject=f"Manual {tipo_manual} del módulo {modulo}",
        )
        self.addPageTemplates([
            PlantillaPagina(self, tipo_manual, modulo, logo_path)
        ])


# ==================== CONTENIDO DEL MANUAL ====================

def generar_manual():
    """Genera el PDF del manual operativo."""

    os.makedirs(RUTA_PDF, exist_ok=True)
    ruta_salida = os.path.join(RUTA_PDF, f"VAH_Manual_Operativo_{MODULO}.pdf")

    doc = DocManual(ruta_salida, TIPO_MANUAL, MODULO, RUTA_LOGO)

    historia = []

    # ============== PORTADA ==============
    historia.append(Spacer(1, 40 * mm))

    if os.path.exists(RUTA_LOGO):
        historia.append(Image(RUTA_LOGO, width=60 * mm, height=60 * mm))
        historia.append(Spacer(1, 10 * mm))

    historia.append(Paragraph(
        f"Manual {TIPO_MANUAL}<br/>Módulo {MODULO}",
        estilo_titulo_principal
    ))
    historia.append(Spacer(1, 8 * mm))
    historia.append(Paragraph(
        f"Versión {VERSION} | {FECHA_GENERACION}",
        ParagraphStyle('InfoPortada', parent=estilo_normal, fontSize=12, textColor=COLOR_GRIS_TEXTO)
    ))
    historia.append(Spacer(1, 10 * mm))
    historia.append(Paragraph(
        "Sistema ERP para gestión de materiales de herrajes.<br/>"
        "Importación, administración y generación de reportes.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== ÍNDICE ==============
    historia.append(Paragraph("Índice de Contenido", estilo_heading1))
    historia.append(Spacer(1, 5 * mm))

    secciones_indice = [
        ("1.", "Introducción", "intro"),
        ("2.", "Requisitos del Sistema", "requisitos"),
        ("3.", "Inicio del Módulo", "inicio"),
        ("4.", "Interfaz Principal", "interfaz"),
        ("  4.1", "Barra de Botones", "interfaz-botones"),
        ("  4.2", "Campos de Datos", "interfaz-campos"),
        ("  4.3", "Tabla de Registros", "interfaz-tabla"),
        ("  4.4", "Barra de Búsqueda", "interfaz-busqueda"),
        ("5.", "Operaciones Básicas", "operaciones"),
        ("  5.1", "Registrar un Nuevo Herraje", "op-nuevo"),
        ("  5.2", "Editar un Registro Existente", "op-editar"),
        ("  5.3", "Eliminar un Registro", "op-eliminar"),
        ("6.", "Importación de Datos", "importacion"),
        ("  6.1", "Archivos Soportados", "imp-archivos"),
        ("  6.2", "Configuración de Importación", "imp-configuracion"),
        ("  6.3", "Ventana de Cantidad Divisora", "imp-divisora"),
        ("  6.4", "Resultados de Importación", "imp-resultados"),
        ("7.", "Generación de Reportes", "reportes"),
        ("  7.1", "Impresión en Pantalla", "rep-pantalla"),
        ("  7.2", "Exportar a PDF", "rep-pdf"),
        ("  7.3", "Enviar a Impresora", "rep-impresora"),
        ("8.", "Solución de Problemas", "problemas"),
        ("9.", "Atajos de Teclado", "atajos"),
    ]

    datos_indice = [["#", "Sección"]]
    for num, titulo, ancla in secciones_indice:
        datos_indice.append([
            num,
            Paragraph(f'<a href="#{ancla}" color="#1f6feb">{titulo}</a>', estilo_indice_link),
        ])

    historia.append(_tabla(datos_indice, anchos=[15 * mm, 141 * mm]))
    historia.append(PageBreak())

    # ============== 1. INTRODUCCIÓN ==============
    historia.append(_ancla("intro"))
    historia.append(Paragraph("1. Introducción", estilo_heading1))
    historia.append(Paragraph(
        "El <b>Módulo de Herrajes</b> del ERP VAH es una herramienta diseñada para la gestión integral "
        "del catálogo de materiales de herrajes utilizados en la fabricación de aluminio y vidrio. "
        "Permite registrar, consultar, actualizar y eliminar productos, así como importar masivamente "
        "datos desde archivos Excel de proveedores como <b>Herralum</b> y <b>Profilo</b>.",
        estilo_normal
    ))
    historia.append(Paragraph(
        "Este manual operativo está dirigido a los <b>usuarios finales</b> del sistema: capturistas, "
        "almacenistas, compradores y personal administrativo que requiere mantener actualizado el "
        "catálogo de precios de herrajes.",
        estilo_normal
    ))
    historia.append(Paragraph("<b>Funcionalidades principales:</b>", estilo_normal))
    historia.append(_lista([
        "Captura manual de herrajes (clave, descripción, precio).",
        "Edición y eliminación de registros existentes.",
        "Búsqueda dinámica por clave.",
        "Importación masiva desde archivos Excel (.xlsx/.xls) y CSV.",
        "Detección automática de proveedor (Herralum/Profilo).",
        "Cálculo automático de precio unitario según unidad de medida.",
        "Corrección manual de registros con precio inválido mediante cantidad divisora.",
        "Generación de reportes PDF e impresión.",
    ]))
    historia.append(PageBreak())

    # ============== 2. REQUISITOS DEL SISTEMA ==============
    historia.append(_ancla("requisitos"))
    historia.append(Paragraph("2. Requisitos del Sistema", estilo_heading1))
    historia.append(Paragraph(
        "Para utilizar el Módulo de Herrajes, su equipo debe cumplir con los siguientes requisitos:",
        estilo_normal
    ))

    datos_req = [
        ["Componente", "Requisito"],
        ["Sistema Operativo", "Windows 10 o superior (64 bits)"],
        ["Python", "3.10 o superior"],
        ["Base de Datos", "SQL Server (Express o Standard)"],
        ["ODBC Driver", "ODBC Driver 18 for SQL Server"],
        ["Memoria RAM", "Mínimo 4 GB (8 GB recomendado)"],
        ["Resolución", "1366 x 768 o superior"],
        ["Librerías Python", "PyQt6, pandas, pyodbc, openpyxl, reportlab"],
    ]
    historia.append(_tabla(datos_req, anchos=[70 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_nota(
        "Si el módulo no abre o muestra errores de conexión, verifique que SQL Server "
        "esté en ejecución y que el ODBC Driver 18 esté instalado correctamente."
    ))
    historia.append(PageBreak())

    # ============== 3. INICIO DEL MÓDULO ==============
    historia.append(_ancla("inicio"))
    historia.append(Paragraph("3. Inicio del Módulo", estilo_heading1))
    historia.append(Paragraph(
        "El Módulo de Herrajes se inicia desde el menú principal del ERP VAH. "
        "Al abrirlo, se muestra la pantalla principal en <b>estado inicial</b> (limpio), "
        "lista para realizar una nueva captura o buscar registros existentes.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("pantalla_principal.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "La pantalla siempre inicia en blanco. Para ver los registros existentes, "
        "active el modo <b>Editar</b> o <b>Eliminar</b> y use la barra de búsqueda."
    ))
    historia.append(PageBreak())

    # ============== 4. INTERFAZ PRINCIPAL ==============
    historia.append(_ancla("interfaz"))
    historia.append(Paragraph("4. Interfaz Principal", estilo_heading1))
    historia.append(Paragraph(
        "La interfaz del módulo se divide en cuatro zonas principales:",
        estilo_normal
    ))
    historia.append(_lista([
        "<b>Barra de Botones:</b> Acceso a todas las operaciones (Guardar, Editar, Eliminar, etc.).",
        "<b>Campos de Datos:</b> Captura de información del herraje (Clave, Descripción, Precio).",
        "<b>Tabla de Registros:</b> Visualización de los registros existentes.",
        "<b>Barra de Búsqueda:</b> Filtro dinámico por clave.",
    ]))

    # 4.1 Barra de Botones
    historia.append(_ancla("interfaz-botones"))
    historia.append(Paragraph("4.1 Barra de Botones", estilo_heading2))
    historia.append(_imagen("botones_principales.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_botones = [
        ["Botón", "Función", "Atajo"],
        ["Guardar", "Registra un nuevo herraje o guarda cambios", "Ctrl+S"],
        ["Editar", "Activa el modo edición para modificar registros", "—"],
        ["Eliminar", "Activa el modo eliminación (doble clic para confirmar)", "Supr"],
        ["Limpiar", "Limpia todos los campos y regresa al estado inicial", "—"],
        ["Refresh", "Limpia la pantalla (no recarga datos)", "F5"],
        ["Imprimir", "Abre opciones de impresión/reporte", "Ctrl+P"],
        ["Salir", "Cierra el módulo", "Esc"],
        ["Importar", "Importa datos desde Excel o CSV", "—"],
    ]
    historia.append(_tabla(datos_botones, anchos=[30 * mm, 96 * mm, 30 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Los botones se deshabilitan durante la importación para evitar conflictos. "
        "Al finalizar, se reactivan automáticamente."
    ))

    # 4.2 Campos de Datos
    historia.append(_ancla("interfaz-campos"))
    historia.append(Paragraph("4.2 Campos de Datos", estilo_heading2))
    historia.append(_imagen("campos_datos.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_campos = [
        ["Campo", "Descripción", "Validación"],
        ["Clave", "Código único del producto (máx. 20 caracteres)", "Obligatorio, sin espacios, alfanumérico"],
        ["Descripción", "Nombre o descripción del producto (máx. 100 caracteres)", "Obligatorio"],
        ["Precio", "Precio unitario en pesos (2 decimales)", "Obligatorio, mayor a 0.00"],
    ]
    historia.append(_tabla(datos_campos, anchos=[30 * mm, 70 * mm, 56 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "El campo <b>Clave</b> se convierte automáticamente a mayúsculas al teclear. "
        "La tecla <b>Enter</b> avanza al siguiente campo (como Tab). "
        "El campo con el foco se resalta con un <b>borde azul</b>.",
        estilo_normal
    ))

    # 4.3 Tabla de Registros
    historia.append(_ancla("interfaz-tabla"))
    historia.append(Paragraph("4.3 Tabla de Registros", estilo_heading2))
    historia.append(_imagen("tabla_registros.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "La tabla muestra tres columnas: <b>CLAVE</b>, <b>DESCRIPCIÓN</b> y <b>PRECIO</b>. "
        "Los registros aparecen ordenados alfabéticamente por clave. "
        "Las filas alternan colores para facilitar la lectura. "
        "Al hacer <b>doble clic</b> sobre una fila, los datos se cargan en los campos para su edición.",
        estilo_normal
    ))

    # 4.4 Barra de Búsqueda
    historia.append(_ancla("interfaz-busqueda"))
    historia.append(Paragraph("4.4 Barra de Búsqueda", estilo_heading2))
    historia.append(_imagen("barra_busqueda.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "La barra de búsqueda se activa al entrar en modo <b>Editar</b> o <b>Eliminar</b>. "
        "La búsqueda es <b>dinámica</b>: al escribir, la tabla se filtra automáticamente "
        "mostrando solo los registros cuya clave <b>comienza</b> con el texto ingresado.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== 5. OPERACIONES BÁSICAS ==============
    historia.append(_ancla("operaciones"))
    historia.append(Paragraph("5. Operaciones Básicas", estilo_heading1))

    # 5.1 Registrar Nuevo
    historia.append(_ancla("op-nuevo"))
    historia.append(Paragraph("5.1 Registrar un Nuevo Herraje", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Verifique que la pantalla esté en estado inicial (campos vacíos). Si no, presione <b>Limpiar</b>.",
        "Capture la <b>Clave</b> del producto (ej. 100100000).",
        "Presione <b>Enter</b> para pasar al campo Descripción.",
        "Capture la <b>Descripción</b> completa del producto.",
        "Presione <b>Enter</b> para pasar al campo Precio.",
        "Capture el <b>Precio</b> unitario (ej. 125.50).",
        "Presione <b>Enter</b> nuevamente o haga clic en <b>Guardar</b> (Ctrl+S).",
        "Aparecerá un mensaje de confirmación: 'Información guardada con éxito'.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("mensaje_guardar.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Si la clave ya existe, el sistema mostrará un mensaje de error. "
        "Use el modo Editar para modificar un registro existente."
    ))

    # 5.2 Editar Registro
    historia.append(_ancla("op-editar"))
    historia.append(Paragraph("5.2 Editar un Registro Existente", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Editar</b>.",
        "La barra de búsqueda se activa. Escriba la clave del producto a modificar.",
        "La tabla se filtrará mostrando las coincidencias.",
        "Haga <b>doble clic</b> sobre el registro deseado, o selecciónelo con un clic.",
        "Los datos se cargarán en los campos superiores.",
        "Modifique los campos necesarios (Descripción y/o Precio).",
        "Presione <b>Guardar</b> (Ctrl+S).",
        "Aparecerá el mensaje: 'Registro actualizado con éxito'.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("mensaje_editar.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Si cambia la clave por una que ya existe, el sistema mostrará un error de duplicidad."
    ))

    # 5.3 Eliminar Registro
    historia.append(_ancla("op-eliminar"))
    historia.append(Paragraph("5.3 Eliminar un Registro", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Eliminar</b>.",
        "Se activa el modo eliminación. La tabla se llena con todos los registros.",
        "Use la barra de búsqueda para localizar el registro a eliminar.",
        "Seleccione la fila deseada con un clic.",
        "Presione nuevamente el botón <b>Eliminar</b> (o tecla Supr).",
        "El sistema pedirá confirmación: '¿Seguro que deseas eliminar [clave]?'.",
        "Seleccione <b>Sí</b> para eliminar o <b>No</b> para cancelar.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("modo_eliminar.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "<b>⚠️ Precaución:</b> La eliminación es <b>permanente</b>. "
        "No hay papelera de reciclaje ni opción de deshacer. "
        "Verifique siempre antes de confirmar.",
        ParagraphStyle('Advertencia', parent=estilo_normal, textColor=HexColor("#dc2626"))
    ))
    historia.append(PageBreak())

    # ============== 6. IMPORTACIÓN DE DATOS ==============
    historia.append(_ancla("importacion"))
    historia.append(Paragraph("6. Importación de Datos", estilo_heading1))
    historia.append(Paragraph(
        "La función de importación permite cargar masivamente productos desde archivos externos. "
        "Es la herramienta principal para actualizar precios desde las listas de proveedores.",
        estilo_normal
    ))

    # 6.1 Archivos Soportados
    historia.append(_ancla("imp-archivos"))
    historia.append(Paragraph("6.1 Archivos Soportados", estilo_heading2))
    datos_archivos = [
        ["Formato", "Extensión", "Proveedores"],
        ["Excel", ".xlsx, .xls", "Herralum, Profilo (detección automática)"],
        ["CSV", ".csv", "Genérico (columnas: clave, descripcion, precio)"],
    ]
    historia.append(_tabla(datos_archivos, anchos=[40 * mm, 40 * mm, 76 * mm]))

    # 6.2 Configuración de Importación
    historia.append(_ancla("imp-configuracion"))
    historia.append(Paragraph("6.2 Configuración de Importación", estilo_heading2))
    historia.append(Paragraph(
        "Al seleccionar un archivo Excel, aparece el <b>diálogo de configuración</b> "
        "que permite seleccionar las hojas a procesar y mapear las columnas.",
        estilo_normal
    ))
    historia.append(_imagen("mapeo_columnas.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Opciones del diálogo:</b>", estilo_normal))
    historia.append(_lista([
        "<b>Hojas a procesar:</b> Seleccione una o varias hojas del archivo Excel.",
        "<b>Mapeo de columnas:</b> Asocie cada campo del sistema (Clave, Descripción, UM, Precio) "
        "con la columna correspondiente del archivo. El sistema intenta detectarlas automáticamente.",
        "<b>Previsualización:</b> Muestra las primeras filas de datos según el mapeo configurado.",
        "El mapeo se <b>guarda automáticamente</b> por nombre de archivo para futuras importaciones.",
    ]))

    # 6.3 Ventana de Cantidad Divisora
    historia.append(_ancla("imp-divisora"))
    historia.append(Paragraph("6.3 Ventana de Cantidad Divisora", estilo_heading2))
    historia.append(Paragraph(
        "Durante la importación, algunos registros pueden ser rechazados por tener un <b>precio inválido o cero</b>. "
        "En lugar de descartarlos automáticamente, el sistema muestra una <b>ventana auxiliar</b> "
        "donde el usuario puede ingresar manualmente la <b>cantidad divisora</b> para calcular el precio unitario.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("ventana_divisora.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Fórmula aplicada:</b>", estilo_normal))
    historia.append(_codigo("Precio Unitario = Precio Original / Cantidad Divisora"))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Comportamiento de la ventana:</b>", estilo_normal))
    historia.append(_lista([
        "Muestra todos los registros rechazados por precio inválido (clave, descripción, unidad, precio original).",
        "La columna <b>Cantidad Divisora</b> es editable. Ingrese un número mayor a 0.",
        "<b>Aceptar y calcular precios:</b> Calcula el precio unitario y actualiza la base de datos.",
        "<b>Cancelar (dejar sin precio):</b> Los registros quedan con precio $0.00.",
        "Si deja el campo vacío en un registro específico, ese registro queda sin precio.",
    ]))

    # 6.4 Resultados de Importación
    historia.append(_ancla("imp-resultados"))
    historia.append(Paragraph("6.4 Resultados de Importación", estilo_heading2))
    historia.append(Paragraph(
        "Al finalizar la importación, se muestra un <b>resumen detallado</b> con los totales por hoja procesada:",
        estilo_normal
    ))
    historia.append(_imagen("mensaje_final_importacion.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_resumen = [
        ["Concepto", "Descripción"],
        ["Insertados", "Registros nuevos que no existían en la base de datos"],
        ["Actualizados", "Registros existentes cuyo precio se actualizó (se conserva el mayor)"],
        ["Rechazados", "Registros que no pudieron procesarse por errores"],
        ["Duplicados colapsados", "Registros duplicados en el archivo que se unificaron"],
    ]
    historia.append(_tabla(datos_resumen, anchos=[45 * mm, 111 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "Si hay registros <b>RL</b> (rollos) sin factor de conversión detectable, "
        "se listan al final del mensaje para su corrección manual:",
        estilo_normal
    ))
    historia.append(_imagen("rl_pendientes.png", ancho=140 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Los archivos de log con los registros rechazados se guardan en: "
        "<font face='Courier'>D:\\vah\\logs\\rechazados_*.csv</font>"
    ))
    historia.append(PageBreak())

    # ============== 7. GENERACIÓN DE REPORTES ==============
    historia.append(_ancla("reportes"))
    historia.append(Paragraph("7. Generación de Reportes", estilo_heading1))
    historia.append(Paragraph(
        "El botón <b>Imprimir</b> (Ctrl+P) abre un menú con tres opciones de salida:",
        estilo_normal
    ))
    historia.append(_imagen("menu_imprimir.png", ancho=80 * mm))

    # 7.1 Pantalla
    historia.append(_ancla("rep-pantalla"))
    historia.append(Paragraph("7.1 Impresión en Pantalla", estilo_heading2))
    historia.append(Paragraph(
        "Muestra todos los registros en la tabla de la interfaz, ordenados alfabéticamente por clave. "
        "Útil para una consulta rápida sin generar archivos.",
        estilo_normal
    ))

    # 7.2 PDF
    historia.append(_ancla("rep-pdf"))
    historia.append(Paragraph("7.2 Exportar a PDF", estilo_heading2))
    historia.append(Paragraph(
        "Genera un archivo PDF profesional con los siguientes elementos:",
        estilo_normal
    ))
    historia.append(_lista([
        "Encabezado con el título 'Materiales herrajes'.",
        "Columnas: CLAVE, DESCRIPCIÓN, PRECIO.",
        "Encabezados de columna en todas las páginas.",
        "Pie de página con numeración 'Página X'.",
        "Formato tamaño Carta, orientación vertical.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("pdf_generado.png", ancho=120 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "El sistema solicita la ubicación donde guardar el archivo PDF. "
        "Se sugiere el nombre 'Materiales herrajes.pdf'.",
        estilo_normal
    ))

    # 7.3 Impresora
    historia.append(_ancla("rep-impresora"))
    historia.append(Paragraph("7.3 Enviar a Impresora", estilo_heading2))
    historia.append(Paragraph(
        "Envía el documento directamente a la impresora predeterminada de Windows. "
        "Si no hay impresora configurada o la predeterminada es 'PDF', "
        "el sistema mostrará un mensaje: 'No hay Impresora conectada'.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== 8. SOLUCIÓN DE PROBLEMAS ==============
    historia.append(_ancla("problemas"))
    historia.append(Paragraph("8. Solución de Problemas", estilo_heading1))

    problemas = [
        (
            "El módulo no abre",
            [
                "Verifique que Python 3.10+ esté instalado.",
                "Ejecute: <font face='Courier'>pip install PyQt6 pandas pyodbc openpyxl reportlab</font>",
                "Revise que SQL Server esté en ejecución.",
            ]
        ),
        (
            "Error de conexión a la base de datos",
            [
                "Verifique que el servicio SQL Server esté iniciado.",
                "Confirme que existe la base de datos 'herrajes'.",
                "Revise que ODBC Driver 18 esté instalado.",
            ]
        ),
        (
            "No se detectan las columnas del Excel",
            [
                "Verifique que los encabezados estén en las primeras 20 filas.",
                "Seleccione manualmente las columnas en el diálogo de configuración.",
                "Asegúrese de que el archivo no esté protegido con contraseña.",
            ]
        ),
        (
            "Muchos registros rechazados en importación",
            [
                "Revise el archivo de log en D:\\vah\\logs\\",
                "Verifique que los precios no contengan caracteres extraños.",
                "Para RL, asegúrese de que la descripción contenga el metraje (ej. 1600MT).",
            ]
        ),
        (
            "La ventana divisora no aparece",
            [
                "Solo aparece para rechazados con motivo 'precio_invalido_o_cero'.",
                "Verifique que el archivo ventana_divisora.py exista en la carpeta del módulo.",
            ]
        ),
    ]

    for problema, soluciones in problemas:
        historia.append(Paragraph(f"<b>Problema:</b> {problema}", estilo_heading3))
        historia.append(Paragraph("<b>Soluciones:</b>", estilo_normal))
        historia.append(_lista(soluciones))
        historia.append(Spacer(1, 3 * mm))

    historia.append(PageBreak())

    # ============== 9. ATAJOS DE TECLADO ==============
    historia.append(_ancla("atajos"))
    historia.append(Paragraph("9. Atajos de Teclado", estilo_heading1))
    historia.append(Paragraph(
        "El módulo incluye los siguientes atajos de teclado para agilizar las operaciones:",
        estilo_normal
    ))

    datos_atajos = [
        ["Atajo", "Acción"],
        ["Ctrl+S", "Guardar registro"],
        ["Ctrl+F", "Activar búsqueda"],
        ["Supr", "Modo eliminar"],
        ["Ctrl+P", "Imprimir / Generar reporte"],
        ["F5", "Refresh (limpiar pantalla)"],
        ["Esc", "Salir del módulo"],
        ["Enter", "Avanzar al siguiente campo (como Tab)"],
        ["Shift+Tab", "Retroceder al campo anterior"],
        ["Doble clic (tabla)", "Cargar registro para edición"],
    ]
    historia.append(_tabla(datos_atajos, anchos=[50 * mm, 106 * mm]))
    historia.append(Spacer(1, 10 * mm))

    # Cierre
    historia.append(Paragraph(
        "— Fin del Manual Operativo —",
        ParagraphStyle('Cierre', parent=estilo_normal, alignment=TA_CENTER,
                       textColor=COLOR_AZUL, fontSize=12)
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph(
        f"Documento generado el {FECHA_GENERACION} | Versión {VERSION}",
        estilo_pie
    ))
    historia.append(Paragraph(
        "VAH ERP © Todos los derechos reservados",
        estilo_pie
    ))

    # ==================== CONSTRUIR PDF ====================
    doc.build(historia)
    print(f"✅ Manual Operativo generado: {ruta_salida}")
    return ruta_salida


if __name__ == "__main__":
    generar_manual()