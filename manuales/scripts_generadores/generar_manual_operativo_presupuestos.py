# -*- coding: utf-8 -*-
"""
D:\vah\manuales\scripts_generadores\generar_manual_operativo_presupuestos.py
Generador de Manual Operativo - Módulo Presupuestos VAH
Genera un PDF profesional con:
- Índice clickeable (navegación interna)
- Buscador de palabras (PDF searchable)
- Marca de agua: logo VAH al 7%
- Numeración: "Página X"
- Encabezado: "VAH - Manual Operativo - Presupuestos"
- Color corporativo: #1f6feb

ACTUALIZADO: 2026-08-25
- Menú reestructurado (sin Reportes, sin Ventana)
- Mantenimiento con submenús de Materiales y Paquetes
- Atajos de teclado actualizados
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
MODULO = "Presupuestos"
TIPO_MANUAL = "Operativo"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "presupuestos")
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
VERSION = "2.0"

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
    return Paragraph(texto.replace('\n', '<br/>').replace(' ', ' '), estilo_codigo)


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
    """Genera el PDF del manual operativo de Presupuestos."""
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
        "Sistema ERP para gestión de presupuestos de aluminio y herrería.<br/>"
        "Módulo principal del sistema VAH.",
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
        ("  4.1", "Panel Izquierdo", "interfaz-izquierdo"),
        ("  4.2", "Panel Derecho", "interfaz-derecho"),
        ("5.", "Gestión de Clientes", "clientes"),
        ("  5.1", "Buscar Cliente", "cliente-buscar"),
        ("  5.2", "Crear Nuevo Cliente", "cliente-nuevo"),
        ("6.", "Gestión de Presupuestos", "presupuestos"),
        ("  6.1", "Crear Nuevo Presupuesto", "presupuesto-nuevo"),
        ("  6.2", "Abrir Presupuesto Existente", "presupuesto-abrir"),
        ("  6.3", "Guardar Presupuesto", "presupuesto-guardar"),
        ("  6.4", "Guardar Como (Duplicar)", "presupuesto-duplicar"),
        ("7.", "Gestión de Partidas", "partidas"),
        ("  7.1", "Crear Nueva Partida", "partida-nueva"),
        ("  7.2", "Navegar entre Partidas", "partida-navegar"),
        ("  7.3", "Duplicar Partida", "partida-duplicar"),
        ("  7.4", "Eliminar Partida", "partida-eliminar"),
        ("8.", "Agregar Materiales", "materiales"),
        ("  8.1", "Tipos de Materiales", "materiales-tipos"),
        ("  8.2", "Búsqueda de Materiales", "materiales-buscar"),
        ("  8.3", "Agregar Material", "materiales-agregar"),
        ("  8.4", "Editar Cantidades", "materiales-editar"),
        ("  8.5", "Eliminar Material", "materiales-eliminar"),
        ("9.", "Gestión de Paquetes", "paquetes"),
        ("  9.1", "Agregar Paquete", "paquete-agregar"),
        ("  9.2", "Ver Componentes (Tabla Anidada)", "paquete-anidada"),
        ("10.", "Cálculos Automáticos", "calculos"),
        ("  10.1", "Desperdicio", "calculo-desperdicio"),
        ("  10.2", "Factor de Venta (F.V.)", "calculo-fv"),
        ("  10.3", "Mano de Obra", "calculo-mo"),
        ("  10.4", "Accesorios", "calculo-acc"),
        ("  10.5", "Aplicar Dimensiones Globales", "calculo-dimensiones"),
        ("11.", "Impresión y Generación de PDF", "impresion"),
        ("  11.1", "Configurar Notas, Forma de Pago y Plazo", "impresion-notas"),
        ("  11.2", "Vista Previa", "impresion-vista"),
        ("  11.3", "Generar PDF", "impresion-pdf"),
        ("12.", "Corrector Ortográfico", "corrector"),
        ("  12.1", "Campos con Corrector", "corrector-campos"),
        ("  12.2", "Agregar Palabras al Diccionario", "corrector-agregar"),
        ("13.", "Atajos de Teclado", "atajos"),
        ("14.", "Menú Principal", "menu"),
        ("  14.1", "Menú Archivo", "menu-archivo"),
        ("  14.2", "Menú Presupuesto", "menu-presupuesto"),
        ("  14.3", "Menú Mantenimiento", "menu-mantenimiento"),
        ("  14.4", "Menú Ayuda", "menu-ayuda"),
        ("15.", "Solución de Problemas", "problemas"),
        ("16.", "Preguntas Frecuentes", "faq"),
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
        "El <b>Módulo de Presupuestos</b> es el <b>corazón del ERP VAH</b>. "
        "Es una herramienta completa diseñada para la creación, gestión y seguimiento "
        "de presupuestos para proyectos de aluminio, herrería, vidrio, plásticos y materiales varios.",
        estilo_normal
    ))
    historia.append(Paragraph(
        "Este manual operativo está dirigido a los <b>usuarios finales</b> del sistema: personal "
        "de ventas, cotizadores y cualquier usuario que requiera elaborar presupuestos profesionales.",
        estilo_normal
    ))
    historia.append(Paragraph("<b>Funcionalidades principales:</b>", estilo_normal))
    historia.append(_lista([
        "Gestión de clientes (búsqueda, selección, creación).",
        "Creación de presupuestos con múltiples partidas.",
        "Soporte para 8 tipos de materiales: Aluminio, Herrajes, Herrería, Vidrio, Plásticos, Otros, Paquete Aluminio, Paquete Herrajes.",
        "Cálculos automáticos con Desperdicio (%) y Factor de Venta (%).",
        "Dimensiones globales aplicables a toda la partida.",
        "Mano de obra y accesorios por partida.",
        "Gestión de paquetes (expansión recursiva de componentes).",
        "Tabla anidada para visualizar componentes de paquetes.",
        "Generación de PDF profesional con membrete y marca de agua.",
        "Corrector ortográfico integrado en campos de texto.",
        "Navegación completa por teclado con atajos.",
        "Acceso directo a catálogos de materiales y paquetes desde el menú.",
    ]))
    historia.append(PageBreak())

    # ============== 2. REQUISITOS DEL SISTEMA ==============
    historia.append(_ancla("requisitos"))
    historia.append(Paragraph("2. Requisitos del Sistema", estilo_heading1))
    historia.append(Paragraph(
        "Para utilizar el Módulo de Presupuestos, su equipo debe cumplir con los siguientes requisitos:",
        estilo_normal
    ))
    datos_req = [
        ["Componente", "Requisito"],
        ["Sistema Operativo", "Windows 10 o superior (64 bits)"],
        ["Python", "3.12 o superior"],
        ["Base de Datos", "SQL Server (Express o Standard)"],
        ["Bases de datos requeridas", "presupuestos, clientes, aluminio, herrajes, herreria, plasticos, otros, vidrio"],
        ["ODBC Driver", "ODBC Driver 17 o 18 for SQL Server"],
        ["Memoria RAM", "Mínimo 4 GB (8 GB recomendado)"],
        ["Resolución", "1366 x 768 o superior (recomendado 1920x1080)"],
        ["Librerías Python", "PyQt6, pyodbc, reportlab"],
        ["Corrector ortográfico", "pyspellchecker (opcional, recomendado)"],
    ]
    historia.append(_tabla(datos_req, anchos=[70 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_nota(
        "Para el corrector ortográfico, ejecute: <font face='Courier'>pip install pyspellchecker</font>"
    ))
    historia.append(PageBreak())

    # ============== 3. INICIO DEL MÓDULO ==============
    historia.append(_ancla("inicio"))
    historia.append(Paragraph("3. Inicio del Módulo", estilo_heading1))
    historia.append(Paragraph(
        "El Módulo de Presupuestos se inicia desde el menú principal del ERP VAH. "
        "Al abrirlo, se muestra la pantalla principal maximizada, lista para crear un nuevo presupuesto.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("pantalla_principal.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "El número de presupuesto se genera automáticamente a partir del último registrado + 1."
    ))
    historia.append(PageBreak())

    # ============== 4. INTERFAZ PRINCIPAL ==============
    historia.append(_ancla("interfaz"))
    historia.append(Paragraph("4. Interfaz Principal", estilo_heading1))
    historia.append(Paragraph(
        "La interfaz se divide en un Splitter 20%/80%:",
        estilo_normal
    ))
    historia.append(_lista([
        "<b>Panel Izquierdo (20%):</b> Datos del presupuesto, Datos de la partida, Valores de la partida, Resumen.",
        "<b>Panel Derecho (80%):</b> Barra de búsqueda de materiales y tablas (Materiales, Herrería, Paquetes, Anidada).",
    ]))

    # 4.1 Panel Izquierdo
    historia.append(_ancla("interfaz-izquierdo"))
    historia.append(Paragraph("4.1 Panel Izquierdo", estilo_heading2))
    historia.append(_imagen("panel_izquierdo.png", ancho=80 * mm))
    datos_panel_izq = [
        ["Grupo", "Campos", "Descripción"],
        ["Datos del Presupuesto", "CLIENTE, OBRA, PRESUPUESTO, PARTIDA, FECHA, COLOR",
         "Datos generales del presupuesto"],
        ["Datos de la Partida", "TÍTULO, DESCRIPCIÓN", "Descripción de la partida actual"],
        ["Valores de la Partida", "DESPERDICIO, F.V., COLOR, $/KG, KG, ANCHO, ALTO, MO, ACC, P.U., PIEZAS",
         "Parámetros de cálculo"],
        ["Resumen", "TOTAL PARTIDA, SUB TOTAL, I.V.A., TOTAL", "Totales del presupuesto"],
    ]
    historia.append(_tabla(datos_panel_izq, anchos=[40 * mm, 70 * mm, 46 * mm]))

    # 4.2 Panel Derecho
    historia.append(_ancla("interfaz-derecho"))
    historia.append(Paragraph("4.2 Panel Derecho", estilo_heading2))
    historia.append(_imagen("panel_derecho.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "El panel derecho contiene la <b>barra de búsqueda de materiales</b> (Tipo, Buscar por, Filtro) "
        "y <b>cuatro tablas</b> que se muestran según el contexto:",
        estilo_normal
    ))
    historia.append(_lista([
        "<b>📦 Paquetes:</b> Muestra los paquetes agregados a la partida.",
        "<b>📝 Anidada:</b> Muestra los componentes del paquete seleccionado (solo visual).",
        "<b> Materiales:</b> Tabla estándar para aluminio, vidrio, plásticos, herrajes, otros.",
        "<b>🔧 Herrería:</b> Tabla especializada para materiales de herrería (con kg/m).",
    ]))
    historia.append(PageBreak())

    # ============== 5. GESTIÓN DE CLIENTES ==============
    historia.append(_ancla("clientes"))
    historia.append(Paragraph("5. Gestión de Clientes", estilo_heading1))
    historia.append(_ancla("cliente-buscar"))
    historia.append(Paragraph("5.1 Buscar Cliente", estilo_heading2))
    historia.append(Paragraph(
        "Al escribir en el campo <b>CLIENTE</b>, el sistema muestra una lista desplegable "
        "con los clientes que coinciden con el texto ingresado. La búsqueda se realiza "
        "por nombre completo (título, nombre, apellido paterno, apellido materno).",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("buscar_cliente.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "Seleccione el cliente deseado con <b>clic</b> o <b>Enter</b>.",
        "El ID del cliente se guarda automáticamente.",
        "El botón <b>Nuevo cliente</b> permite agregar un cliente no registrado.",
    ]))
    historia.append(_ancla("cliente-nuevo"))
    historia.append(Paragraph("5.2 Crear Nuevo Cliente", estilo_heading2))
    historia.append(Paragraph(
        "Para crear un nuevo cliente, presione el botón <b>Nuevo cliente</b> "
        "y complete el formulario:",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("nuevo_cliente.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "<b>Título:</b> SR., SRA., SRITA., ARQ., ING., LIC., DR. (opcional).",
        "<b>Nombre:</b> Obligatorio.",
        "<b>A. Paterno:</b> Obligatorio.",
        "<b>A. Materno:</b> Opcional.",
        "Todos los campos se guardan en MAYÚSCULAS automáticamente.",
    ]))
    historia.append(PageBreak())

    # ============== 6. GESTIÓN DE PRESUPUESTOS ==============
    historia.append(_ancla("presupuestos"))
    historia.append(Paragraph("6. Gestión de Presupuestos", estilo_heading1))
    historia.append(_ancla("presupuesto-nuevo"))
    historia.append(Paragraph("6.1 Crear Nuevo Presupuesto", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Archivo → Nuevo Presupuesto</b> (Ctrl+N).",
        "El número de presupuesto se incrementa automáticamente.",
        "Se limpian todos los datos de la pantalla.",
        "Se crea automáticamente la primera partida.",
    ]))
    historia.append(_ancla("presupuesto-abrir"))
    historia.append(Paragraph("6.2 Abrir Presupuesto Existente", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Archivo → Abrir Presupuesto</b> (Ctrl+O).",
        "Se abre un diálogo con filtros de búsqueda:",
        "   - Número exacto",
        "   - Cliente",
        "   - Obra",
        "   - Rango de fechas",
        "Seleccione el presupuesto y haga clic en <b>Abrir</b>.",
        "El sistema carga todas las partidas y materiales.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("abrir_presupuesto.png", ancho=160 * mm))
    historia.append(_ancla("presupuesto-guardar"))
    historia.append(Paragraph("6.3 Guardar Presupuesto", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Archivo → Guardar Presupuesto</b> (Ctrl+S).",
        "También se guarda <b>AUTOMÁTICAMENTE</b> al cambiar de partida.",
        "Se guardan: presupuesto, partidas, items, paquetes, notas, forma de pago, plazo.",
    ]))
    historia.append(_ancla("presupuesto-duplicar"))
    historia.append(Paragraph("6.4 Guardar Como (Duplicar)", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Archivo → Guardar Como...</b> (Ctrl+Shift+S).",
        "Crea una copia del presupuesto actual con un nuevo número.",
        "Útil para crear presupuestos similares.",
    ]))
    historia.append(PageBreak())

    # ============== 7. GESTIÓN DE PARTIDAS ==============
    historia.append(_ancla("partidas"))
    historia.append(Paragraph("7. Gestión de Partidas", estilo_heading1))
    historia.append(_ancla("partida-nueva"))
    historia.append(Paragraph("7.1 Crear Nueva Partida", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Presupuesto → Nueva Partida</b> (Ctrl+T).",
        "También desde el botón <b>→</b> (Partida siguiente).",
        "La nueva partida se crea con el número siguiente automático.",
        "Se limpian todos los campos y tablas.",
    ]))
    historia.append(_ancla("partida-navegar"))
    historia.append(Paragraph("7.2 Navegar entre Partidas", estilo_heading2))
    historia.append(_imagen("navegacion_partidas.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "<b>ComboBox de partidas:</b> Seleccione directamente la partida.",
        "<b>Botón ← (Anterior):</b> Va a la partida anterior.",
        "<b>Botón → (Siguiente):</b> Va a la partida siguiente.",
        "<b>La partida actual se guarda automáticamente</b> antes de cambiar.",
    ]))
    historia.append(_ancla("partida-duplicar"))
    historia.append(Paragraph("7.3 Duplicar Partida", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Presupuesto → Duplicar Partida</b>.",
        "Crea una copia de la partida actual con un nuevo número.",
        "Los materiales, paquetes y valores se copian.",
        "Los precios se recalculan con los precios actuales de la base de datos.",
    ]))
    historia.append(_ancla("partida-eliminar"))
    historia.append(Paragraph("7.4 Eliminar Partida", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Presupuesto → Eliminar Partida</b> (Del).",
        "Confirme la eliminación.",
        "Las partidas restantes se renumeran automáticamente.",
    ]))
    historia.append(PageBreak())

    # ============== 8. AGREGAR MATERIALES ==============
    historia.append(_ancla("materiales"))
    historia.append(Paragraph("8. Agregar Materiales", estilo_heading1))
    historia.append(_ancla("materiales-tipos"))
    historia.append(Paragraph("8.1 Tipos de Materiales", estilo_heading2))
    datos_tipos = [
        ["Tipo", "Campos", "Cálculo"],
        ["Aluminio", "Ancho, Alto, CA, CH, Piezas, Color", "Precio por color / (Largo - 0.10) × Metros"],
        ["Herrajes", "Piezas", "Precio unitario × Piezas"],
        ["Herrería", "Ancho, Alto, CA, CH, Piezas", "Kgs = ((CA×Ancho)+(CH×Alto)) × Kg/m → P.U. = Kgs × $/kg"],
        ["Vidrio", "Ancho, Alto, Piezas", "m² × Precio m²"],
        ["Plásticos", "Piezas", "Precio unitario × Piezas"],
        ["Otros", "Piezas", "Precio unitario × Piezas"],
        ["Paquete Aluminio", "Ancho, Alto, Piezas", "Expande componentes (recursivo)"],
        ["Paquete Herrajes", "Piezas", "Expande herrajes (recursivo)"],
    ]
    historia.append(_tabla(datos_tipos, anchos=[35 * mm, 40 * mm, 81 * mm]))
    historia.append(_ancla("materiales-buscar"))
    historia.append(Paragraph("8.2 Búsqueda de Materiales", estilo_heading2))
    historia.append(_imagen("busqueda_materiales.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "Seleccione el <b>TIPO</b> de material.",
        "Seleccione <b>BUSCAR POR</b>: CLAVE (prefijo) o DESCRIPCIÓN (contiene).",
        "Escriba el texto en <b>FILTRO</b>.",
        "Aparece una lista con los resultados.",
        "Seleccione el material deseado (clic o Enter).",
        "El sistema agrega el material a la tabla correspondiente.",
    ]))
    historia.append(_ancla("materiales-agregar"))
    historia.append(Paragraph("8.3 Agregar Material", estilo_heading2))
    historia.append(_lista([
        "Después de seleccionar el material, se agrega automáticamente a la tabla.",
        "El <b>Precio Unitario</b> e <b>Importe</b> se calculan automáticamente.",
        "Para Aluminio: edite <b>CA</b> y <b>CH</b> (cantidades de tramos).",
        "Para Herrería: edite <b>CA</b> y <b>CH</b> (número de barras).",
        "Para todos: edite <b>Ancho</b>, <b>Alto</b> y <b>Piezas</b>.",
        "El sistema recalcula inmediatamente al editar cualquier campo.",
    ]))
    historia.append(_ancla("materiales-editar"))
    historia.append(Paragraph("8.4 Editar Cantidades", estilo_heading2))
    historia.append(_lista([
        "Haga <b>doble clic</b> en la celda que desea editar.",
        "Modifique el valor.",
        "Presione <b>Enter</b> para confirmar.",
        "El <b>P.U.</b> e <b>Importe</b> se recalculan automáticamente.",
        "Los campos <b>no editables</b> aparecen con fondo gris.",
    ]))
    historia.append(_ancla("materiales-eliminar"))
    historia.append(Paragraph("8.5 Eliminar Material", estilo_heading2))
    historia.append(_lista([
        "<b>Seleccione la fila</b> de la tabla.",
        "Presione <b>Delete</b> o use el menú contextual.",
        "Confirme la eliminación.",
        "La fila desaparece y los totales se recalculan.",
    ]))
    historia.append(PageBreak())

    # ============== 9. GESTIÓN DE PAQUETES ==============
    historia.append(_ancla("paquetes"))
    historia.append(Paragraph("9. Gestión de Paquetes", estilo_heading1))
    historia.append(_ancla("paquete-agregar"))
    historia.append(Paragraph("9.1 Agregar Paquete", estilo_heading2))
    historia.append(_imagen("agregar_paquete.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "Seleccione <b>PAQUETE ALUMINIO</b> o <b>PAQUETE HERRAJES</b> en el ComboBox de Tipo.",
        "Busque el paquete por clave o descripción.",
        "Seleccione el paquete de la lista.",
        "El paquete aparece en la tabla <b>📦 Paquetes</b>.",
        "Seleccione la fila del paquete para ver sus componentes en la tabla <b> Anidada</b>.",
        "El paquete se <b>expande</b> automáticamente y sus componentes se agregan a la tabla de materiales.",
        "Cambios en <b>Ancho, Alto o Piezas</b> del paquete actualizan todos sus componentes.",
    ]))
    historia.append(_ancla("paquete-anidada"))
    historia.append(Paragraph("9.2 Ver Componentes (Tabla Anidada)", estilo_heading2))
    historia.append(_imagen("tabla_anidada.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "La tabla anidada es <b>SOLO VISUAL</b>. No participa en cálculos ni guardado. "
        "Su propósito es mostrar al usuario qué contiene el paquete seleccionado."
    ))
    historia.append(PageBreak())

    # ============== 10. CÁLCULOS AUTOMÁTICOS ==============
    historia.append(_ancla("calculos"))
    historia.append(Paragraph("10. Cálculos Automáticos", estilo_heading1))
    historia.append(_ancla("calculo-desperdicio"))
    historia.append(Paragraph("10.1 Desperdicio", estilo_heading2))
    historia.append(Paragraph(
        "El <b>Desperdicio</b> es un porcentaje que se aplica <b>después</b> de sumar los importes "
        "de materiales, mano de obra y accesorios. Representa material que se pierde en el proceso.",
        estilo_normal
    ))
    historia.append(_codigo(
        "Base = TotalMateriales + MO + Accesorios<br/>"
        "ConDesperdicio = Base + (Base × Desperdicio%)"
    ))
    historia.append(_ancla("calculo-fv"))
    historia.append(Paragraph("10.2 Factor de Venta (F.V.)", estilo_heading2))
    historia.append(Paragraph(
        "El <b>Factor de Venta</b> es un porcentaje que se aplica <b>después</b> del desperdicio. "
        "Representa la utilidad o gastos indirectos.",
        estilo_normal
    ))
    historia.append(_codigo(
        "ConFV = ConDesperdicio + (ConDesperdicio × FV%)"
    ))
    historia.append(_ancla("calculo-mo"))
    historia.append(Paragraph("10.3 Mano de Obra", estilo_heading2))
    historia.append(Paragraph(
        "El campo <b>MANO DE OBRA</b> es un monto fijo que se suma <b>antes</b> de aplicar desperdicio y F.V.",
        estilo_normal
    ))
    historia.append(_ancla("calculo-acc"))
    historia.append(Paragraph("10.4 Accesorios", estilo_heading2))
    historia.append(Paragraph(
        "El campo <b>ACCESORIOS</b> es un monto fijo que se suma <b>antes</b> de aplicar desperdicio y F.V.",
        estilo_normal
    ))
    historia.append(_ancla("calculo-dimensiones"))
    historia.append(Paragraph("10.5 Aplicar Dimensiones Globales", estilo_heading2))
    historia.append(_imagen("dimensiones_globales.png", ancho=100 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "Capture <b>ANCHO</b> y <b>ALTO</b> globales en el panel izquierdo.",
        "Los valores se aplican automáticamente a todos los materiales de la partida.",
        "Los paquetes siguen las dimensiones SOLO si no están personalizados (regla sigue/se respeta).",
    ]))
    historia.append(PageBreak())

    # ============== 11. IMPRESIÓN Y GENERACIÓN DE PDF ==============
    historia.append(_ancla("impresion"))
    historia.append(Paragraph("11. Impresión y Generación de PDF", estilo_heading1))
    historia.append(_ancla("impresion-notas"))
    historia.append(Paragraph("11.1 Configurar Notas, Forma de Pago y Plazo", estilo_heading2))
    historia.append(_imagen("notas_dialog.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "Antes de imprimir, el sistema pregunta si desea configurar notas.",
        "<b>NOTAS ACLARATORIAS:</b> Texto que aparece después del total.",
        "<b>FORMA DE PAGO:</b> Seleccione una opción predefinida o escriba personalizada.",
        "<b>PLAZO DE ENTREGA:</b> Seleccione días o fecha específica.",
        "Los datos se guardan en la base de datos.",
    ]))
    historia.append(_ancla("impresion-vista"))
    historia.append(Paragraph("11.2 Vista Previa", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Archivo → Vista Previa de Impresión</b>.",
        "Genera el PDF y lo abre automáticamente.",
        "Permite revisar el presupuesto antes de imprimir.",
    ]))
    historia.append(_ancla("impresion-pdf"))
    historia.append(Paragraph("11.3 Generar PDF", estilo_heading2))
    historia.append(_lista([
        "Menú <b>Archivo → Imprimir</b> (Ctrl+P).",
        "El PDF incluye membrete, marca de agua, notas, forma de pago y plazo.",
        "Se guarda automáticamente en <b>D:\\vah\\pdfs\\</b>.",
    ]))
    historia.append(PageBreak())

    # ============== 12. CORRECTOR ORTOGRÁFICO ==============
    historia.append(_ancla("corrector"))
    historia.append(Paragraph("12. Corrector Ortográfico", estilo_heading1))
    historia.append(_ancla("corrector-campos"))
    historia.append(Paragraph("12.1 Campos con Corrector", estilo_heading2))
    historia.append(_imagen("corrector.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_lista([
        "<b>OBRA</b> - Campo de texto multilínea.",
        "<b>TÍTULO DE PARTIDA</b> - Campo de texto.",
        "<b>DESCRIPCIÓN DE LA PARTIDA</b> - Campo de texto multilínea.",
        "Las palabras mal escritas aparecen <b>subrayadas en ROJO</b>.",
        "Haga <b>clic derecho</b> sobre una palabra subrayada para ver sugerencias.",
    ]))
    historia.append(_ancla("corrector-agregar"))
    historia.append(Paragraph("12.2 Agregar Palabras al Diccionario", estilo_heading2))
    historia.append(_lista([
        "Haga <b>clic derecho</b> sobre una palabra subrayada.",
        "Seleccione <b>➕ Agregar 'palabra' al diccionario</b>.",
        "La palabra ya no será marcada como error en el futuro.",
    ]))
    historia.append(PageBreak())

    # ============== 13. ATAJOS DE TECLADO ==============
    historia.append(_ancla("atajos"))
    historia.append(Paragraph("13. Atajos de Teclado", estilo_heading1))
    historia.append(Paragraph(
        "El módulo incluye atajos de teclado para agilizar las operaciones:",
        estilo_normal
    ))
    datos_atajos = [
        ["Atajo", "Acción"],
        ["Ctrl+N", "Nuevo Presupuesto"],
        ["Ctrl+O", "Abrir Presupuesto"],
        ["Ctrl+S", "Guardar Presupuesto"],
        ["Ctrl+Shift+S", "Guardar Como (Duplicar)"],
        ["Ctrl+P", "Imprimir"],
        ["Ctrl+T", "Nueva Partida"],
        ["Del", "Eliminar Partida"],
        ["F5", "Recalcular Todo"],
        ["F1", "Contenido de Ayuda"],
        ["Enter", "Aceptar / Avanzar"],
        ["Tab", "Avanzar campo"],
        ["Shift+Tab", "Retroceder campo"],
        ["Esc", "Cancelar / Cerrar"],
    ]
    historia.append(_tabla(datos_atajos, anchos=[60 * mm, 96 * mm]))
    historia.append(PageBreak())

    # ============== 14. MENÚ PRINCIPAL ==============
    historia.append(_ancla("menu"))
    historia.append(Paragraph("14. Menú Principal", estilo_heading1))
    historia.append(Paragraph(
        "El menú principal del módulo de Presupuestos está organizado en 4 secciones:",
        estilo_normal
    ))

    # 14.1 Menú Archivo
    historia.append(_ancla("menu-archivo"))
    historia.append(Paragraph("14.1 Menú Archivo", estilo_heading2))
    datos_menu_archivo = [
        ["Opción", "Atajo", "Descripción"],
        ["Nuevo Presupuesto", "Ctrl+N", "Crea un nuevo presupuesto"],
        ["Abrir Presupuesto", "Ctrl+O", "Abre un presupuesto existente"],
        ["Guardar Presupuesto", "Ctrl+S", "Guarda el presupuesto actual"],
        ["Guardar Como...", "Ctrl+Shift+S", "Duplica el presupuesto con nuevo número"],
        ["Imprimir", "Ctrl+P", "Genera e imprime el PDF"],
        ["Vista Previa de Impresión", "-", "Previsualiza el PDF antes de imprimir"],
        ["Salir", "Ctrl+Q", "Cierra el módulo"],
    ]
    historia.append(_tabla(datos_menu_archivo, anchos=[50 * mm, 35 * mm, 71 * mm]))
    historia.append(Spacer(1, 5 * mm))

    # 14.2 Menú Presupuesto
    historia.append(_ancla("menu-presupuesto"))
    historia.append(Paragraph("14.2 Menú Presupuesto", estilo_heading2))
    datos_menu_presupuesto = [
        ["Opción", "Atajo", "Descripción"],
        ["Nueva Partida", "Ctrl+T", "Crea una nueva partida"],
        ["Duplicar Partida", "-", "Duplica la partida actual"],
        ["Eliminar Partida", "Del", "Elimina la partida actual"],
        ["Recalcular Todo", "F5", "Recalcula todas las partidas del presupuesto"],
    ]
    historia.append(_tabla(datos_menu_presupuesto, anchos=[50 * mm, 35 * mm, 71 * mm]))
    historia.append(Spacer(1, 5 * mm))

    # 14.3 Menú Mantenimiento
    historia.append(_ancla("menu-mantenimiento"))
    historia.append(Paragraph("14.3 Menú Mantenimiento", estilo_heading2))
    historia.append(Paragraph(
        "El menú Mantenimiento permite acceder a los catálogos de materiales y paquetes, "
        "así como configurar parámetros del sistema.",
        estilo_normal
    ))
    historia.append(Paragraph("<b>Catálogo de Materiales</b> (submenú):", estilo_normal))
    historia.append(_lista([
        "Aluminio - Catálogo de perfiles de aluminio",
        "Herrería - Catálogo de perfiles de herrería",
        "Vidrio - Catálogo de vidrios",
        "Herrajes - Catálogo de herrajes",
        "Plásticos - Catálogo de plásticos",
        "Otros - Catálogo de otros materiales",
    ]))
    historia.append(Paragraph("<b>Catálogo de Paquetes</b> (submenú):", estilo_normal))
    historia.append(_lista([
        "Aluminio - Catálogo de paquetes de aluminio",
        "Herrajes - Catálogo de paquetes de herrajes",
    ]))
    historia.append(Paragraph("<b>Parámetros del Sistema</b>:", estilo_normal))
    historia.append(_lista([
        "Configurar número inicial de presupuesto",
        "Configurar color global por defecto",
        "Configurar desperdicio y F.V. por defecto",
        "Configurar IVA",
        "Configurar clave de administrador",
    ]))
    historia.append(Spacer(1, 5 * mm))

    # 14.4 Menú Ayuda
    historia.append(_ancla("menu-ayuda"))
    historia.append(Paragraph("14.4 Menú Ayuda", estilo_heading2))
    datos_menu_ayuda = [
        ["Opción", "Atajo", "Descripción"],
        ["Contenido de Ayuda", "F1", "Muestra información de ayuda"],
        ["Tutoriales", "-", "Acceso a tutoriales del sistema"],
        ["Acerca de VAH", "-", "Información del sistema y versión"],
    ]
    historia.append(_tabla(datos_menu_ayuda, anchos=[50 * mm, 35 * mm, 71 * mm]))
    historia.append(PageBreak())

    # ============== 15. SOLUCIÓN DE PROBLEMAS ==============
    historia.append(_ancla("problemas"))
    historia.append(Paragraph("15. Solución de Problemas", estilo_heading1))
    problemas = [
        (
            "El módulo no abre o muestra error de importación",
            [
                "Verifique que Python 3.12+ esté instalado.",
                "Ejecute: <font face='Courier'>pip install PyQt6 pyodbc reportlab</font>",
                "Para el corrector: <font face='Courier'>pip install pyspellchecker</font>",
                "Revise que SQL Server esté en ejecución.",
                "Verifique que todas las bases de datos existan.",
            ]
        ),
        (
            "Error de conexión a la base de datos",
            [
                "Verifique que el servicio SQL Server esté iniciado.",
                "Confirme que las bases de datos existan (presupuestos, clientes, aluminio, etc.).",
                "Revise que ODBC Driver 17/18 esté instalado.",
                "Verifique el nombre del servidor en el código o variable de entorno VAH_SQLSERVER.",
            ]
        ),
        (
            "No aparecen materiales en la búsqueda",
            [
                "Verifique que la tabla correspondiente al tipo seleccionado tenga datos.",
                "Use el botón de búsqueda completa (filtro vacío) para ver todos.",
                "Verifique la conexión a la base de datos.",
            ]
        ),
        (
            "Los cálculos no se actualizan",
            [
                "Presione <b>F5</b> (Recalcular Todo).",
                "Verifique que los valores de Desperdicio y F.V. sean correctos.",
                "Asegúrese de que los precios de los materiales existan en la base de datos.",
            ]
        ),
        (
            "El PDF no se genera",
            [
                "Verifique que ReportLab esté instalado: <font face='Courier'>pip install reportlab</font>",
                "Asegúrese de que el presupuesto tenga al menos una partida con datos.",
                "Revise que el directorio <b>D:\\vah\\pdfs</b> exista o se pueda crear.",
            ]
        ),
        (
            "El corrector ortográfico no funciona",
            [
                "Ejecute: <font face='Courier'>pip install pyspellchecker</font>",
                "Ejecute el instalador del diccionario: <b>instalar_diccionario_espanol.py</b>",
                "Verifique que el campo sea de tipo TextEditConCorrector.",
            ]
        ),
    ]
    for problema, soluciones in problemas:
        historia.append(Paragraph(f"<b>Problema:</b> {problema}", estilo_heading3))
        historia.append(Paragraph("<b>Soluciones:</b>", estilo_normal))
        historia.append(_lista(soluciones))
        historia.append(Spacer(1, 3 * mm))
    historia.append(PageBreak())

    # ============== 16. PREGUNTAS FRECUENTES ==============
    historia.append(_ancla("faq"))
    historia.append(Paragraph("16. Preguntas Frecuentes", estilo_heading1))
    faqs = [
        (
            "¿Qué diferencia hay entre Desperdicio y Factor de Venta?",
            "El <b>Desperdicio</b> representa material que se pierde en la fabricación. "
            "El <b>Factor de Venta (F.V.)</b> representa la utilidad o gastos indirectos. "
            "Se aplican en ese orden: primero Desperdicio, luego F.V."
        ),
        (
            "¿Cómo funcionan los paquetes anidados?",
            "Un <b>Paquete Herrajes (PH)</b> puede contener dentro otros PH. "
            "El sistema expande recursivamente todos los componentes hasta llegar a los herrajes individuales. "
            "Los multiplicadores se aplican correctamente a cada nivel."
        ),
        (
            "¿Puedo editar los componentes de un paquete directamente?",
            "No directamente. Debe editar el paquete en el módulo de Paquetes correspondiente. "
            "Los cambios en el paquete se reflejarán automáticamente en los presupuestos que lo usen."
        ),
        (
            "¿Qué significa COLOR GLOBAL = VARIOS?",
            "Cuando <b>COLOR GLOBAL</b> es <b>VARIOS</b>, cada material puede tener su propio color "
            "individualmente. Si se selecciona un color específico (ej. NATURAL), todos los materiales "
            "usan ese color y el campo individual se deshabilita."
        ),
        (
            "¿Los paquetes se guardan en el presupuesto?",
            "Sí. Los paquetes se guardan en la tabla <b>partida_paquetes</b>. "
            "Al reabrir un presupuesto, los paquetes se restauran y expanden correctamente."
        ),
        (
            "¿Puedo aplicar dimensiones globales solo a algunos materiales?",
            "No. La función de dimensiones globales afecta <b>TODOS</b> los materiales "
            "de la partida actual. Sin embargo, los paquetes personalizados mantienen sus dimensiones."
        ),
        (
            "¿Cómo accedo a los catálogos de materiales desde Presupuestos?",
            "Menú <b>Mantenimiento → Catálogo de Materiales</b> y seleccione el tipo de material. "
            "Se abrirá el catálogo correspondiente en una ventana independiente."
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
    print(f"Manual Operativo de {MODULO} generado: {ruta_salida}")
    return ruta_salida


if __name__ == "__main__":
    generar_manual()