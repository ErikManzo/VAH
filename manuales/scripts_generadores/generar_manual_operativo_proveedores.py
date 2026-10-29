# D:\vah\manuales\scripts_generadores\generar_manual_operativo_proveedores.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Operativo - Módulo Proveedores VAH
======================================================
Genera un PDF profesional con:
  - Índice clickeable (navegación interna)
  - Buscador de palabras (PDF searchable)
  - Marca de agua: logo VAH al 7%
  - Numeración: "Página X"
  - Encabezado: "VAH - Manual Operativo - Proveedores"
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
MODULO = "Proveedores"
TIPO_MANUAL = "Operativo"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "proveedores")
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
    """Genera el PDF del manual operativo de Proveedores."""

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
        "Sistema ERP para gestión de proveedores.<br/>"
        "Registro, administración y unificación de información de proveedores.",
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
        ("  5.1", "Registrar un Nuevo Proveedor", "op-nuevo"),
        ("  5.2", "Editar un Registro Existente", "op-editar"),
        ("  5.3", "Eliminar un Registro", "op-eliminar"),
        ("  5.4", "Buscar Proveedores", "op-buscar"),
        ("  5.5", "Ver Listado de Proveedores (Pantalla)", "op-pantalla"),
        ("  5.6", "Agrupar Proveedores Duplicados", "op-agrupar"),
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
        "El <b>Módulo de Proveedores</b> del ERP VAH es una herramienta diseñada para la gestión integral "
        "de la información de los proveedores de la empresa. Permite registrar, consultar, actualizar "
        "y eliminar proveedores, así como unificar registros duplicados.",
        estilo_normal
    ))
    historia.append(Paragraph(
        "Este manual operativo está dirigido a los <b>usuarios finales</b> del sistema: personal "
        "de compras, almacén y administrativo que requiere gestionar el catálogo de proveedores.",
        estilo_normal
    ))
    historia.append(Paragraph("<b>Funcionalidades principales:</b>", estilo_normal))
    historia.append(_lista([
        "Registro de nuevos proveedores con información completa.",
        "Edición de datos de proveedores existentes.",
        "Eliminación de registros.",
        "Búsqueda dinámica por nombre de empresa.",
        "Visualización de listados completos en pantalla.",
        "Unificación de proveedores duplicados con selección manual.",
    ]))
    historia.append(PageBreak())

    # ============== 2. REQUISITOS DEL SISTEMA ==============
    historia.append(_ancla("requisitos"))
    historia.append(Paragraph("2. Requisitos del Sistema", estilo_heading1))
    historia.append(Paragraph(
        "Para utilizar el Módulo de Proveedores, su equipo debe cumplir con los siguientes requisitos:",
        estilo_normal
    ))

    datos_req = [
        ["Componente", "Requisito"],
        ["Sistema Operativo", "Windows 10 o superior (64 bits)"],
        ["Python", "3.10 o superior"],
        ["Base de Datos", "SQL Server (Express o Standard)"],
        ["ODBC Driver", "ODBC Driver 17 o 18 for SQL Server"],
        ["Memoria RAM", "Mínimo 4 GB (8 GB recomendado)"],
        ["Resolución", "1366 x 768 o superior"],
        ["Librerías Python", "PyQt6, pyodbc"],
    ]
    historia.append(_tabla(datos_req, anchos=[70 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_nota(
        "Si el módulo no abre o muestra errores de conexión, verifique que SQL Server "
        "esté en ejecución y que la base de datos 'proveedores' exista."
    ))
    historia.append(PageBreak())

    # ============== 3. INICIO DEL MÓDULO ==============
    historia.append(_ancla("inicio"))
    historia.append(Paragraph("3. Inicio del Módulo", estilo_heading1))
    historia.append(Paragraph(
        "El Módulo de Proveedores se inicia desde el menú principal del ERP VAH. "
        "Al abrirlo, se muestra la pantalla principal en <b>estado inicial</b> (limpio), "
        "lista para realizar una nueva captura o buscar registros existentes.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("pantalla_principal.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "La pantalla siempre inicia en blanco. Para ver los registros existentes, "
        "active el modo <b>Editar</b>, <b>Eliminar</b> o <b>Pantalla</b>."
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
        "<b>Campos de Datos:</b> Captura de información del proveedor.",
        "<b>Tabla de Registros:</b> Visualización de los registros existentes.",
        "<b>Barra de Búsqueda:</b> Filtro dinámico por nombre de empresa.",
    ]))

    # 4.1 Barra de Botones
    historia.append(_ancla("interfaz-botones"))
    historia.append(Paragraph("4.1 Barra de Botones", estilo_heading2))
    historia.append(_imagen("botones_principales.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_botones = [
        ["Botón", "Función", "Atajo"],
        ["Guardar", "Registra un nuevo proveedor o guarda cambios", "Ctrl+S"],
        ["Editar", "Activa el modo edición para modificar registros", "—"],
        ["Eliminar", "Activa el modo eliminación (doble clic para confirmar)", "Supr"],
        ["Limpiar", "Limpia todos los campos y regresa al estado inicial", "—"],
        ["Refresh", "Refresca la base de datos y limpia la pantalla", "F5"],
        ["Pantalla", "Muestra todos los proveedores en la tabla", "—"],
        ["Salir", "Cierra el módulo", "Esc"],
        ["Agrupar", "Agrupa proveedores duplicados", "—"],
    ]
    historia.append(_tabla(datos_botones, anchos=[30 * mm, 96 * mm, 30 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "El botón <b>Pantalla</b> es la única opción de salida. No genera PDF, CSV o impresiones."
    ))

    # 4.2 Campos de Datos
    historia.append(_ancla("interfaz-campos"))
    historia.append(Paragraph("4.2 Campos de Datos", estilo_heading2))
    historia.append(_imagen("campos_datos.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))

    datos_campos = [
        ["Campo", "Descripción", "Validación"],
        ["Empresa", "Nombre de la empresa proveedora", "Obligatorio"],
        ["Tipo proveedor", "ALUMINIO, HERRERÍA, VIDRIO, HERRAJES, OTROS", "Opcional"],
        ["Nombre agente", "Persona de contacto", "Opcional"],
        ["Dirección", "Calle y número", "Opcional"],
        ["# Exterior", "Número exterior", "Opcional"],
        ["# Interior", "Número interior", "Opcional"],
        ["C.P.", "Código Postal", "Opcional"],
        ["Colonia", "Colonia o fraccionamiento", "Opcional"],
        ["Municipio", "Municipio o delegación", "Opcional"],
        ["Estado", "Seleccione de la lista", "Opcional"],
        ["R.F.C.", "Registro Federal de Contribuyentes", "Opcional"],
        ["Teléfono", "Número telefónico", "Opcional (formato 00-0000-0000)"],
        ["Correo", "Dirección de correo electrónico", "Opcional (se guarda en minúsculas)"],
    ]
    historia.append(_tabla(datos_campos, anchos=[30 * mm, 70 * mm, 56 * mm]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "El campo <b>Empresa</b> se convierte automáticamente a MAYÚSCULAS. "
        "El campo <b>Correo</b> se convierte automáticamente a minúsculas. "
        "La tecla <b>Enter</b> avanza al siguiente campo.",
        estilo_normal
    ))

    # 4.3 Tabla de Registros
    historia.append(_ancla("interfaz-tabla"))
    historia.append(Paragraph("4.3 Tabla de Registros", estilo_heading2))
    historia.append(_imagen("tabla_registros.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "La tabla muestra todos los campos del proveedor. "
        "Los registros aparecen ordenados alfabéticamente por empresa. "
        "Las filas alternan colores para facilitar la lectura. "
        "Al hacer <b>doble clic</b> sobre una fila en modo edición, los datos se cargan en los campos.",
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
        "mostrando solo los registros cuya empresa <b>comienza</b> con el texto ingresado.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== 5. OPERACIONES BÁSICAS ==============
    historia.append(_ancla("operaciones"))
    historia.append(Paragraph("5. Operaciones Básicas", estilo_heading1))

    # 5.1 Registrar Nuevo
    historia.append(_ancla("op-nuevo"))
    historia.append(Paragraph("5.1 Registrar un Nuevo Proveedor", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Verifique que la pantalla esté en estado inicial. Si no, presione <b>Limpiar</b>.",
        "Complete los campos del formulario. El campo <b>Empresa</b> es obligatorio.",
        "Presione <b>Enter</b> para avanzar entre campos.",
        "Haga clic en <b>Guardar</b> (Ctrl+S).",
        "Aparecerá un mensaje de confirmación: 'Proveedor guardado correctamente'.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("mensaje_guardar.png", ancho=100 * mm))

    # 5.2 Editar Registro
    historia.append(_ancla("op-editar"))
    historia.append(Paragraph("5.2 Editar un Registro Existente", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Editar</b>.",
        "La barra de búsqueda se activa. Escriba parte del nombre de la empresa.",
        "La tabla se filtrará mostrando las coincidencias.",
        "Haga <b>doble clic</b> sobre el registro deseado.",
        "Los datos se cargarán en los campos superiores.",
        "Modifique los campos necesarios.",
        "Presione <b>Guardar</b> (Ctrl+S).",
        "Aparecerá el mensaje: 'Proveedor actualizado correctamente'.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("mensaje_editar.png", ancho=100 * mm))

    # 5.3 Eliminar Registro
    historia.append(_ancla("op-eliminar"))
    historia.append(Paragraph("5.3 Eliminar un Registro", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Eliminar</b>.",
        "Se activa el modo eliminación. Use la barra de búsqueda para localizar el registro.",
        "Haga <b>doble clic</b> sobre la fila del proveedor a eliminar.",
        "El sistema pedirá confirmación: '¿Estas seguro de eliminar este proveedor?'.",
        "Seleccione <b>Sí</b> para eliminar o <b>No</b> para cancelar.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("modo_eliminar.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "<b>⚠️ Precaución:</b> La eliminación es <b>permanente</b>. "
        "No hay papelera de reciclaje ni opción de deshacer.",
        ParagraphStyle('Advertencia', parent=estilo_normal, textColor=HexColor("#dc2626"))
    ))

    # 5.4 Buscar Proveedores
    historia.append(_ancla("op-buscar"))
    historia.append(Paragraph("5.4 Buscar Proveedores", estilo_heading2))
    historia.append(Paragraph(
        "La búsqueda solo está disponible en los modos <b>Editar</b>, <b>Eliminar</b> y <b>Pantalla</b>. "
        "La búsqueda es por <b>prefijo</b> del nombre de la empresa. "
        "Ejemplo: escribir 'ACER' mostrará 'ACEROS', 'ACERCA', etc. "
        "Los resultados se muestran en orden descendente por empresa.",
        estilo_normal
    ))

    # 5.5 Pantalla
    historia.append(_ancla("op-pantalla"))
    historia.append(Paragraph("5.5 Ver Listado de Proveedores (Pantalla)", estilo_heading2))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Pantalla</b>.",
        "La tabla mostrará <b>TODOS</b> los proveedores registrados.",
        "Use el campo <b>Buscar por empresa</b> para filtrar la lista.",
        "Para regresar a la pantalla inicial, haga clic en <b>Regresar</b>.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota(
        "Esta función solo muestra datos en pantalla. No permite imprimir ni exportar a otros formatos."
    ))

    # 5.6 Agrupar Duplicados
    historia.append(_ancla("op-agrupar"))
    historia.append(Paragraph("5.6 Agrupar Proveedores Duplicados", estilo_heading2))
    historia.append(Paragraph(
        "Esta función permite unificar proveedores que podrían estar duplicados "
        "(por ejemplo, la misma empresa registrada dos veces).",
        estilo_normal
    ))
    historia.append(Paragraph("<b>Procedimiento paso a paso:</b>", estilo_normal))
    historia.append(_lista([
        "Haga clic en el botón <b>Agrupar coincidencias</b>.",
        "El sistema buscará automáticamente empresas con el mismo nombre.",
        "Si se encuentran múltiples grupos, seleccione cuál desea revisar.",
        "Se abrirá un diálogo mostrando los registros duplicados.",
        "Seleccione el registro que desea <b>CONSERVAR</b> (usando el radio button).",
        "Haga clic en <b>Unificar seleccionados</b>.",
        "Confirme la operación.",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("unificar_dialog.png", ancho=160 * mm))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "<b>Resultado:</b><br/>"
        "- El registro seleccionado se conserva y se fusionan sus datos con los otros.<br/>"
        "- Los registros no seleccionados se eliminan permanentemente.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph(
        "<b>⚠️ Precaución:</b> Esta acción NO se puede deshacer. "
        "Verifique cuidadosamente antes de confirmar.",
        ParagraphStyle('Advertencia', parent=estilo_normal, textColor=HexColor("#dc2626"))
    ))
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
        ["Ctrl+S", "Guardar proveedor"],
        ["Ctrl+F", "Activar búsqueda"],
        ["Supr", "Modo eliminar / Eliminar seleccionado"],
        ["F5", "Refrescar base de datos"],
        ["Esc", "Salir del módulo"],
        ["Enter", "Avanzar al siguiente campo (como Tab)"],
        ["Shift+Tab", "Retroceder al campo anterior"],
        ["Doble clic (tabla)", "Cargar registro para edición (en modo editar)"],
    ]
    historia.append(_tabla(datos_atajos, anchos=[50 * mm, 106 * mm]))
    historia.append(PageBreak())

    # ============== 7. SOLUCIÓN DE PROBLEMAS ==============
    historia.append(_ancla("problemas"))
    historia.append(Paragraph("7. Solución de Problemas", estilo_heading1))

    problemas = [
        (
            "El módulo no abre",
            [
                "Verifique que Python 3.10+ esté instalado.",
                "Ejecute: <font face='Courier'>pip install PyQt6 pyodbc</font>",
                "Revise que SQL Server esté en ejecución.",
            ]
        ),
        (
            "Error de conexión a la base de datos",
            [
                "Verifique que el servicio SQL Server esté iniciado.",
                "Confirme que existe la base de datos 'proveedores'.",
                "Revise que ODBC Driver 17/18 esté instalado.",
            ]
        ),
        (
            "No se puede guardar el proveedor",
            [
                "Verifique que el campo <b>Empresa</b> no esté vacío.",
                "Complete el teléfono con el formato completo (10 dígitos).",
                "Consulte el archivo de log para más detalles.",
            ]
        ),
        (
            "El sistema muestra un error al agrupar proveedores",
            [
                "Asegúrese de tener al menos 2 proveedores registrados.",
                "Verifique que tengan el mismo nombre de empresa.",
                "En el diálogo, seleccione el registro a conservar (radio button).",
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
            "¿Cómo diferencio entre proveedores de diferentes tipos?",
            "Use el campo <b>Tipo proveedor</b> para clasificarlos: ALUMINIO, HERRERÍA, VIDRIO, HERRAJES u OTROS."
        ),
        (
            "¿Qué pasa si una empresa tiene varias sucursales?",
            "Puede registrar cada sucursal por separado. Al usar la función 'Agrupar coincidencias', "
            "el sistema le permitirá decidir si unificarlas o mantenerlas separadas."
        ),
        (
            "¿Cómo busco un proveedor por RFC o teléfono?",
            "Actualmente, la búsqueda solo está disponible por EMPRESA. Use la función <b>Pantalla</b> "
            "para ver la lista completa y buscar visualmente."
        ),
        (
            "¿Qué significa el botón 'Refresh'?",
            "Refresca los datos desde la base de datos y limpia el formulario. No guarda cambios pendientes."
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