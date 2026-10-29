# D:\vah\manuales\scripts_generadores\generar_manual_tecnico_paquete_herrajes.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Técnico - Módulo Paquete Herrajes VAH
=========================================================
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
MODULO = "Paquete Herrajes"
TIPO_MANUAL = "Técnico"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "paquete_herrajes")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf", "técnico")
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
    ruta_salida = os.path.join(RUTA_PDF, f"VAH_Manual_Tecnico_{MODULO.replace(' ', '_')}.pdf")
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
        ("  3.1", "Tabla paquetes_herrajes", "bd-paquetes"),
        ("  3.2", "Tabla paquete_herraje_items", "bd-items"),
        ("  3.3", "Relaciones y FKs", "bd-relaciones"),
        ("4.", "Dependencias", "dependencias"),
        ("5.", "Módulos y Clases Principales", "modulos"),
        ("  5.1", "Clase DBManager", "modulo-dbmanager"),
        ("  5.2", "Clase PaqueteHerrajesUI", "modulo-pantalla"),
        ("  5.3", "Clase PrintOptionsDialog", "modulo-impresion"),
        ("6.", "Flujo de Datos", "flujo"),
        ("  6.1", "Creación de Paquete", "flujo-crear"),
        ("  6.2", "Edición de Paquete", "flujo-editar"),
        ("  6.3", "Impresión", "flujo-impresion"),
        ("7.", "Manejo de Errores", "errores"),
        ("8.", "Logging y Depuración", "logging"),
        ("9.", "Configuración", "configuracion"),
        ("10.", "Integración con Presupuestos", "integracion"),
    ]

    datos_indice = [["#", "Sección"]]
    for num, titulo, ancla in secciones:
        datos_indice.append([num, Paragraph(f'<a href="#{ancla}" color="#1f6feb">{titulo}</a>', estilo_indice_link)])
    historia.append(_tabla(datos_indice, anchos=[15 * mm, 141 * mm]))
    historia.append(PageBreak())

    # 1. ARQUITECTURA
    historia.append(_ancla("arquitectura"))
    historia.append(Paragraph("1. Arquitectura del Sistema", estilo_heading1))
    historia.append(Paragraph("El Módulo de Paquete Herrajes sigue una arquitectura de tres capas:", estilo_normal))
    datos_arq = [["Capa", "Tecnología", "Responsabilidad"],
                 ["Presentación", "PyQt6", "Interfaz gráfica (PaqueteHerrajesUI)"],
                 ["Lógica de Negocio", "Python 3.12", "DBManager, validaciones de paquete"],
                 ["Acceso a Datos", "pyodbc + SQL Server", "CRUD sobre paquetes_herrajes y paquete_herraje_items"],
                 ["Almacenamiento", "SQL Server", "Base de datos 'herrajes', tablas de paquetes"]]
    historia.append(_tabla(datos_arq, anchos=[35 * mm, 35 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("arquitectura_sistema.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 2. ESTRUCTURA DE ARCHIVOS
    historia.append(_ancla("estructura"))
    historia.append(Paragraph("2. Estructura de Archivos", estilo_heading1))
    datos_files = [
        ["Archivo", "Descripción"],
        ["pantalla_paquete_herrajes.py", "UI principal (QMainWindow) con lógica de eventos y modos"],
        ["imprimir.py", "Generación de reportes (General/Desglosado) a Pantalla/PDF/Impresora"],
        ["__init__.py", "Marcador de paquete Python (vacío)"],
    ]
    historia.append(_tabla(datos_files, anchos=[70 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("estructura_modulos.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 3. BASE DE DATOS
    historia.append(_ancla("basedatos"))
    historia.append(Paragraph("3. Base de Datos", estilo_heading1))

    historia.append(_ancla("bd-paquetes"))
    historia.append(Paragraph("3.1 Tabla paquetes_herrajes", estilo_heading2))
    datos_paquetes = [
        ["Columna", "Tipo", "Nulo", "Descripción"],
        ["clave", "varchar(20)", "NO", "PK - Clave única del paquete"],
        ["descripcion", "varchar(100)", "NO", "Descripción del paquete"],
    ]
    historia.append(_tabla(datos_paquetes, anchos=[35 * mm, 40 * mm, 15 * mm, 66 * mm]))

    historia.append(_ancla("bd-items"))
    historia.append(Paragraph("3.2 Tabla paquete_herraje_items", estilo_heading2))
    datos_items = [
        ["Columna", "Tipo", "Nulo", "Descripción"],
        ["clave_paquete", "varchar(20)", "NO", "FK → paquetes_herrajes.clave"],
        ["clv_herraje", "varchar(20)", "NO", "FK → materiales_herraje.Clave"],
        ["cantidad", "int", "NO", "Cantidad de piezas del herraje"],
    ]
    historia.append(_tabla(datos_items, anchos=[35 * mm, 40 * mm, 15 * mm, 66 * mm]))

    historia.append(_ancla("bd-relaciones"))
    historia.append(Paragraph("3.3 Relaciones y Claves Foráneas", estilo_heading2))
    historia.append(_lista([
        "FK_paquete_herraje_items_paquetes: paquete_herraje_items.clave_paquete → paquetes_herrajes.clave (ON DELETE CASCADE)",
        "FK_paquete_herraje_items_materiales: paquete_herraje_items.clv_herraje → materiales_herraje.Clave",
        "CASCADE: Al eliminar un paquete, se eliminan automáticamente todos sus items.",
        "No hay ON DELETE CASCADE hacia materiales_herraje por seguridad.",
    ]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("diagrama_bd.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 4. DEPENDENCIAS
    historia.append(_ancla("dependencias"))
    historia.append(Paragraph("4. Dependencias", estilo_heading1))
    datos_deps = [
        ["Librería", "Versión", "Uso"],
        ["PyQt6", "6.5+", "Interfaz gráfica completa (QMainWindow, QTableWidget, QCompleter)"],
        ["pyodbc", "4.0+", "Conexión ODBC a SQL Server"],
        ["reportlab", "3.6+", "Generación de PDF para impresión"],
        ["win32print", "pywin32", "Impresión directa a impresora física (filtrado de virtuales)"],
        ["Python", "3.10+", "Lenguaje base"],
    ]
    historia.append(_tabla(datos_deps, anchos=[40 * mm, 30 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "pip install PyQt6 pyodbc reportlab pywin32"
    ))
    historia.append(PageBreak())

    # 5. MÓDULOS Y CLASES PRINCIPALES
    historia.append(_ancla("modulos"))
    historia.append(Paragraph("5. Módulos y Clases Principales", estilo_heading1))

    historia.append(_ancla("modulo-dbmanager"))
    historia.append(Paragraph("5.1 Clase DBManager (dentro del mismo archivo)", estilo_heading2))
    historia.append(_lista([
        "materiales_buscar(texto, por) → List[Dict] - Búsqueda de herrajes (clave o descripción)",
        "paquete_existe(clave_paquete) → bool - Verifica existencia de paquete",
        "paquetes_listar() → List[Dict] - Obtiene todos los paquetes",
        "paquetes_y_items() → List[Dict] - Obtiene paquetes con sus items anidados",
        "paquete_cargar(clave_paquete) → Tuple[Dict, List] - Carga paquete completo",
        "paquete_guardar(header, items) - Guarda o actualiza paquete (UPSERT)",
        "paquete_eliminar(clave_paquete) - Elimina paquete y sus items (CASCADE manual)",
        "cn() → Connection - Context manager con autodetección de drivers",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Ejemplo de guardado de paquete\n"
        "db = DBManager()\n"
        "header = {\n"
        '    "clave": "PAQ-001",\n'
        '    "descripcion": "Paquete de prueba"\n'
        "}\n"
        "items = [\n"
        '    {"clave": "TOR-101", "descripcion": "Tornillo", "cantidad": 10},\n'
        '    {"clave": "BIS-202", "descripcion": "Bisagra", "cantidad": 4}\n'
        "]\n"
        "db.paquete_guardar(header, items)"
    ))

    historia.append(_ancla("modulo-pantalla"))
    historia.append(Paragraph("5.2 Clase PaqueteHerrajesUI (QMainWindow)", estilo_heading2))
    historia.append(_lista([
        "on_guardar() - Guarda paquete (modo nuevo o edición)",
        "on_editar() - Abre PaquetePicker y carga paquete para edición",
        "on_eliminar() - Elimina paquete por clave (input dialog)",
        "on_imprimir() - Llama a imprimir_paquetes() desde imprimir.py",
        "on_herraje() - Abre pantalla_herrajes.py en subproceso",
        "_agregar_item() - Agrega herraje a la lista local",
        "on_quitar_item() - Elimina herraje de la lista local",
        "_buscar_popup() - Maneja autocompletado con QCompleter + QTableView",
        "_refrescar_tabla_items() - Actualiza QTableWidget con self.items",
        "_append_pending_if_any() - Guarda item pendiente antes de guardar paquete",
        "eventFilter() - Captura Delete en tabla",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Atajos de teclado definidos\n"
        "Ctrl+S → on_guardar\n"
        "Ctrl+P → on_imprimir\n"
        "Delete → on_quitar_item (en tabla)\n"
        "F5 → Inicio (refresh)\n"
        "Esc → close"
    ))

    historia.append(_ancla("modulo-impresion"))
    historia.append(Paragraph("5.3 Clase PrintOptionsDialog y funciones de impresión (imprimir.py)", estilo_heading2))
    historia.append(_lista([
        "PrintOptionsDialog - Diálogo con destino (Pantalla/PDF/Impresora) y tipo (General/Desglosado)",
        "ScreenReportGeneral / ScreenReportDesglosado - Ventanas de vista previa",
        "_build_html_general() / _build_html_desglosado() - Generadores HTML para PDF",
        "_filtrar_impresoras_fisicas() - Excluye impresoras virtuales (PDF, XPS, OneNote, Fax)",
        "_print_to_physical() - Impresión directa a impresora física",
        "imprimir(parent, db) - Función principal de impresión",
    ]))
    historia.append(PageBreak())

    # 6. FLUJO DE DATOS
    historia.append(_ancla("flujo"))
    historia.append(Paragraph("6. Flujo de Datos", estilo_heading1))

    historia.append(_ancla("flujo-crear"))
    historia.append(Paragraph("6.1 Creación de Paquete", estilo_heading2))
    historia.append(_lista([
        "1. Usuario captura clave y descripción del paquete",
        "2. Usuario busca herrajes (autocompletado por clave o descripción)",
        "3. Usuario ingresa cantidad y presiona Agregar",
        "4. _agregar_item() valida y agrega a self.items",
        "5. _refrescar_tabla_items() actualiza QTableWidget",
        "6. Usuario repite pasos 2-5 para agregar más herrajes",
        "7. Usuario presiona Guardar",
        "8. _append_pending_if_any() verifica si hay item pendiente",
        "9. Validaciones: clave y descripción no vacías, al menos un item",
        "10. Si modo='nuevo', verifica que clave no exista (pregunta sobrescritura)",
        "11. db.paquete_guardar() ejecuta transacción SQL",
        "12. UI muestra mensaje de éxito y limpia pantalla",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("flujo_datos_crear.png", ancho=160 * mm))

    historia.append(_ancla("flujo-editar"))
    historia.append(Paragraph("6.2 Edición de Paquete", estilo_heading2))
    historia.append(_lista([
        "1. Usuario presiona Editar",
        "2. Se abre PaquetePicker (QDialog con tabla de paquetes)",
        "3. Usuario selecciona paquete y confirma",
        "4. db.paquete_cargar(clave) obtiene header y items",
        "5. UI carga datos en campos y self.items",
        "6. Usuario modifica clave, descripción, agrega/quita herrajes",
        "7. Usuario presiona Guardar",
        "8. db.paquete_guardar() con UPSERT (DELETE + INSERT si existe)",
        "9. UI muestra mensaje de éxito y limpia pantalla",
    ]))

    historia.append(_ancla("flujo-impresion"))
    historia.append(Paragraph("6.3 Impresión", estilo_heading2))
    historia.append(_lista([
        "1. Usuario presiona Imprimir",
        "2. Se abre PrintOptionsDialog",
        "3. Usuario selecciona Destino (Pantalla/PDF/Impresora) y Tipo (General/Desglosado)",
        "4. Según tipo: llama a db.paquetes_listar() o db.paquetes_y_items()",
        "5. Genera HTML con _build_html_general() o _build_html_desglosado()",
        "6. Según destino:",
        "   - Pantalla: ScreenReportGeneral / ScreenReportDesglosado",
        "   - PDF: _export_html_to_pdf() con QPrinter",
        "   - Impresora: _print_to_physical() con filtrado de impresoras virtuales",
    ]))
    historia.append(PageBreak())

    # 7. MANEJO DE ERRORES
    historia.append(_ancla("errores"))
    historia.append(Paragraph("7. Manejo de Errores", estilo_heading1))
    datos_err = [
        ["Nivel", "Mecanismo", "Ejemplo"],
        ["Validación UI", "Comprobaciones en _agregar_item()", "Clave vacía → mensaje"],
        ["Clave duplicada", "paquete_existe() + QMessageBox.question", "Pregunta sobrescritura"],
        ["Conexión BD", "try/except + múltiples drivers/variantes", "Logging + raise"],
        ["Eliminación", "Diálogo de confirmación", "Mensaje '¿Seguro?'"],
        ["Impresión", "try/except + filtrado impresoras", "Mensaje si no hay impresora física"],
        ["Autocompletado", "try/except en _buscar_popup", "StatusBar con error"],
    ]
    historia.append(_tabla(datos_err, anchos=[35 * mm, 50 * mm, 71 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "# Ejemplo de manejo de conexión en DBManager.cn()\n"
        "for drv in drivers:\n"
        "    for srv in server_variants:\n"
        "        try:\n"
        "            self._cn = pyodbc.connect(conn_str)\n"
        "            return self._cn\n"
        "        except Exception as e:\n"
        "            last_error = e\n"
        "            continue\n"
        "raise RuntimeError(f'No se pudo conectar: {last_error}')"
    ))
    historia.append(PageBreak())

    # 8. LOGGING Y DEPURACIÓN
    historia.append(_ancla("logging"))
    historia.append(Paragraph("8. Logging y Depuración", estilo_heading1))
    historia.append(_lista([
        "No hay archivo de log específico para este módulo",
        "Los errores de conexión se capturan y muestran en QMessageBox.critical",
        "Los errores de búsqueda se muestran en StatusBar",
        "Para depuración, ejecutar el módulo desde consola:",
        "   python -m paquetes.herrajes.pantalla_paquete_herrajes",
        "El módulo imprimir.py tiene manejo de excepciones con traceback",
    ]))
    historia.append(PageBreak())

    # 9. CONFIGURACIÓN
    historia.append(_ancla("configuracion"))
    historia.append(Paragraph("9. Configuración", estilo_heading1))
    historia.append(Paragraph("Cadena de conexión a SQL Server (DBManager.cn()):", estilo_normal))
    historia.append(_codigo(
        'parts = [\n'
        '    "DRIVER={" + drv + "}",\n'
        '    "SERVER=" + srv,\n'
        '    "DATABASE=" + (self.database or ""),\n'
        '    "Trusted_Connection=yes",\n'
        ']\n'
        'if "ODBC Driver 18" in drv:\n'
        '    parts.append("Encrypt=yes")\n'
        '    parts.append("TrustServerCertificate=yes")'
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("Configuración por defecto:", estilo_normal))
    historia.append(_codigo(
        'DEFAULT_SERVER = r"DESKTOP-AE60PIU\\SQLEXPRESS"\n'
        'DEFAULT_DATABASE = "herrajes"\n'
        'TABLA_PAQUETES = "paquetes_herrajes"\n'
        'TABLA_ITEMS = "paquete_herraje_items"\n'
        'TABLA_HERRAJES = "materiales_herraje"'
    ))
    historia.append(PageBreak())

    # 10. INTEGRACIÓN CON PRESUPUESTOS
    historia.append(_ancla("integracion"))
    historia.append(Paragraph("10. Integración con Presupuestos", estilo_heading1))
    historia.append(Paragraph(
        "El módulo de Paquete Herrajes está diseñado para ser consumido por el módulo de Presupuestos "
        "a través de la tabla 'partida_paquetes'.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    datos_integracion = [
        ["Tabla", "Campo", "Descripción"],
        ["partida_paquetes", "tipo_paquete", "'herrajes' para identificar el origen"],
        ["partida_paquetes", "clave_paquete", "Clave del paquete (FK semántica)"],
        ["partida_paquetes", "ancho", "Ancho del vano/puerta/ventana"],
        ["partida_paquetes", "alto", "Alto del vano/puerta/ventana"],
        ["partida_paquetes", "piezas", "Número de piezas"],
    ]
    historia.append(_tabla(datos_integracion, anchos=[40 * mm, 50 * mm, 66 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_nota(
        "La integración real entre Paquete Herrajes y Presupuestos se implementa en el módulo de Presupuestos, "
        "que consulta los paquetes y sus items para calcular costos y generar partidas."
    ))
    historia.append(PageBreak())

    # CIERRE
    historia.append(Paragraph("— Fin del Manual Técnico —",
                              ParagraphStyle('Cierre', parent=estilo_normal, alignment=TA_CENTER, textColor=COLOR_AZUL,
                                             fontSize=12)))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph(f"Documento generado el {FECHA_GENERACION} | Versión {VERSION}", estilo_pie))
    historia.append(Paragraph("VAH ERP © Todos los derechos reservados", estilo_pie))

    doc.build(historia)
    print(f"✅ Manual Técnico de {MODULO} generado: {ruta_salida}")


def _nota(texto):
    """Crea un párrafo de nota para el manual técnico."""
    estilo_nota = ParagraphStyle(
        'NotaTecnica',
        parent=estilo_normal,
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=HexColor("#6b7280"),
        leftIndent=5 * mm,
        rightIndent=5 * mm,
    )
    return Paragraph(f'📌 <b>Nota:</b> {texto}', estilo_nota)


if __name__ == "__main__":
    generar_manual_tecnico()