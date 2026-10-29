# D:\vah\manuales\scripts_generadores\generar_manual_operativo_paquete_herrajes.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Operativo - Módulo Paquete Herrajes VAH
===========================================================
Genera un PDF profesional con:
  - Índice clickeable (navegación interna)
  - Buscador de palabras (PDF searchable)
  - Marca de agua: logo VAH al 7%
  - Numeración: "Página X"
  - Encabezado: "VAH - Manual Operativo - Paquete Herrajes"
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
MODULO = "Paquete Herrajes"
TIPO_MANUAL = "Operativo"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "paquete_herrajes")
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
    """Genera el PDF del manual operativo de Paquete Herrajes."""

    os.makedirs(RUTA_PDF, exist_ok=True)
    ruta_salida = os.path.join(RUTA_PDF, f"VAH_Manual_Operativo_{MODULO.replace(' ', '_')}.pdf")

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
        "Sistema ERP para gestión de paquetes de herrajes.<br/>"
        "Agrupación de herrajes en conjuntos predefinidos para cotización rápida.",
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
        ("  4.2", "Campos de Datos del Paquete", "interfaz-campos-paquete"),
        ("  4.3", "Campos de Agregar Herrajes", "interfaz-campos-items"),
        ("  4.4", "Tabla de Herrajes", "interfaz-tabla"),
        ("5.", "Operaciones Básicas", "operaciones"),
        ("  5.1", "Crear un Nuevo Paquete", "op-nuevo"),
        ("  5.2", "Agregar Herrajes al Paquete", "op-agregar"),
        ("  5.3", "Editar un Paquete Existente", "op-editar"),
        ("  5.4", "Eliminar un Paquete", "op-eliminar"),
        ("  5.5", "Eliminar un Herraje del Paquete", "op-quitar"),
        ("  5.6", "Imprimir Listado de Paquetes", "op-imprimir"),
        ("  5.7", "Consultar Herrajes", "op-herraje"),
        ("6.", "Búsqueda y Autocompletado", "busqueda"),
        ("7.", "Atajos de Teclado", "atajos"),
        ("8.", "Solución de Problemas", "problemas"),
        ("9.", "Preguntas Frecuentes", "faq"),
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
        "El <b>Módulo de Paquetes de Herrajes</b> del ERP VAH es una herramienta diseñada para agrupar "
        "herrajes en conjuntos predefinidos. Esto permite, en el módulo de Presupuestos, agregar "
        "paquetes completos con un solo clic en lugar de seleccionar cada herraje individualmente.",
        estilo_normal
    ))
    historia.append(Paragraph(
        "Este manual operativo está dirigido a los <b>usuarios finales</b> del sistema: personal "
        "de ventas, cotizadores y cualquier usuario que requiera crear y gestionar paquetes de herrajes.",
        estilo_normal
    ))
    historia.append(Paragraph("<b>Funcionalidades principales:</b>", estilo_normal))
    historia.append(_lista([
        "Creación de paquetes de herrajes con clave y descripción.",
        "Agregar herrajes a un paquete con cantidades específicas.",
        "Edición de paquetes existentes (modificar clave, descripción o componentes).",
        "Eliminación de paquetes completos o de herrajes individuales.",
        "Búsqueda de herrajes por clave o descripción con autocompletado.",
        "Impresión de listados: General (solo cabeceras) o Desglosado (con componentes).",
        "Acceso directo al módulo de Herrajes para gestionar la base de datos.",
        "Integración con Presupuestos (partida_paquetes).",
    ]))
    historia.append(PageBreak())

    # ============== 2. REQUISITOS DEL SISTEMA ==============
    historia.append(_ancla("requisitos"))
    historia.append(Paragraph("2. Requisitos del Sistema", estilo_heading1))
    historia.append(Paragraph(
        "Para utilizar el Módulo de Paquete Herrajes, su equipo debe cumplir con los siguientes requisitos:",
        estilo_normal
    ))

    datos_req = [
        ["Componente", "Requisito"],
        ["Sistema Operativo", "Windows 10 o superior (64 bits)"],
        ["Python", "3.10 o superior"],
        ["Base de Datos", "SQL Server (Express o Standard) - BD 'herrajes'"],
        ["Tablas requeridas", "paquetes_herrajes, paquete_herraje_items, materiales_herraje"],
        ["ODBC Driver", "ODBC Driver 17 o 18 for SQL Server"],
        ["Memoria RAM", "Mínimo 4 GB (8 GB recomendado)"],
        ["Resolución", "1366 x 768 o superior"],
        ["Librerías Python", "PyQt6, pyodbc, reportlab, win32print"],
    ]
    historia.append(_tabla(datos_req, anchos=[70 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_nota(
        "Si el módulo no abre o muestra errores de conexión, verifique que SQL Server "
        "esté en ejecución y que la base de datos 'herrajes' exista."
    ))
    historia.append(PageBreak())

    # ============== 3. INICIO DEL MÓDULO ==============
    historia.append(_ancla("inicio"))
    historia.append(Paragraph("3. Inicio del Módulo", estilo_heading1))
    historia.append(Paragraph(
        "El Módulo de Paquete Herrajes se inicia desde el menú principal del ERP VAH "
        "o directamente desde el botón 'Paquete Herrajes' en la pantalla principal. "
        "Al abrirlo, se muestra la pantalla en <b>estado inicial</b> (limpio), "
        "lista para crear un nuevo paquete o buscar uno existente.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("pantalla_principal.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "La pantalla siempre inicia en blanco. Para ver los paquetes existentes, "
        "use el botón <b>Editar</b>."
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
        "<b>Barra de Botones:</b> Acceso a todas las operaciones.",
        "<b>Datos del Paquete:</b> Clave y descripción del paquete.",
        "<b>Agregar Herrajes:</b> Campos para buscar y agregar herrajes al paquete.",
        "<b>Tabla de Herrajes:</b> Listado de herrajes que componen el paquete actual.",
    ]))

    # 4.1 Barra de Botones
    historia.append(_ancla("interfaz-botones"))
    historia.append(Paragraph("4.1 Barra de Botones", estilo_heading2))
    historia.append(_imagen("botones_principales.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_botones = [
        ["Botón", "Función", "Atajo"],
        ["Guardar", "Guarda el paquete actual (nuevo o editado)", "Ctrl+S"],
        ["Agregar", "Agrega el herraje actual a la tabla", "Enter en Cantidad"],
        ["Editar", "Abre selector para cargar un paquete existente", "—"],
        ["Eliminar", "Elimina el paquete actual (pide clave)", "—"],
        ["Limpiar", "Limpia todos los campos y reinicia", "—"],
        ["Refresh", "Refresca la conexión a la base de datos", "F5"],
        ["Imprimir", "Abre diálogo para imprimir listado", "Ctrl+P"],
        ["Quitar item", "Elimina el herraje seleccionado de la tabla", "Delete/Supr"],
        ["Herraje", "Abre el módulo de gestión de herrajes", "—"],
        ["Salir", "Cierra el módulo", "Esc"],
    ]
    historia.append(_tabla(datos_botones, anchos=[35 * mm, 106 * mm, 25 * mm]))

    # 4.2 Datos del Paquete
    historia.append(_ancla("interfaz-campos-paquete"))
    historia.append(Paragraph("4.2 Campos de Datos del Paquete", estilo_heading2))
    historia.append(_imagen("campos_paquete.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_campos_paquete = [
        ["Campo", "Descripción", "Validación"],
        ["Clave", "Identificador único del paquete", "Obligatorio, mayúsculas, máx. 20 caracteres"],
        ["Descripción", "Nombre del paquete", "Obligatorio, máx. 100 caracteres"],
    ]
    historia.append(_tabla(datos_campos_paquete, anchos=[40 * mm, 80 * mm, 46 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "La tecla <b>Enter</b> avanza al siguiente campo (como Tab). "
        "El campo <b>Clave</b> se convierte automáticamente a MAYÚSCULAS.",
        estilo_normal
    ))

    # 4.3 Campos de Agregar Herrajes
    historia.append(_ancla("interfaz-campos-items"))
    historia.append(Paragraph("4.3 Campos de Agregar Herrajes", estilo_heading2))
    historia.append(_imagen("campos_herrajes.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_campos_items = [
        ["Campo", "Descripción", "Validación"],
        ["Clave Herraje", "Clave del herraje (búsqueda por prefijo)", "Autocompletado"],
        ["Descripción Herraje", "Descripción del herraje (búsqueda por texto)", "Autocompletado"],
        ["Cantidad", "Cantidad de piezas del herraje en el paquete", "Obligatorio, mayor a 0"],
    ]
    historia.append(_tabla(datos_campos_items, anchos=[40 * mm, 80 * mm, 46 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "Al escribir en los campos <b>Clave Herraje</b> o <b>Descripción Herraje</b>, "
        "aparece un popup con opciones coincidentes. Puede seleccionar una opción "
        "con el mouse o con las flechas del teclado + Enter.",
        estilo_normal
    ))

    # 4.4 Tabla de Herrajes
    historia.append(_ancla("interfaz-tabla"))
    historia.append(Paragraph("4.4 Tabla de Herrajes", estilo_heading2))
    historia.append(_imagen("tabla_items.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "La tabla muestra tres columnas: <b>CLAVE HERRAJE</b>, <b>DESCRIPCIÓN</b> y <b>CANTIDAD</b>. "
        "Los herrajes aparecen ordenados alfabéticamente por clave. "
        "Las filas alternan colores para facilitar la lectura. "
        "<b>Al seleccionar una fila</b> (con un clic), los datos se cargan automáticamente "
        "en los campos superiores para facilitar la edición de la cantidad.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "La selección de una fila activa el modo 'edición de ítem'. "
        "Al modificar la cantidad y presionar <b>Agregar</b>, se actualizará ese ítem "
        "en lugar de crear uno nuevo."
    ))
    historia.append(PageBreak())

    # ============== 5. OPERACIONES BÁSICAS ==============
    historia.append(_ancla("operaciones"))
    historia.append(Paragraph("5. Operaciones Básicas", estilo_heading1))

    # 5.1 Crear Nuevo Paquete
    historia.append(_ancla("op-nuevo"))
    historia.append(Paragraph("5.1 Crear un Nuevo Paquete", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Verifique que la pantalla esté en estado inicial (campos vacíos). Si no, presione <b>Limpiar</b>.",
        "Capture la <b>Clave</b> del paquete. Se convierte automáticamente a mayúsculas.",
        "Capture la <b>Descripción</b> del paquete.",
        "Agregue herrajes (ver sección 5.2).",
        "Haga clic en <b>Guardar</b> (Ctrl+S).",
        "Aparecerá el mensaje: <b>'Paquete guardado con éxito'</b>.",
        "La pantalla se limpia automáticamente."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("mensaje_guardar.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Si la clave ya existe al intentar guardar, el sistema preguntará: "
        "'Ya existe un paquete con la clave X. ¿Deseas sobrescribirlo?'."
    ))

    # 5.2 Agregar Herrajes
    historia.append(_ancla("op-agregar"))
    historia.append(Paragraph("5.2 Agregar Herrajes al Paquete", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "En el campo <b>Clave Herraje</b>, escriba el prefijo de la clave del herraje.",
        "Seleccione el herraje deseado del popup de autocompletado.",
        "Alternativamente, escriba en <b>Descripción Herraje</b> para buscar por nombre.",
        "Capture la <b>Cantidad</b> (valor predeterminado: 1).",
        "Presione <b>Agregar</b> o <b>Enter</b> en el campo Cantidad.",
        "El herraje aparecerá en la tabla inferior.",
        "Aparecerá el mensaje: '¿Quieres insertar otro herraje al paquete?'",
        "Seleccione <b>Sí</b> para continuar agregando o <b>No</b> para terminar."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("agregar_herraje.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Si intenta agregar un herraje que ya está en la tabla, la cantidad se <b>suma</b> "
        "al registro existente (no se duplica)."
    ))

    # 5.3 Editar Paquete Existente
    historia.append(_ancla("op-editar"))
    historia.append(Paragraph("5.3 Editar un Paquete Existente", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Editar</b>.",
        "Se abrirá el diálogo 'Seleccionar paquete' con la lista de paquetes.",
        "Seleccione el paquete deseado y haga clic en <b>Seleccionar</b> (o doble clic).",
        "El paquete se carga: clave, descripción y lista de herrajes.",
        "Modifique los datos necesarios: clave, descripción, agregue/elimine herrajes.",
        "Haga clic en <b>Guardar</b> (Ctrl+S).",
        "Aparecerá el mensaje: <b>'Paquete guardado con éxito'</b>.",
        "La pantalla se limpia automáticamente."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("selector_paquetes.png", ancho=100 * mm))

    # 5.4 Eliminar Paquete
    historia.append(_ancla("op-eliminar"))
    historia.append(Paragraph("5.4 Eliminar un Paquete", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Eliminar</b>.",
        "Se abrirá un diálogo solicitando la <b>Clave del paquete</b>.",
        "Ingrese la clave del paquete a eliminar.",
        "El sistema confirmará: '¿Seguro que deseas eliminar X?'.",
        "Seleccione <b>Sí</b> para eliminar o <b>No</b> para cancelar.",
        "Si confirma, aparecerá el mensaje: <b>'Paquete eliminado.'</b>.",
        "La pantalla se limpia automáticamente."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "<b>⚠️ Precaución:</b> La eliminación es <b>permanente</b> y elimina también "
        "todos los herrajes asociados al paquete (CASCADE en la BD).",
        ParagraphStyle('Advertencia', parent=estilo_normal, textColor=HexColor("#dc2626"))
    ))

    # 5.5 Eliminar Herraje del Paquete
    historia.append(_ancla("op-quitar"))
    historia.append(Paragraph("5.5 Eliminar un Herraje del Paquete", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "En la tabla de herrajes, <b>seleccione la fila</b> del herraje a eliminar.",
        "Haga clic en <b>Quitar item</b> o presione <b>Delete</b>.",
        "El sistema confirmará: '¿Eliminar el herraje X del paquete?'.",
        "Seleccione <b>Sí</b> para eliminar o <b>No</b> para cancelar.",
        "El herraje desaparecerá de la tabla.",
        "Recuerde <b>Guardar</b> el paquete para hacer permanente el cambio."
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Eliminar un herraje de la tabla NO guarda automáticamente el paquete. "
        "Debe presionar <b>Guardar</b> después de quitar items."
    ))

    # 5.6 Imprimir Listado
    historia.append(_ancla("op-imprimir"))
    historia.append(Paragraph("5.6 Imprimir Listado de Paquetes", estilo_heading2))
    historia.append(Paragraph(
        "El módulo ofrece dos tipos de reporte y tres destinos:",
        estilo_normal
    ))
    historia.append(_lista([
        "<b>General:</b> Muestra solo las cabeceras de los paquetes (clave y descripción).",
        "<b>Desglosado:</b> Muestra cada paquete con todos sus herrajes (clave, descripción, cantidad).",
        "<b>Pantalla:</b> Muestra el reporte en una ventana emergente.",
        "<b>PDF:</b> Genera un archivo PDF guardado en disco.",
        "<b>Impresora:</b> Envía el reporte directamente a la impresora predeterminada.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Imprimir</b> (Ctrl+P).",
        "Seleccione <b>Destino</b>: Pantalla, PDF o Impresora.",
        "Seleccione <b>Tipo</b>: General o Desglosado.",
        "Haga clic en <b>Aceptar</b>.",
        "Si eligió Pantalla, se abrirá una ventana con el reporte.",
        "Si eligió PDF, seleccione la ruta y nombre del archivo.",
        "Si eligió Impresora, el reporte se enviará automáticamente.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("impresion_dialog.png", ancho=100 * mm))

    # 5.7 Consultar Herrajes
    historia.append(_ancla("op-herraje"))
    historia.append(Paragraph("5.7 Consultar/Agregar Herrajes", estilo_heading2))
    historia.append(Paragraph(
        "El botón <b>Herraje</b> abre el módulo de gestión de herrajes en una ventana separada. "
        "Esto permite agregar nuevos herrajes a la base de datos sin cerrar el paquete actual.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("boton_herraje.png", ancho=80 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "El módulo de Herrajes se abre en una <b>nueva ventana</b>. "
        "Después de agregar nuevos herrajes, use el botón <b>Refresh</b> en Paquete Herrajes "
        "para actualizar el autocompletado."
    ))
    historia.append(PageBreak())

    # ============== 6. BÚSQUEDA Y AUTOCOMPLETADO ==============
    historia.append(_ancla("busqueda"))
    historia.append(Paragraph("6. Búsqueda y Autocompletado", estilo_heading1))
    historia.append(Paragraph(
        "El módulo de Paquete Herrajes incluye un sistema de autocompletado para facilitar "
        "la selección de herrajes:",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("autocompletado.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_busqueda = [
        ["Tipo de búsqueda", "Campo", "Comportamiento"],
        ["Por Clave", "Clave Herraje", "Coincidencia por PREFIJO (empieza con)"],
        ["Por Descripción", "Descripción Herraje", "Coincidencia por CONTIENE (en cualquier parte)"],
        ["Límite", "Ambos campos", "Máximo 100 resultados"],
    ]
    historia.append(_tabla(datos_busqueda, anchos=[50 * mm, 50 * mm, 56 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "Al seleccionar una opción del popup (con mouse o flechas + Enter), "
        "el otro campo se completa automáticamente.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== 7. ATAJOS DE TECLADO ==============
    historia.append(_ancla("atajos"))
    historia.append(Paragraph("7. Atajos de Teclado", estilo_heading1))
    historia.append(Paragraph(
        "El módulo incluye los siguientes atajos de teclado para agilizar las operaciones:",
        estilo_normal
    ))

    datos_atajos = [
        ["Atajo", "Acción"],
        ["Ctrl+S", "Guardar paquete"],
        ["Ctrl+P", "Abrir diálogo de impresión"],
        ["Delete", "Eliminar herraje seleccionado de la tabla"],
        ["F5", "Refresh (probar conexión a BD)"],
        ["Esc", "Salir del módulo"],
        ["Enter", "Agregar herraje (en campo Cantidad) / Aceptar en diálogos"],
        ["Enter", "Avanza al siguiente campo (fuera de Cantidad)"],
        ["Shift+Tab", "Retroceder al campo anterior"],
        ["Flechas ↑↓", "Navegar en popup de autocompletado"],
        ["Clic en fila", "Cargar herraje para editar cantidad"],
    ]
    historia.append(_tabla(datos_atajos, anchos=[50 * mm, 106 * mm]))
    historia.append(PageBreak())

    # ============== 8. SOLUCIÓN DE PROBLEMAS ==============
    historia.append(_ancla("problemas"))
    historia.append(Paragraph("8. Solución de Problemas", estilo_heading1))

    problemas = [
        (
            "El módulo no abre o muestra error de importación",
            [
                "Verifique que Python 3.10+ esté instalado.",
                "Ejecute: <font face='Courier'>pip install PyQt6 pyodbc reportlab</font>",
                "Revise que SQL Server esté en ejecución.",
                "Verifique que la base de datos 'herrajes' exista.",
            ]
        ),
        (
            "Error de conexión a la base de datos",
            [
                "Verifique que el servicio SQL Server esté iniciado.",
                "Confirme que la base de datos 'herrajes' exista.",
                "Revise que ODBC Driver 17/18 esté instalado.",
                "Verifique la cadena de conexión en el código.",
            ]
        ),
        (
            "No aparecen herrajes en el autocompletado",
            [
                "Verifique que la tabla 'materiales_herraje' tenga datos.",
                "Asegúrese de estar escribiendo en el campo correcto.",
                "Use el botón <b>Herraje</b> para abrir el módulo y agregar herrajes.",
                "Presione <b>Refresh</b> para reconectar a la BD.",
            ]
        ),
        (
            "No puedo guardar un paquete",
            [
                "Verifique que la <b>Clave</b> y <b>Descripción</b> del paquete no estén vacías.",
                "Verifique que haya al menos un herraje en la tabla.",
                "Si la clave ya existe, confirme que desea sobrescribir.",
            ]
        ),
        (
            "La impresión a impresora no funciona",
            [
                "Verifique que haya una impresora predeterminada configurada en Windows.",
                "Asegúrese de tener instalado pywin32: <font face='Courier'>pip install pywin32</font>",
                "El módulo filtra impresoras virtuales (PDF, XPS, OneNote, Fax).",
                "Conecte una impresora física.",
            ]
        ),
        (
            "El autocompletado no muestra resultados",
            [
                "Verifique que la tabla 'materiales_herraje' tenga datos.",
                "Intente con un prefijo más corto.",
                "Presione <b>Refresh</b> y vuelva a intentar.",
            ]
        ),
    ]

    for problema, soluciones in problemas:
        historia.append(Paragraph(f"<b>Problema:</b> {problema}", estilo_heading3))
        historia.append(Paragraph("<b>Soluciones:</b>", estilo_normal))
        historia.append(_lista(soluciones))
        historia.append(Spacer(1, 3 * mm))

    historia.append(PageBreak())

    # ============== 9. PREGUNTAS FRECUENTES ==============
    historia.append(_ancla("faq"))
    historia.append(Paragraph("9. Preguntas Frecuentes", estilo_heading1))

    faqs = [
        (
            "¿Puedo modificar la CLAVE de un paquete existente?",
            "Sí. En modo edición, el campo Clave está habilitado y puede modificarse. "
            "Si la nueva clave ya existe, el sistema preguntará si desea sobrescribir."
        ),
        (
            "¿Qué pasa si agrego un herraje que ya está en la tabla?",
            "La cantidad se <b>suma</b> al registro existente. No se crea un duplicado."
        ),
        (
            "¿Cómo elimino un herraje de un paquete sin eliminar el paquete completo?",
            "Seleccione la fila del herraje en la tabla y presione <b>Quitar item</b> o <b>Delete</b>. "
            "Luego presione <b>Guardar</b> para hacer permanente el cambio."
        ),
        (
            "¿El módulo de Paquete Herrajes se integra con Presupuestos?",
            "Sí. En el módulo de Presupuestos, existe la tabla 'partida_paquetes' que referencia "
            "directamente los paquetes creados aquí. Al seleccionar un paquete, se cargan automáticamente "
            "todos los herrajes que lo componen."
        ),
        (
            "¿Puedo imprimir solo un paquete específico?",
            "No directamente. El reporte imprime todos los paquetes existentes. "
            "Para filtrar, use la opción de búsqueda antes de imprimir."
        ),
        (
            "¿Qué significa el botón 'Refresh'?",
            "Prueba la conexión a la base de datos y actualiza el autocompletado. "
            "No guarda datos ni limpia la pantalla."
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