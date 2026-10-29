# D:\vah\manuales\scripts_generadores\generar_manual_operativo_vidrio.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Operativo - Módulo Materiales Vidrio VAH
===========================================================
Genera un PDF profesional con:
  - Índice clickeable (navegación interna)
  - Buscador de palabras (PDF searchable)
  - Marca de agua: logo VAH al 7%
  - Numeración: "Página X"
  - Encabezado: "VAH - Manual Operativo - Vidrio"
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
MODULO = "Vidrio"
TIPO_MANUAL = "Operativo"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "vidrio")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf", "operativo")
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

estilo_ancla = ParagraphStyle(
    'Ancla',
    fontSize=0,
    leading=0,
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
    return Paragraph(f'<a name="{nombre}"/>', estilo_ancla)


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
    """Genera el PDF del manual operativo de Vidrio."""

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
        "Sistema ERP para gestión de materiales de vidrio.<br/>"
        "Administración de precios unitarios, importación desde Excel y listas de materiales.",
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
        ("  5.1", "Registrar un Nuevo Material", "op-nuevo"),
        ("  5.2", "Editar un Registro Existente", "op-editar"),
        ("  5.3", "Eliminar un Registro", "op-eliminar"),
        ("  5.4", "Buscar Materiales", "op-buscar"),
        ("  5.5", "Importar desde Excel", "op-importar"),
        ("  5.6", "Imprimir Listado", "op-imprimir"),
        ("6.", "Atajos de Teclado", "atajos"),
        ("7.", "Solución de Problemas", "problemas"),
        ("8.", "Preguntas Frecuentes", "faq"),
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
        "El <b>Módulo de Materiales Vidrio</b> del ERP VAH es una herramienta diseñada para la gestión "
        "de los materiales de vidrio utilizados en la fabricación de ventanas, puertas y canceles. "
        "Permite registrar, consultar, actualizar y eliminar materiales, así como importar listas "
        "desde archivos Excel.",
        estilo_normal
    ))
    historia.append(Paragraph(
        "Este manual operativo está dirigido a los <b>usuarios finales</b> del sistema: personal "
        "de ventas, cotizadores y cualquier usuario que requiera gestionar la lista de tipos de vidrio.",
        estilo_normal
    ))
    historia.append(Paragraph("<b>Funcionalidades principales:</b>", estilo_normal))
    historia.append(_lista([
        "Registro de nuevos materiales con Clave, Descripción y Precio unitario.",
        "Edición de datos de materiales existentes (incluyendo la clave).",
        "Eliminación directa de registros (desde los inputs, sin depender de la tabla).",
        "Búsqueda dinámica por clave (prefijo).",
        "Importación masiva desde archivos Excel.",
        "Selección en tabla con doble clic o un solo clic (ambos cargan los datos).",
        "Impresión de listados a Pantalla, PDF o Impresora.",
    ]))
    historia.append(PageBreak())

    # ============== 2. REQUISITOS DEL SISTEMA ==============
    historia.append(_ancla("requisitos"))
    historia.append(Paragraph("2. Requisitos del Sistema", estilo_heading1))
    historia.append(Paragraph(
        "Para utilizar el Módulo de Vidrio, su equipo debe cumplir con los siguientes requisitos:",
        estilo_normal
    ))

    datos_req = [
        ["Componente", "Requisito"],
        ["Sistema Operativo", "Windows 10 o superior (64 bits)"],
        ["Python", "3.10 o superior"],
        ["Base de Datos", "SQL Server (Express o Standard) - BD 'vidrio'"],
        ["ODBC Driver", "ODBC Driver 17 o 18 for SQL Server"],
        ["Memoria RAM", "Mínimo 4 GB (8 GB recomendado)"],
        ["Resolución", "1366 x 768 o superior"],
        ["Librerías Python", "PyQt6, pyodbc, openpyxl, pandas, numpy, reportlab, win32print"],
    ]
    historia.append(_tabla(datos_req, anchos=[70 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_nota(
        "Si el módulo no abre o muestra errores de conexión, verifique que SQL Server "
        "esté en ejecución y que la base de datos 'vidrio' exista."
    ))
    historia.append(PageBreak())

    # ============== 3. INICIO DEL MÓDULO ==============
    historia.append(_ancla("inicio"))
    historia.append(Paragraph("3. Inicio del Módulo", estilo_heading1))
    historia.append(Paragraph(
        "El Módulo de Vidrio se inicia desde el menú principal del ERP VAH. "
        "Al abrirlo, se muestra la pantalla principal en <b>estado inicial</b> (limpio), "
        "lista para realizar una nueva captura o buscar registros existentes.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("pantalla_principal.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "La pantalla siempre inicia en blanco. Para ver los registros existentes, "
        "active el modo <b>Editar</b> o use la barra de búsqueda directamente."
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
        "<b>Campos de Datos:</b> Captura de Clave, Descripción y Precio unitario.",
        "<b>Tabla de Registros:</b> Visualización de los materiales existentes.",
        "<b>Barra de Búsqueda:</b> Filtro dinámico por clave.",
    ]))

    # 4.1 Barra de Botones
    historia.append(_ancla("interfaz-botones"))
    historia.append(Paragraph("4.1 Barra de Botones", estilo_heading2))
    historia.append(_imagen("botones_principales.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_botones = [
        ["Botón", "Función", "Atajo"],
        ["Guardar", "Registra un nuevo material o guarda cambios", "Ctrl+S"],
        ["Editar", "Activa el modo edición para modificar registros", "—"],
        ["Eliminar", "Elimina el registro actual (cargado en inputs)", "Delete"],
        ["Limpiar", "Limpia todos los campos y regresa al estado inicial", "—"],
        ["Refresh", "Refresca la conexión a la base de datos (ping)", "F5"],
        ["Imprimir", "Abre diálogo para imprimir (Pantalla/PDF/Impresora)", "Ctrl+P"],
        ["Salir", "Cierra el módulo", "Esc"],
    ]
    historia.append(_tabla(datos_botones, anchos=[35 * mm, 106 * mm, 25 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "El botón <b>Refresh</b> solo prueba la conexión a la base de datos. "
        "Para ver registros, use <b>Editar</b> o la barra de búsqueda."
    ))

    # 4.2 Campos de Datos
    historia.append(_ancla("interfaz-campos"))
    historia.append(Paragraph("4.2 Campos de Datos", estilo_heading2))
    historia.append(_imagen("campos_datos.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_campos = [
        ["Campo", "Descripción", "Validación"],
        ["Clave", "Identificador único del tipo de vidrio", "Obligatorio, mayúsculas, máx. 20 caracteres"],
        ["Descripción", "Nombre del vidrio (ej. Vidrio Claro 6mm)", "Obligatorio, máx. 100 caracteres"],
        ["Precio", "Precio unitario por metro cuadrado", "Obligatorio, mayor a 0, 2 decimales"],
    ]
    historia.append(_tabla(datos_campos, anchos=[40 * mm, 80 * mm, 46 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "La tecla <b>Enter</b> avanza al siguiente campo (como Tab). "
        "El campo <b>Clave</b> se convierte automáticamente a MAYÚSCULAS.",
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
        "<b>Para cargar un registro en los campos:</b> puede hacer <b>doble clic</b> o simplemente "
        "<b>un solo clic</b> en la fila (ambos métodos funcionan).",
        estilo_normal
    ))

    # 4.4 Barra de Búsqueda
    historia.append(_ancla("interfaz-busqueda"))
    historia.append(Paragraph("4.4 Barra de Búsqueda", estilo_heading2))
    historia.append(_imagen("barra_busqueda.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "La barra de búsqueda se activa al entrar en modo <b>Editar</b>. "
        "La búsqueda es por <b>prefijo de clave</b>: al escribir, la tabla se filtra automáticamente "
        "mostrando solo los registros cuya <b>clave comience</b> con el texto ingresado.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== 5. OPERACIONES BÁSICAS ==============
    historia.append(_ancla("operaciones"))
    historia.append(Paragraph("5. Operaciones Básicas", estilo_heading1))

    # 5.1 Registrar Nuevo
    historia.append(_ancla("op-nuevo"))
    historia.append(Paragraph("5.1 Registrar un Nuevo Material", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Verifique que la pantalla esté en estado inicial (campos vacíos). Si no, presione <b>Limpiar</b>.",
        "Capture la <b>Clave</b> del tipo de vidrio (ej. V-CLARO-6). Se convierte automáticamente a mayúsculas.",
        "Capture la <b>Descripción</b> (ej. Vidrio Claro 6mm).",
        "Capture el <b>Precio</b> unitario por metro cuadrado (ej. 450.00).",
        "Presione <b>Enter</b> para avanzar entre campos (clave → descripción → precio → Guardar).",
        "Haga clic en <b>Guardar</b> (Ctrl+S).",
        "Aparecerá el mensaje: <b>'Información guardada con éxito'</b>.",
        "La pantalla se limpia automáticamente."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("mensaje_guardar.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Si la clave ya existe al salir del campo (con Enter/Tab), el sistema preguntará: "
        "'Clave existente. ¿Deseas editarla?' Si responde NO, la pantalla se limpia."
    ))

    # 5.2 Editar un Registro Existente
    historia.append(_ancla("op-editar"))
    historia.append(Paragraph("5.2 Editar un Registro Existente", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Editar</b>.",
        "La barra de búsqueda se activa. Escriba el prefijo de la clave del material a editar.",
        "La tabla se filtrará mostrando las coincidencias.",
        "<b>Seleccione la fila</b> con un clic o doble clic (los datos se cargan automáticamente).",
        "Modifique la <b>Clave</b>, <b>Descripción</b> y/o <b>Precio</b> necesarios.",
        "Presione <b>Guardar</b> (Ctrl+S).",
        "Aparecerá el mensaje: <b>'Registro actualizado con éxito'</b>.",
        "La pantalla se limpia automáticamente."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("mensaje_editar.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Si cambia la clave y la nueva ya existe, el sistema mostrará un mensaje de duplicidad."
    ))

    # 5.3 Eliminar un Registro
    historia.append(_ancla("op-eliminar"))
    historia.append(Paragraph("5.3 Eliminar un Registro", estilo_heading2))
    historia.append(Paragraph(
        "El módulo permite eliminar directamente el registro cargado en los inputs, "
        "sin necesidad de seleccionarlo en la tabla.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Cargue el material a eliminar en los campos (buscando y seleccionando en la tabla, o escribiendo la clave).",
        "Haga clic en el botón <b>Eliminar</b> (o presione Delete).",
        "El sistema pedirá confirmación: '¿Seguro que deseas eliminar la clave X?'.",
        "Seleccione <b>Sí</b> para eliminar o <b>No</b> para cancelar.",
        "Si confirma, aparecerá el mensaje: <b>'Registro eliminado.'</b>",
        "La pantalla se limpia automáticamente."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("modo_eliminar.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "<b>⚠️ Precaución:</b> La eliminación es <b>permanente</b>. "
        "No hay papelera de reciclaje ni opción de deshacer.",
        ParagraphStyle('Advertencia', parent=estilo_normal, textColor=HexColor("#dc2626"))
    ))

    # 5.4 Buscar Materiales
    historia.append(_ancla("op-buscar"))
    historia.append(Paragraph("5.4 Buscar Materiales", estilo_heading2))
    historia.append(Paragraph(
        "La búsqueda está disponible en modo <b>Editar</b>. "
        "La búsqueda es por <b>prefijo de clave</b>. "
        "Ejemplo: escribir 'V-CLARO' mostrará 'V-CLARO-6', 'V-CLARO-8', 'V-CLARO-10', etc. "
        "La búsqueda es <b>dinámica</b> y los resultados se muestran en orden descendente.",
        estilo_normal
    ))

    # 5.5 Importar desde Excel
    historia.append(_ancla("op-importar"))
    historia.append(Paragraph("5.5 Importar desde Excel", estilo_heading2))
    historia.append(Paragraph(
        "El módulo permite importar listas de materiales desde archivos Excel. "
        "El sistema detecta automáticamente los encabezados y asigna los valores.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Formato esperado del Excel:</b>", estilo_normal))
    historia.append(_lista([
        "Columnas: <b>Clave</b> (obligatorio), <b>Descripción</b> (obligatorio), <b>Precio</b> (obligatorio).",
        "El encabezado puede estar en cualquier fila (el sistema lo detecta).",
        "Los nombres pueden tener variaciones (Descripción/Descripcion, Precio/Precio unitario/PU).",
        "Los precios aceptan coma o punto decimal, y símbolo $.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Ejecute el script de importación: <b>python -m materiales.vidrio.cargar_excel_vidrio</b>",
        "Seleccione el archivo Excel cuando se solicite.",
        "El sistema procesa el archivo, muestra las columnas detectadas y el resultado.",
        "Los registros rechazados se guardan en D:\\vah\\logs\\rechazados_vidrio_*.csv",
        "Si un material ya existe, se actualiza SOLO si el nuevo precio es MAYOR (conserva el máximo).",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("importar_dialog.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "La importación es por línea de comandos, no desde la interfaz gráfica. "
        "Está diseñada para uso administrativo al cargar listas de precios de proveedores."
    ))

    # 5.6 Imprimir Listado
    historia.append(_ancla("op-imprimir"))
    historia.append(Paragraph("5.6 Imprimir Listado", estilo_heading2))
    historia.append(Paragraph(
        "El módulo ofrece tres opciones de impresión:",
        estilo_normal
    ))
    historia.append(_lista([
        "<b>Pantalla:</b> Muestra todos los registros en la tabla (equivale a ver el listado completo).",
        "<b>PDF:</b> Genera un archivo PDF con todos los materiales ordenados por clave.",
        "<b>Impresora:</b> Envía el PDF directamente a la impresora predeterminada.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Imprimir</b> (Ctrl+P).",
        "Seleccione la opción deseada (Pantalla, PDF o Impresora).",
        "Si elige <b>PDF</b>, seleccione la ruta y nombre del archivo.",
        "Si elige <b>Impresora</b>, el PDF se envía automáticamente a la impresora predeterminada.",
        "El listado incluye: Clave, Descripción y Precio unitario.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("impresion_dialog.png", ancho=100 * mm))
    historia.append(PageBreak())

    # ============== 6. ATAJOS DE TECLADO ==============
    historia.append(_ancla("atajos"))
    historia.append(Paragraph("6. Atajos de Teclado", estilo_heading1))
    historia.append(Paragraph(
        "El módulo incluye los siguientes atajos de teclado para agilizar las operaciones:",
        estilo_normal
    ))

    datos_atajos = [
        ["Atajo", "Acción"],
        ["Ctrl+S", "Guardar material"],
        ["Ctrl+F", "Activar búsqueda (si está en modo Editar)"],
        ["Ctrl+P", "Abrir diálogo de impresión"],
        ["Delete", "Eliminar registro actual (cargado en inputs)"],
        ["F5", "Refresh (probar conexión a BD)"],
        ["Esc", "Salir del módulo"],
        ["Enter", "Avanzar al siguiente campo (como Tab)"],
        ["Shift+Tab", "Retroceder al campo anterior"],
        ["Clic en fila", "Cargar registro automáticamente (doble clic o un solo clic)"],
    ]
    historia.append(_tabla(datos_atajos, anchos=[50 * mm, 106 * mm]))
    historia.append(PageBreak())

    # ============== 7. SOLUCIÓN DE PROBLEMAS ==============
    historia.append(_ancla("problemas"))
    historia.append(Paragraph("7. Solución de Problemas", estilo_heading1))

    problemas = [
        (
            "El módulo no abre o muestra error de importación",
            [
                "Verifique que Python 3.10+ esté instalado.",
                "Ejecute: <font face='Courier'>pip install PyQt6 pyodbc openpyxl pandas numpy reportlab</font>",
                "Revise que SQL Server esté en ejecución.",
                "Verifique que la base de datos 'vidrio' exista.",
            ]
        ),
        (
            "Error de conexión a la base de datos",
            [
                "Verifique que el servicio SQL Server esté iniciado.",
                "Confirme que la base de datos 'vidrio' exista.",
                "Revise que ODBC Driver 17/18 esté instalado.",
                "Verifique la cadena de conexión en D:\\vah\\materiales\\vidrio\\db_manager.py",
            ]
        ),
        (
            "No se puede guardar un material",
            [
                "Verifique que la <b>Clave</b> y <b>Descripción</b> no estén vacías.",
                "Verifique que el <b>Precio</b> sea mayor a 0.",
                "Si la clave ya existe, use una clave diferente o edite el registro existente.",
            ]
        ),
        (
            "No aparecen materiales en la tabla al buscar",
            [
                "Asegúrese de estar en modo <b>Editar</b>.",
                "Escriba el <b>prefijo</b> de la clave (ej. 'V-CLARO' para claves que empiecen con V-CLARO).",
                "Use la opción <b>Imprimir</b> → Pantalla para ver todos los registros.",
            ]
        ),
        (
            "La importación de Excel no funciona",
            [
                "Verifique que el formato del archivo tenga las columnas Clave, Descripción y Precio.",
                "Revise los logs en D:\\vah\\logs\\rechazados_vidrio_*.csv",
                "Asegúrese de tener instaladas las librerías: openpyxl, pandas, numpy.",
            ]
        ),
        (
            "La impresión a impresora no funciona",
            [
                "Verifique que haya una impresora predeterminada configurada en Windows.",
                "Asegúrese de tener instalado pywin32: <font face='Courier'>pip install pywin32</font>",
                "Si la impresora es PDF, la impresión fallará. Conecte una impresora física.",
            ]
        ),
    ]

    for problema, soluciones in problemas:
        historia.append(Paragraph(f"<b>Problema:</b> {problema}", estilo_heading3))
        historia.append(Paragraph("<b>Soluciones:</b>", estilo_normal))
        historia.append(_lista(soluciones))
        historia.append(Spacer(1, 3 * mm))

    historia.append(PageBreak())

    # ============== 8. PREGUNTAS FRECUENTES ==============
    historia.append(_ancla("faq"))
    historia.append(Paragraph("8. Preguntas Frecuentes", estilo_heading1))

    faqs = [
        (
            "¿Puedo modificar la CLAVE de un material existente?",
            "Sí. En modo edición, el campo Clave está habilitado y puede modificarse. "
            "Si la nueva clave ya existe, el sistema mostrará un mensaje de duplicidad."
        ),
        (
            "¿Cómo elimino un material sin tener que seleccionarlo en la tabla?",
            "El módulo permite eliminar directamente el registro cargado en los inputs. "
            "Simplemente escriba o seleccione la clave en los campos y presione <b>Eliminar</b> (Delete)."
        ),
        (
            "¿Cómo selecciono un registro para editar?",
            "Puede hacer <b>doble clic</b> en la fila de la tabla o simplemente <b>un solo clic</b> "
            "(ambos métodos cargan los datos en los campos superiores)."
        ),
        (
            "¿Qué significa el botón 'Refresh'?",
            "Solo prueba la conexión a la base de datos (realiza una consulta de prueba). "
            "NO llena la tabla. Para ver datos, use <b>Editar</b> o la barra de búsqueda."
        ),
        (
            "¿Cómo exporto la lista de materiales a Excel?",
            "Actualmente, la exportación directa a Excel no está disponible. "
            "Puede imprimir a PDF o usar la opción Pantalla para ver el listado completo."
        ),
        (
            "¿La importación desde Excel actualiza o solo inserta nuevos?",
            "Ambos. Si un material ya existe, se actualiza SOLO si el nuevo precio es MAYOR "
            "(política de 'máximo valor'). Si el nuevo valor es menor, se conserva el existente."
        ),
    ]

    for pregunta, respuesta in faqs:
        historia.append(Paragraph(f"<b>P:</b> {pregunta}", estilo_heading3))
        historia.append(Paragraph(f"<b>R:</b> {respuesta}", estilo_normal))
        historia.append(Spacer(1, 3 * mm))

    historia.append(Spacer(1, 10 * mm))

    # ============== CIERRE ==============
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
    print(f"✅ Manual Operativo de {MODULO} generado: {ruta_salida}")
    return ruta_salida


if __name__ == "__main__":
    generar_manual()