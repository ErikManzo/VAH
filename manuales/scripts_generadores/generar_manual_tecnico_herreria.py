# D:\vah\manuales\scripts_generadores\generar_manual_tecnico_herreria.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Técnico - Módulo Materiales Herrería VAH
============================================================
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
MODULO = "Herrería"
TIPO_MANUAL = "Técnico"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "herreria")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf", "técnico")  # ✅ CORREGIDO
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
        ("  3.2", "Relaciones", "bd-relaciones"),
        ("4.", "Dependencias", "dependencias"),
        ("5.", "Módulos y Clases Principales", "modulos"),
        ("  5.1", "DBManager", "modulo-dbmanager"),
        ("  5.2", "PantallaHerreria", "modulo-pantalla"),
        ("  5.3", "Importador Excel", "modulo-importador"),
        ("6.", "Flujo de Datos", "flujo"),
        ("  6.1", "Guardado Manual", "flujo-guardar"),
        ("  6.2", "Edición", "flujo-editar"),
        ("  6.3", "Importación Excel", "flujo-importar"),
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
    historia.append(Paragraph("El Módulo de Herrería sigue una arquitectura de tres capas:", estilo_normal))
    datos_arq = [["Capa", "Tecnología", "Responsabilidad"],
                 ["Presentación", "PyQt6", "Interfaz gráfica (PantallaHerreria)"],
                 ["Lógica de Negocio", "Python 3.12", "DBManager, validaciones"],
                 ["Acceso a Datos", "pyodbc + SQL Server", "CRUD sobre materiales_herreria"],
                 ["Almacenamiento", "SQL Server", "Base de datos 'herreria', tabla materiales_herreria"]]
    historia.append(_tabla(datos_arq, anchos=[35 * mm, 35 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("arquitectura_sistema.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 2. ESTRUCTURA DE ARCHIVOS
    historia.append(_ancla("estructura"))
    historia.append(Paragraph("2. Estructura de Archivos", estilo_heading1))
    datos_files = [
        ["Archivo", "Descripción"],
        ["pantalla_herreria.py", "UI principal, modos de operación, eventos"],
        ["db_manager.py", "CRUD, conexión BD, context manager"],
        ["cargar_excel_herreria.py", "Importador Excel con MERGE set-based"],
        ["imprimir.py", "Generación de PDF con reportlab"],
        ["utils.py", "Función dec2() para conversión a Decimal"],
    ]
    historia.append(_tabla(datos_files, anchos=[60 * mm, 96 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("estructura_modulos.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 3. BASE DE DATOS
    historia.append(_ancla("basedatos"))
    historia.append(Paragraph("3. Base de Datos", estilo_heading1))
    historia.append(_ancla("bd-esquema"))
    historia.append(Paragraph("3.1 Esquema de la Tabla", estilo_heading2))

    datos_esq = [
        ["Columna", "Tipo", "Nulo", "Descripción"],
        ["Clave", "varchar(20)", "NO", "PK - Clave única del material"],
        ["Descripcion", "varchar(100)", "YES", "Nombre del material"],
        ["kilogramos", "decimal(10,2)", "YES", "Peso por metro lineal (kg/m)"],
    ]
    historia.append(_tabla(datos_esq, anchos=[35 * mm, 35 * mm, 15 * mm, 71 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("diagrama_bd.png", ancho=160 * mm))

    historia.append(_ancla("bd-relaciones"))
    historia.append(Paragraph("3.2 Relaciones", estilo_heading2))
    historia.append(_lista([
        "La tabla NO tiene claves foráneas explícitas.",
        "La clave primaria es 'Clave' (única).",
        "No hay relaciones directas con otras tablas.",
        "La integridad se maneja a nivel de aplicación.",
        "El módulo de Presupuestos consulta esta tabla para obtener kg/m.",
    ]))
    historia.append(PageBreak())

    # 4. DEPENDENCIAS
    historia.append(_ancla("dependencias"))
    historia.append(Paragraph("4. Dependencias", estilo_heading1))
    datos_deps = [
        ["Librería", "Versión", "Uso"],
        ["PyQt6", "6.5+", "Interfaz gráfica completa"],
        ["pyodbc", "4.0+", "Conexión ODBC a SQL Server"],
        ["openpyxl", "3.0+", "Lectura de archivos Excel"],
        ["pandas", "1.5+", "Procesamiento de datos en importador"],
        ["numpy", "1.24+", "Manejo de NaN en importador"],
        ["reportlab", "3.6+", "Generación de PDF para impresión"],
        ["win32print", "pywin32", "Impresión directa a impresora física"],
        ["Python", "3.10+", "Lenguaje base"],
    ]
    historia.append(_tabla(datos_deps, anchos=[40 * mm, 30 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "pip install PyQt6 pyodbc openpyxl pandas numpy reportlab pywin32"
    ))
    historia.append(PageBreak())

    # 5. MÓDULOS Y CLASES PRINCIPALES
    historia.append(_ancla("modulos"))
    historia.append(Paragraph("5. Módulos y Clases Principales", estilo_heading1))

    historia.append(_ancla("modulo-dbmanager"))
    historia.append(Paragraph("5.1 DBManager (db_manager.py)", estilo_heading2))
    historia.append(_lista([
        "listar_todos() → List[Dict] - Obtiene todos los materiales",
        "existe_clave(clave) → bool - Verifica existencia",
        "insertar(reg) - Inserta nuevo material",
        "actualizar_por_clave(clave_original, reg) - Actualiza (permite cambiar clave)",
        "eliminar_por_clave(clave) - Elimina material",
        "_get_conn() - Context manager para conexiones seguras",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Ejemplo de uso\n"
        "db = DBManager()\n"
        "material = {\n"
        '    "clave": "ANG-101",\n'
        '    "descripcion": "Ángulo 1/2 x 1/2",\n'
        '    "kilogramos": Decimal("1.25")\n'
        "}\n"
        "db.insertar(material)"
    ))

    historia.append(_ancla("modulo-pantalla"))
    historia.append(Paragraph("5.2 PantallaHerreria (pantalla_herreria.py)", estilo_heading2))
    historia.append(_lista([
        "_on_guardar() - Guarda material (modo nuevo o edición)",
        "_modo_editar() - Activa modo edición, habilita búsqueda",
        "_modo_eliminar() - Activa modo eliminación (requiere doble clic + segundo Delete)",
        "Inicio() - Limpia todos los campos y tabla",
        "_buscar_dinamico() - Filtra tabla por prefijo de clave",
        "_on_imprimir() - Diálogo de impresión (Pantalla/PDF/Impresora)",
        "_llenar_tabla() - Carga datos en QTableWidget",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Atajos de teclado definidos\n"
        "Ctrl+S → _on_guardar\n"
        "Ctrl+F → focus búsqueda\n"
        "Ctrl+P → _on_imprimir\n"
        "Delete → _modo_eliminar\n"
        "F5 → _on_refresh\n"
        "Esc → close"
    ))

    historia.append(_ancla("modulo-importador"))
    historia.append(Paragraph("5.3 Importador Excel (cargar_excel_herreria.py)", estilo_heading2))
    historia.append(_lista([
        "importar(file_path, sheet_name) - Función principal",
        "_find_header_row() - Detecta fila de encabezados",
        "_pick_columns() - Identifica columnas Clave, Descripción, Kilogramos",
        "_guess_text_column() - Infiere columna de descripción si no existe",
        "_prepare_rows() - Prepara datos y valida",
        "_bulk_merge() - Ejecuta MERGE con tabla temporal #imp",
        "_save_rejected() - Guarda registros rechazados en CSV",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Uso del importador\n"
        "python -m materiales.herreria.cargar_excel_herreria\n"
        "# o con parámetros:\n"
        "python -m materiales.herreria.cargar_excel_herreria \"ruta\\archivo.xlsx\" \"NombreHoja\""
    ))
    historia.append(PageBreak())

    # 6. FLUJO DE DATOS
    historia.append(_ancla("flujo"))
    historia.append(Paragraph("6. Flujo de Datos", estilo_heading1))

    historia.append(_ancla("flujo-guardar"))
    historia.append(Paragraph("6.1 Guardado Manual", estilo_heading2))
    historia.append(_lista([
        "1. Usuario completa campos (Clave, Descripción, Kilogramos)",
        "2. Usuario presiona Guardar (Ctrl+S)",
        "3. UI valida campos obligatorios (Clave, Descripción, kg > 0)",
        "4. Si modo='nuevo': verifica que clave no exista",
        "5. Si modo='editar': verifica duplicado si cambia clave",
        "6. UI llama a DBManager.insertar() o actualizar_por_clave()",
        "7. DBManager ejecuta INSERT/UPDATE con pyodbc",
        "8. UI muestra mensaje de éxito y limpia pantalla"
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("flujo_datos.png", ancho=160 * mm))

    historia.append(_ancla("flujo-editar"))
    historia.append(Paragraph("6.2 Edición (incluyendo cambio de clave)", estilo_heading2))
    historia.append(_lista([
        "1. Usuario presiona Editar",
        "2. UI activa barra de búsqueda",
        "3. Usuario escribe prefijo de clave",
        "4. UI filtra y muestra resultados",
        "5. Usuario hace doble clic en registro deseado",
        "6. UI carga datos (todos los campos habilitados)",
        "7. Usuario modifica clave, descripción o kg",
        "8. Usuario presiona Guardar",
        "9. Si clave cambió, verifica que la nueva no exista",
        "10. DBManager ejecuta UPDATE",
        "11. UI muestra mensaje de éxito"
    ]))

    historia.append(_ancla("flujo-importar"))
    historia.append(Paragraph("6.3 Importación Excel (MERGE set-based)", estilo_heading2))
    historia.append(_lista([
        "1. Usuario ejecuta script: python -m materiales.herreria.cargar_excel_herreria",
        "2. Script lee Excel y detecta encabezados",
        "3. Identifica columnas Clave, Descripción, Kilogramos",
        "4. Valida cada fila (clave no vacía, kg válido)",
        "5. Crea tabla temporal #imp",
        "6. Ejecuta MERGE contra materiales_herreria:",
        "   - MATCHED → UPDATE (kg = MAX(existente, nuevo))",
        "   - NOT MATCHED → INSERT",
        "7. Registros rechazados se guardan en CSV",
        "8. Muestra resumen en consola"
    ]))
    historia.append(PageBreak())

    # 7. MANEJO DE ERRORES
    historia.append(_ancla("errores"))
    historia.append(Paragraph("7. Manejo de Errores", estilo_heading1))
    datos_err = [
        ["Nivel", "Mecanismo", "Ejemplo"],
        ["Validación UI", "Comprobaciones en _on_guardar()", "Clave vacía → mensaje"],
        ["Clave duplicada", "existe_clave() + QMessageBox", "Mensaje de advertencia"],
        ["Conexión BD", "try/except + context manager", "Logging + raise"],
        ["Importación", "try/except por registro + CSV rechazados", "Continúa con siguiente"],
        ["Impresión", "try/except en imprimir_pdf_guardar", "QMessageBox.critical"],
    ]
    historia.append(_tabla(datos_err, anchos=[35 * mm, 50 * mm, 71 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "# Ejemplo de context manager en db_manager.py\n"
        "@contextmanager\n"
        "def _get_conn(self):\n"
        "    conn = pyodbc.connect(self.conn_str)\n"
        "    try:\n"
        "        yield conn\n"
        "    finally:\n"
        "        conn.close()"
    ))
    historia.append(PageBreak())

    # 8. LOGGING
    historia.append(_ancla("logging"))
    historia.append(Paragraph("8. Logging y Depuración", estilo_heading1))
    historia.append(_lista([
        "No hay archivo de log específico para este módulo",
        "Los errores de conexión se capturan y muestran en UI",
        "Los rechazados de importación se guardan en:",
        "   D:\\vah\\logs\\rechazados_herreria_YYYYMMDD_HHMMSS.csv",
        "Para depuración, ejecutar el módulo desde consola:",
        "   python -m materiales.herreria.pantalla_herreria"
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Ejemplo de salida de importador\n"
        "Columnas detectadas → Clave: 'CLAVE' | Descripción: 'DESCRIPCIÓN' | Kilogramos: 'KG/MT'\n"
        "=== Importación HERRERÍA ===\n"
        "Válidos: 150  |  Insertados: 45  |  Actualizados: 105\n"
        "Rechazados: 3\n"
        "Detalle rechazados: D:\\vah\\logs\\rechazados_herreria_20260522_143022.csv"
    ))
    historia.append(PageBreak())

    # 9. CONFIGURACIÓN
    historia.append(_ancla("configuracion"))
    historia.append(Paragraph("9. Configuración", estilo_heading1))
    historia.append(Paragraph("Cadena de conexión a SQL Server (db_manager.py):", estilo_normal))
    historia.append(_codigo(
        'cs = (\n'
        '    f"DRIVER={{ODBC Driver 18 for SQL Server}};"\n'
        '    f"SERVER={self.server};"\n'
        '    f"DATABASE={self.database};"\n'
        '    "Trusted_Connection=yes;"\n'
        '    "Encrypt=yes;TrustServerCertificate=yes;"\n'
        ")"
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("Configuración por defecto:", estilo_normal))
    historia.append(_codigo(
        'DEFAULT_SERVER = r"DESKTOP-AE60PIU\\SQLEXPRESS"\n'
        'DEFAULT_DATABASE = "herreria"\n'
        'DEFAULT_TABLE = "dbo.materiales_herreria"\n'
        'DEFAULT_XLSX = r"C:\\Users\\Personal\\OneDrive\\Escritorio\\herreria.xlsx"'
    ))
    historia.append(PageBreak())

    # 10. INTEGRACIÓN CON PRESUPUESTOS
    historia.append(_ancla("integracion"))
    historia.append(Paragraph("10. Integración con Presupuestos", estilo_heading1))
    historia.append(Paragraph(
        "El módulo de Herrería es consumido por el <b>módulo de Presupuestos</b> para calcular costos.",
        estilo_normal
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(Paragraph("<b>Flujo de integración:</b>", estilo_normal))
    historia.append(_lista([
        "1. Usuario selecciona 'Herrería' como tipo de material en presupuesto.",
        "2. El sistema consulta la tabla `materiales_herreria` para obtener la lista de claves.",
        "3. Usuario selecciona una clave y captura el ancho/alto/piezas.",
        "4. El sistema calcula los metros lineales necesarios.",
        "5. Usuario captura el precio por kilogramo ($/kg).",
        "6. El sistema consulta `kilogramos` de la tabla y calcula:",
        "   <b>Total = Metros × kg/m × $/kg</b>",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Consulta típica desde presupuestos\n"
        "SELECT Clave, Descripcion, kilogramos\n"
        "FROM herreria.dbo.materiales_herreria\n"
        "WHERE Clave = ?"
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


if __name__ == "__main__":
    generar_manual_tecnico()