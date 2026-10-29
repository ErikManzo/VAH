# D:\vah\manuales\scripts_generadores\generar_manual_tecnico_presupuestos.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Técnico - Módulo Presupuestos VAH
=====================================================
Documentación técnica para desarrolladores y administradores.
"""

import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak, Table, TableStyle, ListFlowable, ListItem

# ==================== CONFIGURACIÓN ====================
MODULO = "Presupuestos"
TIPO_MANUAL = "Técnico"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "presupuestos")
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
estilo_nota = ParagraphStyle('Nota', parent=estilo_normal, fontName='Helvetica-Oblique', fontSize=9, textColor=HexColor("#6b7280"), leftIndent=5 * mm, rightIndent=5 * mm)


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


def _nota(texto):
    return Paragraph(f'📌 <b>Nota:</b> {texto}', estilo_nota)


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
        ("  3.1", "Tabla presupuestos", "bd-presupuestos"),
        ("  3.2", "Tabla partidas", "bd-partidas"),
        ("  3.3", "Tabla items_partida", "bd-items"),
        ("  3.4", "Tabla partida_paquetes", "bd-paquetes"),
        ("  3.5", "Tabla parametros_sistema", "bd-parametros"),
        ("  3.6", "Relaciones", "bd-relaciones"),
        ("4.", "Dependencias", "dependencias"),
        ("5.", "Módulos y Clases Principales", "modulos"),
        ("  5.1", "Clase PresupuestosWindow", "modulo-ventana"),
        ("  5.2", "Clase Service", "modulo-service"),
        ("  5.3", "Clase PresupuestoController", "modulo-controller"),
        ("  5.4", "Clase PaquetesController", "modulo-paquetes"),
        ("  5.5", "Clase FocusManager", "modulo-foco"),
        ("  5.6", "Calculadoras (calculators/)", "modulo-calculadoras"),
        ("  5.7", "Generador PDF", "modulo-pdf"),
        ("6.", "Flujo de Datos", "flujo"),
        ("  6.1", "Creación de Presupuesto", "flujo-crear"),
        ("  6.2", "Agregar Material", "flujo-agregar"),
        ("  6.3", "Agregar Paquete", "flujo-paquete"),
        ("  6.4", "Guardado de Partida", "flujo-guardar"),
        ("  6.5", "Impresión PDF", "flujo-pdf"),
        ("7.", "Manejo de Errores", "errores"),
        ("8.", "Logging y Depuración", "logging"),
        ("9.", "Configuración", "configuracion"),
        ("10.", "Integración con otros Módulos", "integracion"),
    ]

    datos_indice = [["#", "Sección"]]
    for num, titulo, ancla in secciones:
        datos_indice.append([num, Paragraph(f'<a href="#{ancla}" color="#1f6feb">{titulo}</a>', estilo_indice_link)])
    historia.append(_tabla(datos_indice, anchos=[15 * mm, 141 * mm]))
    historia.append(PageBreak())

    # 1. ARQUITECTURA
    historia.append(_ancla("arquitectura"))
    historia.append(Paragraph("1. Arquitectura del Sistema", estilo_heading1))
    historia.append(Paragraph("El Módulo de Presupuestos sigue una arquitectura de tres capas:", estilo_normal))
    datos_arq = [["Capa", "Tecnología", "Responsabilidad"],
                 ["Presentación", "PyQt6", "Interfaz gráfica (PresupuestosWindow)"],
                 ["Controladores", "Python 3.12", "PresupuestoController, PaquetesController"],
                 ["Lógica de Negocio", "Python + Calculators", "Dispatch de cálculos por tipo"],
                 ["Acceso a Datos", "pyodbc", "Clase Service con conexión a múltiples BD"],
                 ["Almacenamiento", "SQL Server", "Bases de datos: presupuestos, clientes, aluminio, herrajes, herreria, plasticos, otros, vidrio"]]
    historia.append(_tabla(datos_arq, anchos=[35 * mm, 35 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("arquitectura_sistema.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 2. ESTRUCTURA DE ARCHIVOS
    historia.append(_ancla("estructura"))
    historia.append(Paragraph("2. Estructura de Archivos", estilo_heading1))

    datos_files = [
        ["Archivo", "Descripción"],
        ["modulo_presupuestos.py", "UI principal (QMainWindow) con toda la interfaz"],
        ["service.py", "Capa de datos, conexión a BD, CRUD, precios"],
        ["busquedas.py", "Búsqueda de clientes y materiales con autocompletado"],
        ["foco.py", "FocusManager - navegación por teclado centralizada"],
        ["rules_zero_price.py", "Validación de precios > 0 antes de agregar"],
        ["service_outlook.py", "Envío de correos con Outlook COM"],
        ["service_mapi.py", "Envío de correos con MAPI (fallback)"],
        ["calculators/", "Calculadoras específicas por tipo de material"],
        ["controllers/", "Controladores de presupuesto y paquetes"],
        ["core/", "Constantes y utilidades"],
        ["models/", "Modelos de datos (Paquete, Componente)"],
        ["ui/", "MessageManager y diálogos"],
        ["reports/", "Generación de PDF y corrector ortográfico"],
    ]
    historia.append(_tabla(datos_files, anchos=[60 * mm, 96 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("estructura_modulos.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 3. BASE DE DATOS
    historia.append(_ancla("basedatos"))
    historia.append(Paragraph("3. Base de Datos", estilo_heading1))

    historia.append(_ancla("bd-presupuestos"))
    historia.append(Paragraph("3.1 Tabla presupuestos (presupuestos.dbo.presupuestos)", estilo_heading2))
    datos_presupuestos = [
        ["Columna", "Tipo", "Nulo", "Descripción"],
        ["id", "int", "NO", "PK - ID autoincremental"],
        ["cliente_id", "int", "NO", "FK → clientes.dbo.clientes.id"],
        ["obra", "varchar(50)", "NO", "Nombre de la obra"],
        ["presupuesto", "int", "NO", "Número de presupuesto (único)"],
        ["fecha", "date", "NO", "Fecha del presupuesto"],
        ["color_global", "varchar(30)", "NO", "Color global o 'VARIOS'"],
        ["descuento_porcentaje", "decimal(5,2)", "YES", "Descuento global"],
        ["notas", "text", "YES", "Notas aclaratorias"],
        ["forma_pago", "varchar(150)", "YES", "Forma de pago"],
        ["plazo_entrega", "varchar(150)", "YES", "Plazo de entrega"],
    ]
    historia.append(_tabla(datos_presupuestos, anchos=[35 * mm, 35 * mm, 15 * mm, 71 * mm]))

    historia.append(_ancla("bd-partidas"))
    historia.append(Paragraph("3.2 Tabla partidas (presupuestos.dbo.partidas)", estilo_heading2))
    datos_partidas = [
        ["Columna", "Tipo", "Descripción"],
        ["id", "int", "PK autoincremental"],
        ["presupuesto_id", "int", "FK → presupuestos.id"],
        ["partida", "int", "Número de partida (1,2,3...)"],
        ["titulo", "varchar(100)", "Título de la partida"],
        ["descripcion", "text", "Descripción detallada"],
        ["color_partida", "varchar(30)", "Color específico o vacío"],
        ["desperdicio", "decimal(5,2)", "Porcentaje de desperdicio"],
        ["fv_porcentaje", "decimal(5,2)", "Factor de venta %"],
        ["kg", "decimal(10,2)", "Kilos totales (herrería)"],
        ["ancho", "decimal(10,2)", "Ancho global de la partida"],
        ["alto", "decimal(10,2)", "Alto global de la partida"],
        ["mano_obra", "decimal(10,2)", "Monto de mano de obra"],
        ["accesorios", "decimal(10,2)", "Monto de accesorios"],
        ["piezas", "int", "Número de piezas"],
        ["precio_unitario", "decimal(12,2)", "P.U. de la partida"],
        ["total_partida", "decimal(12,2)", "Importe total de la partida"],
    ]
    historia.append(_tabla(datos_partidas, anchos=[40 * mm, 40 * mm, 76 * mm]))

    historia.append(_ancla("bd-items"))
    historia.append(Paragraph("3.3 Tabla items_partida (presupuestos.dbo.items_partida)", estilo_heading2))
    datos_items = [
        ["Columna", "Tipo", "Descripción"],
        ["id", "int", "PK autoincremental"],
        ["partida_id", "int", "FK → partidas.id"],
        ["tipo", "varchar(30)", "AL/HR/HE/VI/PL/OT/PH"],
        ["color", "varchar(30)", "Color del material"],
        ["clave", "varchar(50)", "Clave del material"],
        ["descripcion", "text", "Descripción"],
        ["ca", "decimal(10,2)", "Cantidad Ancho (tramos)"],
        ["ancho", "decimal(10,2)", "Ancho en metros"],
        ["ch", "decimal(10,2)", "Cantidad Alto (tramos)"],
        ["alto", "decimal(10,2)", "Alto en metros"],
        ["piezas", "int", "Número de piezas"],
        ["pu", "decimal(12,2)", "Precio Unitario"],
        ["importe", "decimal(12,2)", "Importe total"],
        ["metros", "decimal(10,2)", "Metros lineales (herrería)"],
        ["kg_m", "decimal(10,3)", "Kg/m (herrería)"],
        ["kgs", "decimal(10,3)", "Kilos totales (herrería)"],
        ["precio_kg", "decimal(12,2)", "Precio por kg (herrería)"],
    ]
    historia.append(_tabla(datos_items, anchos=[40 * mm, 40 * mm, 76 * mm]))

    historia.append(_ancla("bd-paquetes"))
    historia.append(Paragraph("3.4 Tabla partida_paquetes (presupuestos.dbo.partida_paquetes)", estilo_heading2))
    datos_paquetes = [
        ["Columna", "Tipo", "Descripción"],
        ["id", "int", "PK autoincremental"],
        ["partida_id", "int", "FK → partidas.id"],
        ["tipo_paquete", "varchar(50)", "PAQUETE ALUMINIO / PAQUETE HERRAJES"],
        ["clave_paquete", "varchar(50)", "Clave del paquete"],
        ["descripcion", "varchar(255)", "Descripción del paquete"],
        ["ancho", "decimal(10,2)", "Ancho del paquete"],
        ["alto", "decimal(10,2)", "Alto del paquete"],
        ["piezas", "int", "Piezas del paquete"],
    ]
    historia.append(_tabla(datos_paquetes, anchos=[40 * mm, 50 * mm, 66 * mm]))

    historia.append(_ancla("bd-parametros"))
    historia.append(Paragraph("3.5 Tabla parametros_sistema (presupuestos.dbo.parametros_sistema)", estilo_heading2))
    datos_parametros = [
        ["Columna", "Tipo", "Descripción"],
        ["id", "int", "PK (siempre 1)"],
        ["correo_remitente", "varchar(100)", "Correo para envíos"],
        ["contrasena_correo", "varchar(100)", "Contraseña del correo"],
        ["servidor_smtp", "varchar(100)", "Servidor SMTP"],
        ["puerto_smtp", "int", "Puerto SMTP"],
        ["numero_inicial_presupuesto", "int", "Número inicial para nuevos presupuestos"],
    ]
    historia.append(_tabla(datos_parametros, anchos=[40 * mm, 60 * mm, 56 * mm]))

    historia.append(_ancla("bd-relaciones"))
    historia.append(Paragraph("3.6 Relaciones y Claves Foráneas", estilo_heading2))
    historia.append(_lista([
        "FK_items_partida_partidas: items_partida.partida_id → partidas.id (ON DELETE CASCADE)",
        "FK_partida_paquetes_partida: partida_paquetes.partida_id → partidas.id (ON DELETE CASCADE)",
        "FK_partidas_presupuestos: partidas.presupuesto_id → presupuestos.id",
        "FK_resumen_presupuesto_presupuesto: resumen_presupuesto.presupuesto_id → presupuestos.id",
        "presupuestos.cliente_id → clientes.id (relación semántica, sin FK explícita en algunas versiones)",
    ]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("diagrama_bd.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 4. DEPENDENCIAS
    historia.append(_ancla("dependencias"))
    historia.append(Paragraph("4. Dependencias", estilo_heading1))
    datos_deps = [
        ["Librería", "Versión", "Uso"],
        ["PyQt6", "6.5+", "Interfaz gráfica completa"],
        ["pyodbc", "4.0+", "Conexión ODBC a SQL Server (múltiples BD)"],
        ["reportlab", "3.6+", "Generación de PDF profesional"],
        ["pywin32", "305+", "Outlook COM y MAPI para correos"],
        ["pyspellchecker", "0.6+", "Corrector ortográfico (opcional)"],
        ["Python", "3.10+", "Lenguaje base"],
    ]
    historia.append(_tabla(datos_deps, anchos=[40 * mm, 30 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "pip install PyQt6 pyodbc reportlab pywin32 pyspellchecker"
    ))
    historia.append(PageBreak())

    # 5. MÓDULOS Y CLASES PRINCIPALES
    historia.append(_ancla("modulos"))
    historia.append(Paragraph("5. Módulos y Clases Principales", estilo_heading1))

    historia.append(_ancla("modulo-ventana"))
    historia.append(Paragraph("5.1 Clase PresupuestosWindow (modulo_presupuestos.py)", estilo_heading2))
    historia.append(_lista([
        "_build_ui() - Construye toda la interfaz",
        "_build_menu() - Construye el menú principal",
        "_on_guardar() - Guarda presupuesto",
        "_on_abrir_presupuesto() - Abre diálogo de búsqueda",
        "_on_nueva_partida() - Crea nueva partida",
        "_on_partida_anterior/siguiente() - Navegación",
        "_on_imprimir() / _on_vista_previa() - Generación PDF",
        "_on_enviar_correo() - Envío por correo",
        "_on_recalcular_todo() - F5 - Recalcula todas las filas",
        "_add_std() - Agrega material a tabla estándar",
        "_add_he() - Agrega material a tabla herrería",
        "_calc_std_row() / _calc_he_row() - Cálculo por fila",
        "_recalc_summary() - Actualiza totales",
        "_sync_color_rule() - Maneja colores globales",
        "_actualizar_combo_partidas() - Actualiza ComboBox de navegación",
        "eventFilter() - Captura teclas",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Atajos de teclado\n"
        "Ctrl+N → _on_nuevo_presupuesto\n"
        "Ctrl+O → _on_abrir_presupuesto\n"
        "Ctrl+S → _on_guardar\n"
        "Ctrl+Shift+S → _on_guardar_como\n"
        "Ctrl+P → _on_imprimir\n"
        "Ctrl+E → _on_exportar_excel\n"
        "Ctrl+D → _on_exportar_pdf\n"
        "Ctrl+M → _on_enviar_correo\n"
        "Ctrl+T → _on_nueva_partida\n"
        "Delete → _delete_table_row\n"
        "F5 → _on_recalcular_todo"
    ))

    historia.append(_ancla("modulo-service"))
    historia.append(Paragraph("5.2 Clase Service (service.py)", estilo_heading2))
    historia.append(_lista([
        "connect() / cn() - Conexión a SQL Server con autodetección de drivers",
        "cursor() - Context manager para cursores",
        "buscar_por_tabla() / buscar_por_tipo() - Búsqueda de materiales",
        "clientes_buscar() - Búsqueda de clientes por nombre completo",
        "aluminio_precio(), aluminio_largo() - Precios y largo de aluminio",
        "vidrio_precio() - Precio de vidrio por m²",
        "herreria_kg_por_m() - Kg/m de herrería",
        "herrajes_precio(), plasticos_precio(), otros_precio() - Precios unitarios",
        "paquete_aluminio_items() - Componentes de paquete de aluminio",
        "paquete_herrajes_items() - Componentes de paquete de herrajes",
        "paquete_herrajes_precio_total() - Suma de precios de un PH",
        "guardar_presupuesto(), guardar_partida(), guardar_items_partida(), guardar_paquetes_partida()",
        "obtener_presupuesto(), obtener_partidas(), obtener_items_partida(), obtener_paquetes_partida()",
        "obtener_ultimo_numero_presupuesto() - Para consecutivo automático",
        "buscar_presupuestos() - Búsqueda avanzada con filtros",
        "obtener_parametros_sistema(), guardar_parametros_sistema()",
        "obtener_configuracion_presupuesto(), guardar_configuracion_presupuesto()",
        "enviar_correo_presupuesto() - SMTP",
    ]))

    historia.append(_ancla("modulo-controller"))
    historia.append(Paragraph("5.3 Clase PresupuestoController (controllers/presupuesto_controller.py)", estilo_heading2))
    historia.append(_lista([
        "guardar_partida_actual_silencioso() - Guardado automático al cambiar partida",
        "partida_anterior() / partida_siguiente() - Navegación",
        "cargar_partida_por_indice() - Desde ComboBox",
        "crear_nueva_partida() - Creación de partida",
        "duplicar_partida_actual() - Duplicación",
        "eliminar_partida_actual() - Eliminación",
        "cargar_presupuesto() - Carga completa desde BD",
        "aplicar_dimensiones_globales() - Aplica ancho/alto a todos los materiales",
        "recalcular_por_color() - Recalcula al cambiar color",
        "_recolectar_datos_presupuesto() / _recolectar_datos_partida() / _recolectar_items_partida()",
    ]))

    historia.append(_ancla("modulo-paquetes"))
    historia.append(Paragraph("5.4 Clase PaquetesController (controllers/paquetes_controller.py)", estilo_heading2))
    historia.append(_lista([
        "_cargar_componentes_base() - Carga desde BD con expansión recursiva de PH",
        "_expandir_componentes_ph() - Expande paquetes de herrajes anidados",
        "_consolidar_a_materiales() - Toma componentes y los agrega a la tabla de materiales",
        "_mostrar_en_anidada() - Muestra componentes en tabla visual (solo informativa)",
        "_on_piezas_cambiadas() / _on_ancho_cambiado() / _on_alto_cambiado() - Actualiza consolidación",
        "Fórmula: cantidad_final = cantidad_base × multiplicador_ph × piezas_paquete",
    ]))

    historia.append(_ancla("modulo-foco"))
    historia.append(Paragraph("5.5 Clase FocusManager (foco.py)", estilo_heading2))
    historia.append(_lista([
        "FOCUS_FLOW - Orden de navegación por campos",
        "_move_focus_global() - Navegación entre widgets principales",
        "_move_in_table() - Navegación dentro de tablas",
        "_handle_list_enter() - Selección en listas de búsqueda",
        "eventFilter() - Filtro global de teclas",
        "Soporte para Tab, Shift+Tab, Enter, Escape, Flechas, Delete",
    ]))

    historia.append(_ancla("modulo-calculadoras"))
    historia.append(Paragraph("5.6 Calculadoras (calculators/)", estilo_heading2))
    historia.append(_lista([
        "dispatch_calculo(ctx) - Router central por tipo de material",
        "aluminio.compute_aluminio() - Fórmula: (CA × Ancho + CH × Alto) × (Precio_color / (Largo - 0.10))",
        "herreria.compute_herreria() - Kgs = ((CA×Ancho)+(CH×Alto)) × Kg/m → P.U. = Kgs × $/kg",
        "vidrio.compute_vidrio() - m² = Ancho × Alto → P.U. = m² × Precio_m2",
        "paquete_aluminio.compute_paquete_aluminio_inline() - Expande componentes recursivamente",
        "paquete_herrajes.compute_paquete_herrajes_inline() - Expande herrajes recursivamente",
        "dimensioning.adjust_dimension() - Redondeo industrial a múltiplo de 0.05",
    ]))

    historia.append(_ancla("modulo-pdf"))
    historia.append(Paragraph("5.7 Generador PDF (reports/)", estilo_heading2))
    historia.append(_lista([
        "GeneradorPresupuestoPDF - Clase principal",
        "generar_pdf() - Genera PDF desde modelo DatosPresupuesto",
        "pdf_models.DatosPresupuesto - Modelo de datos",
        "pdf_models.PartidaPresupuesto - Partida individual",
        "pdf_models.TotalesPresupuesto - Totales",
        "PresupuestoPDFService.generar_pdf_desde_id() - Servicio desde BD",
        "NotasManager - Gestión de notas, forma de pago, plazo",
        "CorrectorOrtografico - Corrector ortográfico en tiempo real",
        "TextEditConCorrector - QTextEdit con subrayado de errores",
    ]))
    historia.append(PageBreak())

    # 6. FLUJO DE DATOS
    historia.append(_ancla("flujo"))
    historia.append(Paragraph("6. Flujo de Datos", estilo_heading1))

    historia.append(_ancla("flujo-crear"))
    historia.append(Paragraph("6.1 Creación de Presupuesto", estilo_heading2))
    historia.append(_lista([
        "1. Usuario ingresa Cliente (busca o crea nuevo)",
        "2. Usuario ingresa Obra, Fecha, Color Global",
        "3. Usuario crea partida (Ctrl+T o botón Siguiente)",
        "4. Usuario ingresa Título y Descripción (con corrector ortográfico)",
        "5. Usuario configura Desperdicio, F.V., MO, Accesorios",
        "6. Usuario agrega materiales (selecciona tipo, busca, selecciona)",
        "7. El sistema calcula P.U. e Importe automáticamente",
        "8. Usuario repite para más materiales",
        "9. Usuario puede agregar paquetes (expansión automática)",
        "10. Usuario guarda presupuesto (Ctrl+S o al cambiar partida)",
    ]))

    historia.append(_ancla("flujo-agregar"))
    historia.append(Paragraph("6.2 Agregar Material", estilo_heading2))
    historia.append(_lista([
        "1. Usuario selecciona Tipo (Aluminio, Herrajes, etc.)",
        "2. Usuario selecciona Buscar Por (CLAVE o DESCRIPCIÓN)",
        "3. Usuario escribe filtro → textChanged → _search_timer(160ms) → busquedas.do_search()",
        "4. service.buscar_por_tipo() → consulta SQL a BD correspondiente",
        "5. Resultados en lst_result con UserRole conteniendo los datos",
        "6. Usuario selecciona item → on_pick_result()",
        "7. Según tipo, llama a _add_std() o _add_he()",
        "8. Se inserta fila en tabla y se llama a _calc_std_row()",
        "9. dispatch_calculo() → calculadora específica por tipo",
        "10. Se actualizan PU, Importe, y _recalc_summary()",
    ]))

    historia.append(_ancla("flujo-paquete"))
    historia.append(Paragraph("6.3 Agregar Paquete", estilo_heading2))
    historia.append(_lista([
        "1. Usuario selecciona Tipo = PAQUETE ALUMINIO o PAQUETE HERRAJES",
        "2. Usuario busca y selecciona paquete → _on_pick_result_paquete()",
        "3. tbl_paquetes.agregar_paquete() → dispara paqueteAgregado",
        "4. PaquetesController._on_paquete_agregado()",
        "5. _cargar_componentes_base() - Carga desde BD (expansión recursiva de PH)",
        "6. _mostrar_en_anidada() - Muestra en tabla visual",
        "7. _consolidar_a_materiales() - Expande a tabla de materiales",
        "8. Si cambia piezas/ancho/alto → re-consolidación automática",
    ]))

    historia.append(_ancla("flujo-guardar"))
    historia.append(Paragraph("6.4 Guardado de Partida", estilo_heading2))
    historia.append(_lista([
        "1. Usuario cambia de partida o presiona Ctrl+S",
        "2. PresupuestoController.guardar_partida_actual_silencioso()",
        "3. _recolectar_datos_presupuesto() - Obtiene datos del presupuesto",
        "4. _recolectar_datos_partida() - Obtiene datos de partida",
        "5. _recolectar_items_partida() - Recorre tablas (tbl, tbl_he)",
        "6. _recolectar_paquetes_partida() - Recorre tbl_paquetes",
        "7. service.guardar_presupuesto() - INSERT/UPDATE",
        "8. service.guardar_partida() - INSERT/UPDATE",
        "9. service.guardar_items_partida() - DELETE + INSERT",
        "10. service.guardar_paquetes_partida() - DELETE + INSERT",
        "11. Se emite señal listaPartidasActualizada para actualizar ComboBox",
    ]))

    historia.append(_ancla("flujo-pdf"))
    historia.append(Paragraph("6.5 Impresión PDF", estilo_heading2))
    historia.append(_lista([
        "1. Usuario presiona Imprimir o Vista Previa",
        "2. PresupuestoPDFService.generar_pdf_desde_id(presupuesto_id)",
        "3. service.obtener_presupuesto() - Datos del presupuesto",
        "4. service.obtener_partidas() - Lista de partidas",
        "5. service.obtener_configuracion_presupuesto() - Notas, forma_pago, plazo",
        "6. NotasManager.preguntar_notas() - Diálogo opcional",
        "7. Construir modelo DatosPresupuesto con partidas",
        "8. GeneradorPresupuestoPDF.generar_pdf()",
        "9. _dibujar_presupuesto_completo() - Dibuja página por página",
        "10. PartidaManager maneja saltos de página (partidas no se dividen)",
        "11. Se guarda PDF en D:\\vah\\pdfs\\{numero}.pdf",
        "12. Se abre automáticamente el PDF",
    ]))
    historia.append(PageBreak())

    # 7. MANEJO DE ERRORES
    historia.append(_ancla("errores"))
    historia.append(Paragraph("7. Manejo de Errores", estilo_heading1))
    datos_err = [
        ["Nivel", "Mecanismo", "Ejemplo"],
        ["Validación UI", "Comprobaciones en _agregar_item()", "Clave vacía → mensaje"],
        ["Existencia material", "rules_zero_price.py", "Pregunta si desea agregar"],
        ["Clave duplicada", "paquete_existe() + QMessageBox.question", "Pregunta sobrescritura"],
        ["Conexión BD", "try/except + múltiples drivers/variantes", "RuntimeError con detalle"],
        ["Eliminación", "Diálogo de confirmación", "Mensaje '¿Seguro?'"],
        ["Impresión", "try/except + MessageManager", "Error silencioso o crítico según categoría"],
        ["Guardado automático", "Siempre silencioso", "Solo log, no molesta al usuario"],
    ]
    historia.append(_tabla(datos_err, anchos=[35 * mm, 50 * mm, 71 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "# MessageManager - centralización de mensajes\n"
        "MessageManager.info(parent, 'Título', 'Mensaje')\n"
        "MessageManager.warning(parent, 'Título', 'Advertencia')\n"
        "MessageManager.critical(parent, 'Título', 'Error')\n"
        "MessageManager.error_calculo(parent, 'Error de cálculo')\n"
        "MessageManager.confirmar_dimensiones(parent) -> bool"
    ))
    historia.append(PageBreak())

    # 8. LOGGING Y DEPURACIÓN
    historia.append(_ancla("logging"))
    historia.append(Paragraph("8. Logging y Depuración", estilo_heading1))
    historia.append(_lista([
        "MessageManager con categorías: ERROR_CALCULO (silencioso), CONFIRMACION, INFO, ADVERTENCIA, PLACEHOLDER, DEBUG, CRITICO",
        "Para activar logs de depuración: MessageManager.enable_all()",
        "Para silenciar: MessageManager.silence_all()",
        "Los errores de cálculo se registran en consola pero no molestan al usuario",
        "Para depuración, ejecutar módulo desde consola:",
        "   python -m presupuestos.modulo_presupuestos",
        "El módulo imprimir.py tiene manejo de excepciones con traceback",
        "El corrector ortográfico tiene logs en consola",
    ]))

    # 9. CONFIGURACIÓN
    historia.append(_ancla("configuracion"))
    historia.append(Paragraph("9. Configuración", estilo_heading1))
    historia.append(Paragraph("Cadena de conexión a SQL Server (service.py):", estilo_normal))
    historia.append(_codigo(
        'CANDIDATE_SERVERS = [\n'
        '    ENV_SERVER or "",\n'
        '    r"DESKTOP-AE60PIU\\SQLEXPRESS",\n'
        '    r"(local)\\SQLEXPRESS",\n'
        '    r".\\SQLEXPRESS",\n'
        '    r"localhost\\SQLEXPRESS",\n'
        '    r"127.0.0.1,1433",\n'
        ']\n\n'
        'def connect(self):\n'
        '    for driver in ("{ODBC Driver 18 for SQL Server}", "{ODBC Driver 17 for SQL Server}"):\n'
        '        for server in CANDIDATE_SERVERS:\n'
        '            try:\n'
        '                return pyodbc.connect(conn_str)\n'
        '            except: continue\n'
        '    raise RuntimeError("No se pudo conectar")'
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("Variables de entorno:", estilo_normal))
    historia.append(_codigo(
        'VAH_SQLSERVER - Sobrescribe el servidor por defecto\n'
        'Ejemplo: set VAH_SQLSERVER=DESKTOP-OTRO\\SQLEXPRESS'
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("Constantes (core/constants.py):", estilo_normal))
    historia.append(_codigo(
        '# Índices de columnas\n'
        'C_TIPO=0, C_COLOR=1, C_CLAVE=2, C_DESC=3, C_CA=4, C_ANCHO=5, C_CH=6, C_ALTO=7, C_PZAS=8, C_PU=9, C_IMP=10\n'
        'H_TIPO=0, H_CLAVE=1, H_DESC=2, H_CA=3, H_ANCHO=4, H_CH=5, H_ALTO=6, H_METROS=7, H_KG_M=8, H_KGS=9, H_PKG=10, H_PZAS=11, H_PU=12, H_IMP=13\n'
        'P_TIPO=0, P_CLAVE=1, P_DESC=2, P_ANCHO=3, P_ALTO=4, P_PZAS=5\n'
        'A_TIPO=0, A_COLOR=1, A_CLAVE=2, A_DESC=3, A_CA=4, A_ANCHO=5, A_CH=6, A_ALTO=7, A_PZAS=8, A_PU=9, A_IMP=10\n\n'
        '# Reglas de editabilidad\n'
        'EDITABILIDAD = {\n'
        '    "ALUMINIO": dict(CA=True, CH=True, ANCHO=True, ALTO=True, PZAS=True),\n'
        '    "HERRAJES": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),\n'
        '    "HERRERÍA": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),\n'
        '    ...\n'
        '}'
    ))
    historia.append(PageBreak())

    # 10. INTEGRACIÓN CON OTROS MÓDULOS
    historia.append(_ancla("integracion"))
    historia.append(Paragraph("10. Integración con otros Módulos", estilo_heading1))
    datos_integracion = [
        ["Módulo", "Tabla/Relación", "Descripción"],
        ["Clientes", "clientes.dbo.clientes", "FK presupuestos.cliente_id → clientes.id"],
        ["Materiales Aluminio", "aluminio.dbo.materiales_aluminio", "Búsqueda de perfiles y precios por color"],
        ["Materiales Herrajes", "herrajes.dbo.materiales_herraje", "Búsqueda de herrajes y precios"],
        ["Materiales Herrería", "herreria.dbo.materiales_herreria", "Kg/m para cálculo"],
        ["Materiales Vidrio", "vidrio.dbo.materiales_vidrio", "Precio por m²"],
        ["Materiales Plásticos", "plasticos.dbo.materiales_plasticos", "Precio unitario"],
        ["Materiales Otros", "otros.dbo.materiales_otros", "Precio unitario"],
        ["Paquetes Aluminio", "aluminio.dbo.paquetes_aluminio / paquete_aluminio_items", "Expansión de paquetes"],
        ["Paquetes Herrajes", "herrajes.dbo.paquetes_herrajes / paquete_herraje_items", "Expansión recursiva de herrajes"],
        ["Parámetros Sistema", "presupuestos.dbo.parametros_sistema", "Configuración de correo y números iniciales"],
    ]
    historia.append(_tabla(datos_integracion, anchos=[35 * mm, 55 * mm, 66 * mm]))
    historia.append(PageBreak())

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
